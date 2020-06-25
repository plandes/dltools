"""Contains contain classes for results generated from training and testing a
model.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field, InitVar
from abc import ABCMeta, abstractmethod
import logging
import sys
from datetime import datetime
from io import TextIOWrapper
from typing import List, Dict
import sklearn.metrics as mt
import numpy as np
import torch
from zensols.config import Configurable, Writable
from zensols.persist import IncrementKeyDirectoryStash
from zensols.deeplearn import ModelSettings, NetworkSettings
from zensols.deeplearn.batch import Batch

logger = logging.getLogger(__name__)


class NoResultsException(Exception):
    """Convenience used for helping debug the network.

    """
    def __init__(self):
        super().__init__('no results available')


@dataclass
class ResultsContainer(Writable, metaclass=ABCMeta):
    PREDICTIONS_INDEX = 0
    LABELS_INDEX = 1

    @property
    def contains_results(self):
        """Return ``True`` if this container has results.

        """
        return len(self) > 0

    def _assert_results(self):
        "Raises an exception if there are no results."
        if not self.contains_results:
            raise NoResultsException()

    @property
    def min_loss(self) -> float:
        self._assert_results()
        return min(self.losses)

    @abstractmethod
    def get_outcomes(self) -> np.ndarray:
        """Return the outcomes as an array with the first row the provided labels and
        the second row the predictions.  If no labels are given during the
        prediction (i.e. evaluation) there will only be one row, which are the
        predictions.

        """
        pass

    @property
    def labels(self) -> np.ndarray:
        """Return the labels or ``None`` if none were provided (i.e. during
        test/evaluation).

        """
        self._assert_results()
        arr = self.get_outcomes()[self.LABELS_INDEX]
        if arr.shape[-1] > 1:
            arr = arr.flatten()
        return arr

    @property
    def predictions(self) -> np.ndarray:
        """Return the predictions from the model.

        """
        self._assert_results()
        arr = self.get_outcomes()[self.PREDICTIONS_INDEX]
        if arr.shape[-1] > 1:
            arr = arr.flatten()
        return arr

    @property
    def n_outcomes(self) -> int:
        return self.get_outcomes().shape[1]

    @property
    def accuracy(self) -> float:
        return mt.accuracy_score(self.labels, self.predictions)

    @property
    def n_correct(self) -> int:
        is_eq = np.equal(self.labels, self.predictions)
        return np.count_nonzero(is_eq == True)

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
    def micro_metrics(self) -> Dict[str, float]:
        """Compute F1, precision and recall.

        """
        self._assert_results()
        return self._compute_metrics('micro')

    @property
    def macro_metrics(self) -> Dict[str, float]:
        """Compute F1, precision and recall.

        """
        self._assert_results()
        return self._compute_metrics('macro')

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
    batch_losses: List[float] = field(default_factory=list)
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
        self.batch_losses.append(loss.item() * float(batch.size()))
        # batches are always the first dimension
        self.n_data_points.append(label_shape[0])
        # stack and append for metrics computation later
        res = torch.stack((preds, labels), 0)
        self.prediction_updates.append(res.cpu())
        self.batch_ids.append(batch.id)

    def get_outcomes(self) -> np.ndarray:
        self._assert_results()
        return np.concatenate(self.prediction_updates, 1)

    @property
    def ave_loss(self) -> float:
        """Return the average loss of this result set.

        """
        self._assert_results()
        return sum(self.batch_losses) / len(self.batch_losses)

    @property
    def losses(self) -> List[float]:
        """Return the loss for each epoch of the run.  If used on a ``EpocResult`` it
        is the Nth iteration.

        """
        return self.batch_losses

    def __getitem__(self, i: int) -> np.ndarray:
        return self.prediction_updates[i]

    def __len__(self):
        return len(self.batch_ids)

    def __str__(self):
        return f'{self.index}: ave loss: {self.ave_loss:.3f}, len: {len(self)}'

    def __repr__(self):
        return self.__str__()

    def write(self, depth: int = 0, writer: TextIOWrapper = sys.stdout):
        bids = ','.join(self.batch_ids)
        dps = ','.join(map(str, self.n_data_points))
        self._write_line(f'index: {self.index}', depth, writer)
        self._write_line(f'batch_ids: {bids}', depth, writer)
        self._write_line(f'data point IDS: {dps}', depth, writer)


@dataclass
class DatasetResult(ResultsContainer):
    """Contains results from training/validating or test cycle.

    :param results: the results generated from the iterations of the epoch

    """
    results: List[EpochResult] = field(default_factory=list)
    start_time: datetime = field(default=None)
    end_time: datetime = field(default=None)

    def append(self, epoch_result: EpochResult):
        self.results.append(epoch_result)

    @property
    def contains_results(self):
        return len(self.results) > 0

    def start(self):
        if self.contains_results:
            raise ValueError(f'container {self} already contains results')
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()

    @property
    def losses(self) -> List[float]:
        """Return the loss for each epoch of the run.  If used on a ``EpocResult`` it
        is the Nth iteration.

        """
        return tuple(map(lambda r: r.ave_loss, self.results))

    @property
    def ave_loss(self) -> float:
        loss_sum = sum(self.losses)
        batch_sum = sum(map(lambda r: len(r), self.results))
        return 0 if batch_sum == 0 else loss_sum / batch_sum

    def get_outcomes(self):
        prs = tuple(map(lambda r: r.get_outcomes(), self.results))
        return np.concatenate(prs, axis=1)

    @property
    def convergence(self):
        """Return the Nth epoch this result set convergened.  If used on a
        ``EpocResult`` it is the Nth iteration.

        """
        losses = self.losses
        lowest = min(losses)
        return losses.index(lowest)

    @property
    def convereged_epoch(self) -> EpochResult:
        idx = self.convergence
        return self.results[idx]

    def _format_time(self, attr: str):
        if hasattr(self, attr):
            val: datetime = getattr(self, attr)
            if val is not None:
                return val.strftime("%m/%d/%Y %H:%M:%S:%f")

    def __getitem__(self, i: int) -> EpochResult:
        return self.results[i]

    def write(self, depth: int = 0, writer: TextIOWrapper = sys.stdout,
              verbose: bool = False):
        micro = self.micro_metrics
        macro = self.macro_metrics
        er: EpochResult = self.convereged_epoch
        sp = self._sp(depth)
        writer.write(f'{sp}ave/min loss: {self.ave_loss:.5f}/' +
                     f'{er.min_loss:.5f}\n')
        writer.write(f'{sp}accuracy: {self.accuracy:.3f} ' +
                     f'({self.n_correct}/{self.n_outcomes})\n')
        writer.write(f"{sp}micro: F1: {micro['f1']:.3f}, " +
                     f"precision: {micro['precision']:.3f}, " +
                     f"recall: {micro['recall']:.3f}\n")
        writer.write(f"{sp}macro: F1: {macro['f1']:.3f}, " +
                     f"precision: {macro['precision']:.3f}, " +
                     f"recall: {macro['recall']:.3f}\n")
        if verbose:
            writer.write('e{sp}poch details:\n')
            self.results[0].write(depth + 1, writer)


@dataclass
class ModelResult(Writable):
    """A container class used to capture the training, validation and test results.
    The data captured is used to report and plot curves.

    :param config: useful for retrieving hyperparameter settings later after
                   unpersisting from disk

    :param model_settings: the setttings used to configure the model

    """
    TRAIN_DS_NAME = 'train'
    VALIDATION_DS_NAME = 'validation'
    TEST_DS_NAME = 'test'
    RUNS = 1

    config: Configurable
    name: str
    model_settings: InitVar[ModelSettings]
    net_settings: InitVar[NetworkSettings]

    def __post_init__(self, model_settings: ModelSettings,
                      net_settings: NetworkSettings):
        self.RUNS += 1
        self.index = self.RUNS
        splits = 'train validation test'.split()
        self.dataset_result = {k: DatasetResult() for k in splits}
        self.model_settings = model_settings.asdict('class_name')
        self.net_settings = net_settings.asdict('class_name')
        self.net_settings['module_class_name'] = net_settings.get_module_class_name()

    @classmethod
    def reset_runs(self):
        """Reset the run counter.

        """
        self.RUNS = 1

    @classmethod
    def get_num_runs(self):
        return self.RUNS

    def __getitem__(self, name: str) -> DatasetResult:
        return self.dataset_result[name]

    @property
    def train(self) -> DatasetResult:
        """Return the training run results.

        """
        return self.dataset_result[self.TRAIN_DS_NAME]

    @property
    def validation(self) -> DatasetResult:
        """Return the validation run results.

        """
        return self.dataset_result[self.VALIDATION_DS_NAME]

    @property
    def test(self) -> DatasetResult:
        """Return the testing run results.

        """
        return self.dataset_result[self.TEST_DS_NAME]

    def reset(self, name: str):
        logger.debug(f'restting dataset result \'{name}\'')
        self.dataset_result[name] = DatasetResult()

    @property
    def contains_results(self) -> bool:
        return len(self.test) > 0 or len(self.validation) > 0

    @property
    def last_test_dataset_result_name(self) -> str:
        if len(self.test) > 0:
            return self.TRAIN_DS_NAME
        if len(self.validation) > 0:
            return self.VALIDATION_DS_NAME
        raise NoResultsException()

    @property
    def last_test_dataset_result(self) -> DatasetResult:
        """Return either the test or validation results depending on what is available.

        """
        return self[self.last_test_dataset_result_name]

    def get_result_statistics(self, result_name: str):
        ds_result = self.dataset_result[result_name]
        epochs = ds_result.results
        n_data_points = 0
        n_batches = 0
        if len(epochs) > 0:
            epoch: EpochResult = epochs[0]
            n_data_points = epoch.n_data_points
            n_batches = len(epoch.batch_ids)
            for epoch in epochs:
                assert n_data_points == epoch.n_data_points
            n_data_points = sum(n_data_points) / len(n_data_points)
        return {'n_epochs': len(epochs),
                'n_epoch_converged': ds_result.convereged_epoch.index,
                'n_batches': n_batches,
                'n_data_points': n_data_points}

    def write_result_statistics(self, result_name: str, depth: int = 0,
                                writer=sys.stdout):
        stats = self.get_result_statistics(result_name)
        ave_dps = stats['n_data_points']
        sp = self._sp(depth)
        writer.write(f"{sp}batches: {stats['n_batches']}\n")
        writer.write(f"{sp}ave data points per batch: {ave_dps:.1f}\n")
        writer.write(f"{sp}converged/epochs: {stats['n_epoch_converged']}/" +
                     f"{stats['n_epochs']}\n")

    def write(self, depth: int = 0, writer: TextIOWrapper = sys.stdout,
              verbose=False):
        """Generate a human readable format of the results.

        """
        self._write_line(f'Name: {self.name}', depth, writer)
        self._write_line(f'Run index: {self.index}', depth, writer)
        self._write_line(f'Learning rate: {self.model_settings["learning_rate"]}',
                         depth, writer)
        sp = self._sp(depth + 1)
        spe = self._sp(depth + 2)
        ds_res: DatasetResult
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
            self._write_dict(self.model_settings, depth + 1, writer)
            self._write_line('network settings:', depth, writer)
            self._write_dict(self.net_settings, depth + 1, writer)

    def __str__(self):
        model_name = self.net_settings['module_class_name']
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
