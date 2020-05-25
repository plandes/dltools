"""Contains contain classes for results generated from training and testing a
model.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field, asdict
from abc import ABCMeta, abstractmethod
import logging
import sys
from datetime import datetime
from io import TextIOWrapper
from itertools import chain
from typing import Any, List, Dict
import sklearn.metrics as mt
import numpy as np
import pandas as pd
import torch
from zensols.config import Configurable, Writable
from zensols.persist import (
    persisted,
    PersistableContainer,
    IncrementKeyDirectoryStash,
)
from zensols.deeplearn import ModelSettings, NetworkSettings
from zensols.deeplearn.batch import Batch

logger = logging.getLogger(__name__)


class NoResultsException(Exception):
    """Convenience used for helping debug the network.

    """
    def __init__(self):
        super().__init__('no results available')


class ResultsContainer(PersistableContainer, Writable, metaclass=ABCMeta):
    """Container class for results while training, testing and validating a model.

    """
    PREDICTIONS_INDEX = 0
    LABELS_INDEX = 1

    @abstractmethod
    def get_ids(self) -> List[Any]:
        "See property ``ids``."
        pass

    @abstractmethod
    def get_outcomes(self) -> np.ndarray:
        "See property ``outcomes``"
        pass

    @abstractmethod
    def get_loss(self) -> float:
        "See property ``loss``."
        pass

    @abstractmethod
    def get_losses(self) -> List[float]:
        "See property ``losses``."
        pass

    @property
    def contains_results(self) -> bool:
        """Return ``True`` if this container has results.

        """
        return len(self) > 0

    def _assert_results(self):
        "Raises an exception if there are no results."
        if not self.contains_results:
            raise NoResultsException()

    def __len__(self):
        return len(self.get_ids())

    def _data_updated(self):
        "Void out all cached data"
        self._get_persistable_metadata().clear()

    @property
    @persisted('_ids', transient=True)
    def ids(self) -> List[Any]:
        """Return the IDs of the data points found in the batch for this result set.

        """
        self._assert_results()
        return self.get_ids()

    @property
    @persisted('_outcomes', transient=True)
    def outcomes(self) -> np.ndarray:
        """Return the outcomes as an array with the first row the provided labels and
        the second row the predictions.  If no labels are given during the
        prediction (i.e. evaluation) there will only be one row, which are the
        predictions.

        """
        self._assert_results()
        return self.get_outcomes()

    @property
    def labels(self) -> np.ndarray:
        """Return the labels or ``None`` if none were provided (i.e. during
        test/evaluation).

        """
        self._assert_results()
        return self.outcomes[self.LABELS_INDEX]

    @property
    def predictions(self) -> np.ndarray:
        """Return the predictions from the model.

        """
        self._assert_results()
        return self.outcomes[self.PREDICTIONS_INDEX]

    @property
    @persisted('_loss', transient=True)
    def loss(self) -> float:
        """Return the average loss of this result set.

        """
        self._assert_results()
        return self.get_loss()

    @property
    @persisted('_losses', transient=True)
    def losses(self) -> List[float]:
        """Return the loss for each epoch of the run.  If used on a ``EpocResult`` it
        is the Nth iteration.

        """
        return self.get_losses()

    @property
    @persisted('_convergence', transient=True)
    def convergence(self):
        """Return the Nth epoch this result set convergened.  If used on a
        ``EpocResult`` it is the Nth iteration.

        """
        losses = self.losses
        lowest = min(losses)
        return losses.index(lowest)

    @staticmethod
    def compute_metrics(average: str, y_true: np.ndarray,
                        y_pred: np.ndarray) -> Dict[str, float]:
        scores = tuple(map(lambda f: f(y_true,  y_pred, average=average),
                           (mt.f1_score, mt.precision_score, mt.recall_score)))
        return {'f1': scores[0],
                'precision': scores[1],
                'recall': scores[2]}

    def _compute_metrics(self, average: str) -> Dict[str, float]:
        """Compute F1, precision and recall.

        :param average: the type of metric to produce (either ``micro`` or
                        ``macro``).

        """
        return self.compute_metrics(average, self.labels, self.predictions)

    @property
    @persisted('_micro_metrics', transient=True)
    def micro_metrics(self) -> Dict[str, float]:
        """Compute F1, precision and recall.

        """
        self._assert_results()
        return self._compute_metrics('micro')

    @property
    @persisted('_macro_metrics', transient=True)
    def macro_metrics(self) -> Dict[str, float]:
        """Compute F1, precision and recall.

        """
        self._assert_results()
        return self._compute_metrics('macro')

    @property
    @persisted('_dataframe', transient=True)
    def dataframe(self) -> pd.DataFrame:
        """Return the results as a pandas dataframe.

        """
        self._assert_results()
        return pd.DataFrame({'id': self.ids,
                             'label': self.labels,
                             'prediction': self.predictions})

    def _format_time(self, attr: str):
        if hasattr(self, attr):
            val: datetime = getattr(self, attr)
            if val is not None:
                return val.strftime("%m/%d/%Y %H:%M:%S:%f")

    ## TODO: add or replace a min loss to the class and report that instead
    ## since average loss seems less useful
    def write(self, depth: int = 0, writer: TextIOWrapper = sys.stdout):
        """Generate a human readable representation of the results.

        :param writer: the text sink
        :param indent: the indentation space
        """
        sp = self._sp(depth)
        micro = self.micro_metrics
        macro = self.macro_metrics
        writer.write(f'{sp}loss: {self.loss}\n')
        writer.write(f'{sp}num outcomes: {self.outcomes.shape[1]}\n')
        writer.write(f'{sp}epoch convergence: {self.convergence}\n')
        writer.write(f"{sp}micro: F1: {micro['f1']:.3f}, " +
                     f"precision: {micro['precision']:.2f}, " +
                     f"recall: {micro['recall']:.2f}\n")
        writer.write(f"{sp}macro: F1: {macro['f1']:.3f}, " +
                     f"precision: {macro['precision']:.2f}, " +
                     f"recall: {macro['recall']:.2f}\n")


@dataclass
class EpochResult(ResultsContainer):
    """Contains results recorded from an epoch of a neural network model.  This is
    during a training/validation or test cycle.

    :param loss_updates: the losses generated from each iteration of the epoch
    :param id_updates: the IDs of the data points from each iteration of the
                       epoch
    :param prediction_updates: the predictions generated by the model from each
                               iteration of the epoch

    """
    index: int
    split_type: str
    loss_updates: List[float] = field(default_factory=list)
    id_updates: List[int] = field(default_factory=list)
    prediction_updates: List[torch.Tensor] = field(default_factory=list)
    batch_ids: List[int] = field(default_factory=list)
    n_data_points: List[int] = field(default_factory=list)

    def update(self, batch: Batch, loss: torch.Tensor, labels: torch.Tensor,
               preds: torch.Tensor, label_shape: List[tuple]):
        logger.debug(f'{self.index}:{self.split_type}: ' +
                     f'update batch: {batch.id}, label_shape: {label_shape}')
        # object function loss; 'mean' is the default 'reduction' parameter for
        # loss functions; we can either muliply it back out or use 'sum' in the
        # criterion initialize
        self.loss_updates.append(loss.item() * batch.size())
        # batches are always the first dimension
        self.n_data_points.append(label_shape[0])
        # get the indexes of the max value across labels and outcomes
        # labels = labels.argmax(1)
        # preds = output.argmax(1)
        # stack and append for metrics computation later
        res = torch.stack((preds, labels), 0)
        self.prediction_updates.append(res.cpu())
        self.batch_ids.append(batch.id)
        # keep IDs for tracking
        self.id_updates.append(batch.data_point_ids)
        self._data_updated()

    def get_ids(self):
        return tuple(chain.from_iterable(self.id_updates))

    def get_loss(self):
        return sum(self.loss_updates) / len(self)

    def get_losses(self):
        return self.loss_updates

    def get_outcomes(self):
        return np.concatenate(self.prediction_updates, 1)

    def __getitem__(self, i: int) -> np.ndarray:
        return self.prediction_updates[i]

    def __str__(self):
        return f'{self.index}: loss: {self.loss:.3f}, len: {len(self)}'

    def __repr__(self):
        return self.__str__()


@dataclass
class DatasetResult(ResultsContainer):
    """Contains results from training/validating or test cycle.

    :param results: the results generated from the iterations of the epoch
    """
    results: List[EpochResult] = field(default_factory=list)
    start_time: datetime = field(default=None)
    end_time: datetime = field(default=None)

    def start(self):
        if self.contains_results:
            raise ValueError(f'container {self} already contains results')
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()

    def append(self, epoch_result: EpochResult):
        self.results.append(epoch_result)
        self._data_updated()

    def get_ids(self):
        ids = chain.from_iterable(map(lambda r: r.get_ids(), self.results))
        return tuple(ids)

    def get_loss(self):
        loss_sum = sum(map(lambda r: r.loss, self.results))
        batch_sum = sum(map(lambda r: len(r), self.results))
        return 0 if batch_sum == 0 else loss_sum / batch_sum

    def get_losses(self):
        return tuple(map(lambda r: r.loss, self.results))

    def get_outcomes(self):
        prs = tuple(map(lambda r: r.outcomes, self.results))
        return np.concatenate(prs, axis=1)

    def __getitem__(self, i: int) -> EpochResult:
        return self.results[i]


@dataclass
class ModelResult(ResultsContainer, Writable):
    """A container class used to capture the training, validation and test results.
    The data captured is used to report and plot curves.

    :param config: useful for retrieving hyperparameter settings later after
                   unpersisting from disk

    :param model_settings: the setttings used to configure the model

    """
    config: Configurable
    name: str
    model_settings: ModelSettings
    net_settings: NetworkSettings

    def __post_init__(self):
        global _runs
        if '_runs' not in globals():
            _runs = 0
        _runs += 1
        self.index = _runs
        splits = 'train validation test'.split()
        self.dataset_result = {k: DatasetResult() for k in splits}

    @staticmethod
    def reset_runs():
        """Reset the run counter.

        """
        global _runs
        _runs = 0

    def __getitem__(self, name: str) -> DatasetResult:
        return self.dataset_result[name]

    @property
    def train(self) -> DatasetResult:
        """Return the training run results.

        """
        self._data_updated()
        return self.dataset_result['train']

    @property
    def validation(self) -> DatasetResult:
        """Return the validation run results.

        """
        self._data_updated()
        return self.dataset_result['validation']

    @property
    def test(self) -> DatasetResult:
        """Return the testing run results.

        """
        self._data_updated()
        return self.dataset_result['test']

    def reset(self, name: str):
        self.dataset_result[name] = DatasetResult()

    @property
    def contains_results(self) -> bool:
        return len(self.test) > 0 or len(self.validation) > 0

    @property
    def last_test_dataset_result_name(self) -> str:
        if len(self.test) > 0:
            return 'test'
        if len(self.validation) > 0:
            return 'validation'
        raise NoResultsException()

    @property
    def last_test_dataset_result(self) -> DatasetResult:
        """Return either the test or validation results depending on what is available.

        """
        return self[self.last_test_dataset_result_name]

    def get_ids(self):
        return self.last_test_dataset_result.get_ids()

    def get_outcomes(self):
        return self.last_test_dataset_result.get_outcomes()

    def get_loss(self):
        return self.last_test_dataset_result.get_loss()

    def get_losses(self) -> List[float]:
        return self.last_test_dataset_result.get_losses()

    def get_result_statistics(self, result_name: str):
        self._data_updated()
        epochs = self.dataset_result[result_name].results
        fn = 0
        if len(epochs) > 0:
            fn = epochs[0].n_data_points
            for epoc in epochs:
                assert fn == epoc.n_data_points
        return {'n_epochs': len(epochs),
                'n_data_points': fn}

    def write_result_statistics(self, result_name: str, depth: int = 0,
                                writer=sys.stdout):
        sp = self._sp(depth)
        stats = self.get_result_statistics(result_name)
        epochs = stats['n_epochs']
        fn = sum(stats['n_data_points'])
        writer.write(f'{sp}num epochs: {epochs}\n')
        writer.write(f'{sp}num data points per epoc: {fn}\n')

    def write(self, depth: int = 0, writer: TextIOWrapper = sys.stdout,
              verbose=False):
        """Generate a human readable format of the results.

        """
        self._write_line(f'Name: {self.name}', depth, writer)
        self._write_line(f'Run index: {self.index}', depth, writer)
        self._write_line(f'Learning rate: {self.model_settings.learning_rate}',
                         depth, writer)
        sp = self._sp(depth + 1)
        spe = self._sp(depth + 2)
        for name, ds_res in self.dataset_result.items():
            writer.write(f'{sp}{name}:\n')
            if ds_res.contains_results:
                start_time = ds_res._format_time('start_time')
                end_time = ds_res._format_time('end_time')
                if start_time is not None:
                    writer.write(f'{spe}started: {start_time}\n')
                    writer.write(f'{spe}ended: {end_time}\n')
                self.write_result_statistics(name, depth + 2, writer)
                ds_res.write(depth + 2, writer)
            else:
                writer.write(f'{spe}no results\n')
        if verbose:
            self._write_line('configuration:', depth, writer)
            self.config.write(depth + 1, writer)
            self._write_line('model settings:', depth, writer)
            self._write_dict(asdict(self.model_settings), depth + 1, writer)
            self._write_line('network settings:', depth, writer)
            self._write_dict(asdict(self.net_settings), depth + 1, writer)

    def __str__(self):
        model_name = self.net_settings.get_module_class_name()
        return f'{model_name} ({self.index})'

    def __repr__(self):
        return self.__str__()


@dataclass
class ModelResultManager(IncrementKeyDirectoryStash):
    """Saves and loads results from runs
    (:class:`zensols.deeplearn.result.ModelResult`) of the
    :class:``zensols.deeplearn.model.ModelExecutor``.  Keys incrementing
    integers, one for each save, which usually corresponds to the run of the
    model executor.

    :param save_text: if ``True``, save the verbose result output (from
                      :meth:`zensols.deeplearn.result.ModelResult.write`) of
                      the results run

    """
    save_text: bool = field(default=True)

    def __post_init__(self, name: str):
        self.prefix = self.name.lower().replace(' ', '-')
        super().__post_init__(self.prefix)

    def dump(self, result: ModelResult):
        super().dump(result)
        if self.save_text:
            key = self.get_last_key(False)
            path = self.path / f'{self.prefix}-{key}.txt'
            logger.info(f'dumping text results to {path}')
            with open(path, 'w') as f:
                result.write(writer=f, verbose=True)