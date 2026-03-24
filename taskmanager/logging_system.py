import logging
import os
import time

from tqdm import tqdm as standard_tqdm
from tqdm.rich import tqdm as rich_tqdm

LOG_PATH = 'logs'


class TqdmLoggingHandler(logging.StreamHandler):
    def __init__(self, tqdm_impl):
        super().__init__()
        self.tqdm = tqdm_impl

    def emit(self, record):
        try:
            message = self.format(record)
            self.tqdm.write(message)
            self.flush()
        except Exception:
            self.handleError(record)


class NullProgress:
    def update(self, *_):
        return None

    def close(self):
        return None


def set_log_path(path):
    global LOG_PATH
    LOG_PATH = path


def init():
    os.makedirs(LOG_PATH, exist_ok=True)


def get_tqdm(use_rich_progress):
    if not isinstance(use_rich_progress, bool):
        raise ValueError("use_rich_progress must be bool")
    if use_rich_progress:
        return rich_tqdm
    return standard_tqdm


class QueueLogContext:
    def __init__(
        self,
        name,
        log_in_file=True,
        log_in_console=True,
        use_rich_progress=False,
    ):
        self.name = name
        self.tqdm = get_tqdm(use_rich_progress)
        self.dir_path = os.path.join(LOG_PATH, f"{name}_{time.strftime('%Y%m%d%H%M%S')}")
        os.makedirs(self.dir_path, exist_ok=True)

        self.logger = logging.getLogger(name)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if log_in_file:
            file_handler = logging.FileHandler(os.path.join(self.dir_path, 'log.txt'))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        if log_in_console:
            console_handler = TqdmLoggingHandler(self.tqdm)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False


class TaskOutputLogManager:
    def __init__(self, dir_path):
        self.dir_path = dir_path

    def get_task_log_path(self, task_name):
        return os.path.join(self.dir_path, task_name + '.txt')

    def open_task_log(self, task_name):
        return open(self.get_task_log_path(task_name), 'w')
