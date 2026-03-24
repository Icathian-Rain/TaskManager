from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import traceback

from . import logging_system
from .logging_system import (
    NullProgress,
    QueueLogContext,
    TaskOutputLogManager,
    TqdmLoggingHandler,
    get_tqdm,
    init,
    rich_tqdm,
    set_log_path,
    standard_tqdm,
)


def __getattr__(name):
    if name == 'LOG_PATH':
        return logging_system.LOG_PATH
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def validate_max_workers(max_workers):
    if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
        raise ValueError("max_workers must be a positive integer")
    return max_workers


class TaskQueue:
    def __init__(
        self,
        name='TaskQueue',
        log_in_file=True,
        log_in_console=True,
        ignore_fail=False,
        errorFunction=None,
        use_rich_progress=False,
        max_workers=1,
    ):
        self.tasks = []
        self.name = name
        self.ignore_fail = ignore_fail
        self.errorFunction = errorFunction
        self.use_rich_progress = use_rich_progress
        self.max_workers = validate_max_workers(max_workers)

        self.log_context = QueueLogContext(
            name=name,
            log_in_file=log_in_file,
            log_in_console=log_in_console,
            use_rich_progress=use_rich_progress,
        )
        self.task_output_logs = TaskOutputLogManager(self.log_context.dir_path)

        self.dir_path = self.log_context.dir_path
        self.logger = self.log_context.logger
        self.tqdm = self.log_context.tqdm

    def add_task(self, task):
        self.tasks.append(task)

    def _create_progress(self, total):
        try:
            return self.tqdm(total=total)
        except TypeError:
            return NullProgress()

    def _validate_task_names(self):
        seen = set()
        duplicates = []
        for task in self.tasks:
            if task.name in seen and task.name not in duplicates:
                duplicates.append(task.name)
            seen.add(task.name)
        if duplicates:
            raise ValueError(f"Task names must be unique: {', '.join(duplicates)}")

    def _run_task(self, task):
        self.logger.info('-' * 50)
        self.logger.info('[Begin] Running task: %s', task.name)
        return_code = 1
        exception_trace = None

        with self.task_output_logs.open_task_log(task.name) as file_handler:
            try:
                return_code = task(file_handler)
            except Exception:
                exception_trace = traceback.format_exc()
                file_handler.write(exception_trace)
                file_handler.flush()

        self.logger.info('[ End ] Task %s completed, Return: %s', task.name, str(return_code))
        if exception_trace:
            self.logger.error('Task %s raised an exception:\n%s', task.name, exception_trace.rstrip())

        return {
            'task': task,
            'return_code': return_code,
        }

    def _handle_task_result(self, result):
        task = result['task']
        return_code = result['return_code']
        if return_code != 0:
            self.logger.error('Task %s failed', task.name)
            if self.errorFunction:
                self.errorFunction()
            if self.ignore_fail:
                self.logger.info('-' * 50)
            return True

        self.logger.info('-' * 50)
        return False

    def _run_serial(self):
        for task in self.tqdm(self.tasks):
            result = self._run_task(task)
            failed = self._handle_task_result(result)
            if failed and not self.ignore_fail:
                self.logger.error('TaskQueue stopped due to task %s failed', task.name)
                return
        self.logger.info('All tasks completed')

    def _run_parallel(self):
        task_iter = iter(self.tasks)
        futures = {}
        submitted_count = 0
        stop_submitting = False
        failed_task_name = None
        progress = self._create_progress(len(self.tasks))

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while len(futures) < self.max_workers:
                    task = next(task_iter, None)
                    if task is None:
                        break
                    futures[executor.submit(self._run_task, task)] = task
                    submitted_count += 1

                while futures:
                    done, _ = wait(futures, return_when=FIRST_COMPLETED)
                    completed_count = 0

                    for future in done:
                        completed_count += 1
                        futures.pop(future)
                        result = future.result()
                        progress.update(1)
                        failed = self._handle_task_result(result)
                        if failed and not self.ignore_fail and failed_task_name is None:
                            stop_submitting = True
                            failed_task_name = result['task'].name

                    if stop_submitting:
                        continue

                    for _ in range(completed_count):
                        task = next(task_iter, None)
                        if task is None:
                            break
                        futures[executor.submit(self._run_task, task)] = task
                        submitted_count += 1
        finally:
            progress.close()

        if stop_submitting:
            if submitted_count < len(self.tasks):
                self.logger.error('TaskQueue stopped due to task %s failed', failed_task_name)
            return

        self.logger.info('All tasks completed')

    def run(self):
        self._validate_task_names()
        if self.max_workers == 1:
            self._run_serial()
            return
        self._run_parallel()
