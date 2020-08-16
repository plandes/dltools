"""Contains a class to assist in the training lifecycle of the
:class:`.ModelExecutor`.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
from enum import Enum
import sys
import logging
import json
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger(__name__)


class UpdateAction(Enum):
    """An action type to invoke on the :class:`.ModelExecutor` during training.

    """
    ITERATE_EPOCH = 0
    SET_EPOCH = 1
    STOP = 2


@dataclass
class LifeCycleStatus(object):
    """Indicates what to do in the next epoch of the training cycle.

    """
    action: UpdateAction
    epoch: int = field(default=None)


@dataclass
class LifeCycleManager(object):
    """The class is used to assist in the training lifecycle of the
    :class:`.ModelExecutor`.  It watches for a file on the file system to
    provide instructions on what to do in the next epoch.

    """
    update_path: Path
    pbar: tqdm = field(default=None)
    current_epoch: int = field(default=0)

    def reset(self, pbar: tqdm):
        # clear any early stop state
        if self.update_path is not None and self.update_path.is_file():
            logger.info(f'cleaning update file: {self.update_path}')
            self.update_path.unlink()
        self.pbar = pbar
        self.current_epoch = 0
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'watching update file {self.update_path}')

    def _read_status(self) -> LifeCycleStatus:
        """Read the early stop/update file and return a value to update the current
        epoch number (if any).

        """
        update = LifeCycleStatus(UpdateAction.ITERATE_EPOCH)
        update_path = self.update_path
        if update_path is not None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'update check at {update_path}')
            if update_path.exists():
                data = None
                try:
                    with open(update_path) as f:
                        data = json.load(f)
                    if 'epoch' in data:
                        epoch = int(data['epoch'])
                        if logger.isEnabledFor(logging.INFO):
                            logger.info(f'setting epoch to: {epoch}')
                        update.epoch = epoch
                        update.action = UpdateAction.SET_EPOCH
                except Exception as e:
                    if logger.isEnabledFor(logging.INFO):
                        logger.info('unsuccessful parse of ' +
                                    f'{update_path}--assume exit: {e}')
                    update.action = UpdateAction.STOP
                update_path.unlink()
        return update

    def get_status(self) -> LifeCycleStatus:
        """Return the epoch to set in the training loop of the :class:`.ModelExecutor`.

        """
        status = self._read_status()
        if status.action == UpdateAction.STOP:
            # setting to the max value fails the executors train outter loop
            # causing a robust non-error exit
            status.epoch = sys.maxsize
        elif status.action == UpdateAction.SET_EPOCH:
            self.current_epoch = status.epoch
            if self.pbar is not None:
                self.pbar.reset()
                self.pbar.update(self.current_epoch)
        elif status.action == UpdateAction.ITERATE_EPOCH:
            self.current_epoch += 1
            status.epoch = self.current_epoch
            if self.pbar is not None:
                self.pbar.update()
        else:
            raise ValueError(f'unknownn status: {status}')
        return status

    def stop(self) -> bool:
        """Stops the execution of training the model.

        Currently this is done by creating a file the executor monitors.

        """
        update_path = self.update_path
        if update_path is not None and not update_path.is_file():
            update_path.touch()
            logger.info(f'created early stop file: {update_path}')
            return True
        return False
