"""This creates Pandas dataframes containing predictions.

"""
__author__ = 'Paul Landes'

from typing import Callable, List, Iterable
from dataclasses import dataclass, field
import logging
import sys
import itertools as it
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from zensols.persist import persisted
from zensols.deeplearn.vectorize import (
    CategoryEncodableFeatureVectorizer,
    FeatureVectorizerManagerSet,
)
from zensols.deeplearn.batch import Batch, BatchStash, DataPoint
from . import (
    ModelResultError, ModelResult, EpochResult, ClassificationMetrics
)

logger = logging.getLogger(__name__)


@dataclass
class PredictionsDataFrameFactory(object):
    """Create a Pandas data frame containing results from a result as output from a
    ``ModelExecutor``.  The data frame contains the feature IDs, labels,
    predictions mapped back to their original value from the feature data item.

    Currently only classification models are supported.

    """
    source: Path = field()
    """The source file from where the results were unpickled."""

    result: ModelResult = field()
    """The epoch containing the results."""

    stash: BatchStash = field()
    """The batch stash used to generate the results from the
    :class:`~zensols.deeplearn.model.ModelExecutor`.  This is used to get the
    vectorizer to reverse map the labels.

    """
    column_names: List[str] = field(default=None)
    """The list of string column names for each data item the list returned from
    ``data_point_transform`` to be added to the results for each
    label/prediction

    """
    data_point_transform: Callable[[DataPoint], tuple] = field(default=None)
    """A function that returns a tuple, each with an element respective of
    ``column_names`` to be added to the results for each label/prediction; if
    ``None`` (the default), ``str`` used (see the `Iris Jupyter Notebook
    <https://github.com/plandes/deeplearn/blob/master/notebook/iris.ipynb>`_
    example)

    """
    batch_limit: int = sys.maxsize
    """The max number of batche of results to output."""

    epoch_result: EpochResult = field(default=None)
    """The epoch containing the results.  If none given, take it from the test
    results..

    """
    label_vectorizer_name: str = field(default=None)
    """The name of the vectorizer that encodes the labels, which is used to reverse
    map from integers to their original string nominal values.

    """
    def __post_init__(self):
        if self.column_names is None:
            self.column_names = ('data',)
        if self.data_point_transform is None:
            self.data_point_transform = lambda dp: (str(dp),)
        if self.epoch_result is None:
            self.epoch_result = self.result.test.results[0]

    @property
    def name(self) -> str:
        """The name of the results taken from :class:`.ModelResult`."""
        return self.result.name

    def _transform_dataframe(self, batch: Batch, labs: List[str],
                             preds: List[str]):
        transform: Callable = self.data_point_transform
        rows = []
        for dp, lab, pred in zip(batch.data_points, labs, preds):
            assert dp.label == lab
            row = [dp.id, lab, pred, lab == pred]
            row.extend(transform(dp))
            rows.append(row)
        cols = 'id label pred correct'.split() + list(self.column_names)
        return pd.DataFrame(rows, columns=cols)

    def _calc_len(self, batch: Batch) -> int:
        return len(batch)

    def _narrow_encoder(self, batch: Batch) -> LabelEncoder:
        vec: CategoryEncodableFeatureVectorizer = None
        if self.label_vectorizer_name is None:
            vec = batch.get_label_feature_vectorizer()
            while True:
                if not isinstance(vec, CategoryEncodableFeatureVectorizer) \
                   and hasattr(vec, 'delegate'):
                    vec = vec.delegate
                else:
                    break
        else:
            vms: FeatureVectorizerManagerSet = \
                batch.batch_stash.vectorizer_manager_set
            vec = vms.get_vectorizer(self.label_vectorizer_name)
        if not isinstance(vec, CategoryEncodableFeatureVectorizer):
            raise ModelResultError(
                'Expecting a category feature vectorizer but got: ' +
                f'{vec} ({vec.name if vec else "none"})')
        return vec.label_encoder

    def _batch_dataframe(self, inv_trans: bool) -> Iterable[pd.DataFrame]:
        """Return a data from for each batch.

        """
        epoch_labs: List[np.ndarray] = self.epoch_result.labels
        epoch_preds: List[np.ndarray] = self.epoch_result.predictions
        start = 0
        for bid in it.islice(self.epoch_result.batch_ids, self.batch_limit):
            batch: Batch = self.stash[bid]
            end = start + self._calc_len(batch)
            preds: List[int] = epoch_preds[start:end]
            labs: List[int] = epoch_labs[start:end]
            if inv_trans:
                le: LabelEncoder = self._narrow_encoder(batch)
                inv_trans: Callable = le.inverse_transform
                preds: List[str] = inv_trans(preds)
                labs: List[str] = inv_trans(labs)
            df = self._transform_dataframe(batch, labs, preds)
            df['batch_id'] = bid
            assert len(df) == len(labs)
            start = end
            yield df

    def _create_dataframe(self, inv_trans: bool) -> pd.DataFrame:
        return pd.concat(self._batch_dataframe(inv_trans), ignore_index=True)

    @property
    @persisted('_dataframe')
    def dataframe(self) -> pd.DataFrame:
        """The predictions and labels as a dataframe.  The first columns are generated
        from ``data_point_tranform``, and the remaining columns are:

        - id: the ID of the feature (not batch) data item
        - label: the label given by the feature data item
        - pred: the prediction
        - correct: whether or not the prediction was correct

        """
        return self._create_dataframe(True)

    @property
    def metrics_dataframe(self) -> pd.DataFrame:
        """Performance metrics by comparing the gold label to the predictions.

        """
        rows = []
        df = self._create_dataframe(False)
        dfg = df.groupby('label').agg({'label': 'count'}).\
            rename(columns={'label': 'count'})
        cols = 'label wF1 wP wR mF1 mP mR MF1 MP MR correct accuracy count'.split()
        bids = self.epoch_result.batch_ids
        batch: Batch = self.stash[bids[0]]
        le: LabelEncoder = self._narrow_encoder(batch)
        for ann_id, dfg in df.groupby('label'):
            lab: str = le.inverse_transform([ann_id])[0]
            data = dfg['label'], dfg['pred']
            mets = ClassificationMetrics(*data, len(data[0]))
            row = [lab, mets.weighted.f1, mets.weighted.precision,
                   mets.weighted.recall,
                   mets.micro.f1, mets.micro.precision, mets.micro.recall,
                   mets.macro.f1, mets.macro.precision, mets.macro.recall,
                   mets.n_correct, mets.accuracy, mets.n_outcomes]
            rows.append(row)
        dfr = pd.DataFrame(rows, columns=cols)
        dfr = dfr.sort_values('label').reset_index(drop=True)
        return dfr


@dataclass
class SequencePredictionsDataFrameFactory(PredictionsDataFrameFactory):
    """Like the super class but create predictions for sequence based models.

    :see: :class:`~zensols.deeplearn.model.sequence.SequenceNetworkModule`

    """
    def _calc_len(self, batch: Batch) -> int:
        return sum(map(len, batch.data_points))

    def _transform_dataframe(self, batch: Batch, labs: List[str],
                             preds: List[str]):
        dfs: List[pd.DataFrame] = []
        start: int = 0
        transform: Callable = self.data_point_transform
        for dp, lab, pred in zip(batch.data_points, labs, preds):
            end = start + len(dp)
            df = pd.DataFrame({
                'id': dp.id,
                'label': labs[start:end],
                'pred': preds[start:end]})
            df[list(self.column_names)] = transform(dp)
            dfs.append(df)
            start = end
        return pd.concat(dfs)
