import tempfile
import unittest
import uuid

from taskmanager import FunctionTask, TaskQueue
from taskmanager import manager as manager_module
from taskmanager.manager import TqdmLoggingHandler, set_log_path


class TaskQueueSmokeTests(unittest.TestCase):
    def setUp(self):
        self.original_log_path = manager_module.LOG_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        self.loggers = []
        set_log_path(self.temp_dir.name)

    def tearDown(self):
        for logger in self.loggers:
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
        set_log_path(self.original_log_path)
        self.temp_dir.cleanup()

    def make_queue(self, ignore_fail=False, error_function=None, use_rich_progress=False):
        queue = TaskQueue(
            name=f"TestQueue_{uuid.uuid4().hex}",
            log_in_console=False,
            ignore_fail=ignore_fail,
            errorFunction=error_function,
            use_rich_progress=use_rich_progress,
        )
        self.loggers.append(queue.logger)
        return queue

    def run_queue(self, queue):
        queue.tqdm = lambda tasks: tasks
        queue.run()

    def test_tasks_run_in_order(self):
        events = []

        def first_task():
            events.append("first")
            return 0

        def second_task():
            events.append("second")
            return 0

        queue = self.make_queue()
        queue.add_task(FunctionTask("first", first_task))
        queue.add_task(FunctionTask("second", second_task))

        self.run_queue(queue)

        self.assertEqual(events, ["first", "second"])

    def test_queue_stops_after_failure_by_default(self):
        events = []

        def success_task():
            events.append("success")
            return 0

        def fail_task():
            events.append("fail")
            return 1

        def should_not_run():
            events.append("after_fail")
            return 0

        queue = self.make_queue()
        queue.add_task(FunctionTask("success", success_task))
        queue.add_task(FunctionTask("fail", fail_task))
        queue.add_task(FunctionTask("after_fail", should_not_run))

        self.run_queue(queue)

        self.assertEqual(events, ["success", "fail"])

    def test_queue_continues_when_ignore_fail_is_true(self):
        events = []
        error_calls = []

        def fail_task():
            events.append("fail")
            return 1

        def after_fail():
            events.append("after_fail")
            return 0

        def on_error():
            error_calls.append("called")

        queue = self.make_queue(ignore_fail=True, error_function=on_error)
        queue.add_task(FunctionTask("fail", fail_task))
        queue.add_task(FunctionTask("after_fail", after_fail))

        self.run_queue(queue)

        self.assertEqual(events, ["fail", "after_fail"])
        self.assertEqual(error_calls, ["called"])

    def test_default_progress_bar_is_standard(self):
        queue = self.make_queue()

        self.assertFalse(queue.use_rich_progress)
        self.assertIs(queue.tqdm, manager_module.standard_tqdm)

    def test_console_logging_uses_selected_tqdm_writer(self):
        queue = TaskQueue(name=f"TestQueue_{uuid.uuid4().hex}", log_in_file=False, log_in_console=True)
        self.loggers.append(queue.logger)

        console_handlers = [
            handler for handler in queue.logger.handlers if isinstance(handler, TqdmLoggingHandler)
        ]

        self.assertEqual(len(console_handlers), 1)
        self.assertIs(console_handlers[0].tqdm, manager_module.standard_tqdm)
        self.assertFalse(queue.logger.propagate)

    def test_rich_progress_bar_is_available(self):
        queue = TaskQueue(
            name=f"TestQueue_{uuid.uuid4().hex}",
            log_in_file=False,
            log_in_console=True,
            use_rich_progress=True,
        )
        self.loggers.append(queue.logger)

        console_handlers = [
            handler for handler in queue.logger.handlers if isinstance(handler, TqdmLoggingHandler)
        ]

        self.assertTrue(queue.use_rich_progress)
        self.assertIs(queue.tqdm, manager_module.rich_tqdm)
        self.assertEqual(len(console_handlers), 1)
        self.assertIs(console_handlers[0].tqdm, manager_module.rich_tqdm)

    def test_invalid_progress_bar_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.make_queue(use_rich_progress='invalid')
