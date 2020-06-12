"""Client entry point to the model.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field, InitVar
import sys
import logging
import pandas as pd
from io import TextIOWrapper
from zensols.config import Configurable, ConfigFactory
from zensols.persist import persisted, Deallocatable, PersistedWork
from zensols.util import time
from zensols.deeplearn.vectorize import SparseTensorFeatureContext
from . import ModelManager, ModelExecutor

logger = logging.getLogger(__name__)


@dataclass
class ModelFacade(Deallocatable):
    """Provides easy to use client entry points to the model executor, which
    trains, validates, tests, saves and loads the model.

    :param factory: the factory used to create the executor

    :param progress_bar: create text/ASCII based progress bar if ``True``

    :param progress_bar_cols: the number of console columns to use for the
                              text/ASCII based progress bar

    :param debug: if ``True``, raise an error on the first forward pass when
                  training the model

    :param executor_name: the configuration entry name for the executor, which
                          defaults to ``executor``

    :see zensols.deeplearn.domain.ModelSettings:

    """
    factory: ConfigFactory
    progress_bar: bool = field(default=True)
    progress_bar_cols: int = field(default=79)
    debug: bool = field(default=False)
    executor_name: str = field(default='executor')
    cache_executor: InitVar[bool] = field(default=False)

    def __post_init__(self, cache_executor: bool):
        self._executor = PersistedWork(
            '_executor', self, cache_global=cache_executor)

    @property
    @persisted('_executor')
    def executor(self) -> ModelExecutor:
        """Return a cached instance of the executor tied to the instance of this class.

        """
        return self._create_executor()

    def _create_executor(self) -> ModelExecutor:
        executor = self.factory(
            self.executor_name,
            progress_bar=self.progress_bar,
            progress_bar_cols=self.progress_bar_cols)
        executor.net_settings.debug = self.debug
        return executor

    def deallocate(self):
        super().deallocate()
        executor = self.executor
        executor.deallocate()
        self._executor.clear()

    @property
    def config(self) -> Configurable:
        """Return the configuration used to created resources for the facade.

        """
        return self.factory.config

    def train(self, deallocate: bool = False):
        """Train and test or just debug the model depending on the configuration.

        """
        executor = self.executor
        executor.reset()
        try:
            if self.debug:
                self._configure_debug_logging()
                executor.progress_bar = False
                executor.model_settings.batch_limit = 1
            executor.write()
            logger.info('training...')
            with time('trained'):
                res = executor.train()
            if not self.debug:
                logger.info('testing...')
                with time('tested'):
                    res = executor.test()
                res.write()
        finally:
            if deallocate:
                self.deallocate()

    def test(self, deallocate: bool = False):
        """Load the model from disk and test it.

        """
        try:
            path = self.config.populate(section='model_settings').path
            logger.info(f'testing from path: {path}')
            mm = ModelManager(path, self.factory)
            executor = mm.load_executor()
            res = executor.test()
            res.write(verbose=False)
        finally:
            if deallocate:
                self.deallocate()

    def write_results(self, depth: int = 0, writer: TextIOWrapper = sys.stdout,
                      verbose: bool = False):
        """Load the last set of results from the file system and print them out.

        """
        logging.getLogger('zensols.deeplearn.result').setLevel(logging.INFO)
        logger.info('load previous results')
        rm = self.executor.result_manager
        if rm is None:
            rm = ValueError('no result manager available')
        res = rm.load()
        if res is None:
            raise ValueError('no results found')
        res.write(depth, writer, verbose)

    def get_predictions(self, *args, **kwargs) -> pd.DataFrame:
        """Return the predictions made during the test phase of the model execution.
        The arguments are passed to :meth:`ModelExecutor.get_predictions`.

        :see: :meth:`.ModelExecutor.get_predictions`

        """
        executor = self.executor
        executor.load()
        return executor.get_predictions(*args, **kwargs)

    def write_predictions(self, lines: int = 10,
                          writer: TextIOWrapper = sys.stdout):
        """Print the predictions made during the test phase of the model execution.

        :param lines: the number of lines of the predictions data frame to be
                      printed

        :param writer: the data sink

        """
        preds = self.get_predictions()
        print(preds.head(lines), file=writer)

    def _configure_debug_logging(self):
        """When debuging the model, configure the logging system for output.  The
        correct loggers need to be set to debug mode to print the model
        debugging information such as matrix shapes.

        """
        lg = logging.getLogger('zensols.deepnlp.vectorize.vectorizers')
        lg.setLevel(logging.INFO)
        lg = logging.getLogger(__name__ + '.module')
        lg.setLevel(logging.DEBUG)

    @staticmethod
    def get_encode_sparse_matrices() -> bool:
        """Return whether or not sparse matricies are encoded.

        :see: :meth:`set_sparse`

        """
        return SparseTensorFeatureContext.USE_SPARSE

    @staticmethod
    def set_encode_sparse_matrices(use_sparse: bool = False):
        """If called before batches are created, encode all tensors the would be
        encoded as dense rather than sparse when ``use_sparse`` is ``False``.
        Oherwise, tensors will be encoded as sparse where it makes sense on a
        per vectorizer basis.

        """
        SparseTensorFeatureContext.USE_SPARSE = use_sparse
