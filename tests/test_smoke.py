import os
import tempfile
import threading
import time
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

    def make_queue(
        self,
        ignore_fail=False,
        error_function=None,
        use_rich_progress=False,
        max_workers=1,
        log_in_file=True,
        log_in_console=False,
    ):
        queue = TaskQueue(
            name=f"TestQueue_{uuid.uuid4().hex}",
            log_in_file=log_in_file,
            log_in_console=log_in_console,
            ignore_fail=ignore_fail,
            errorFunction=error_function,
            use_rich_progress=use_rich_progress,
            max_workers=max_workers,
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

    def test_invalid_max_workers_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.make_queue(max_workers=0)

        with self.assertRaises(ValueError):
            self.make_queue(max_workers='2')

    def test_duplicate_task_names_raise_value_error(self):
        queue = self.make_queue()
        queue.add_task(FunctionTask("duplicate", lambda: 0))
        queue.add_task(FunctionTask("duplicate", lambda: 0))

        with self.assertRaises(ValueError):
            self.run_queue(queue)

    def test_tasks_can_run_concurrently(self):
        state = {
            "active": 0,
            "max_active": 0,
            "started": 0,
        }
        started_event = threading.Event()
        lock = threading.Lock()

        def concurrent_task():
            with lock:
                state["active"] += 1
                state["max_active"] = max(state["max_active"], state["active"])
                state["started"] += 1
                if state["started"] == 2:
                    started_event.set()
            started_event.wait(timeout=0.5)
            time.sleep(0.05)
            with lock:
                state["active"] -= 1
            return 0

        queue = self.make_queue(max_workers=2)
        queue.add_task(FunctionTask("first", concurrent_task))
        queue.add_task(FunctionTask("second", concurrent_task))

        self.run_queue(queue)

        self.assertEqual(state["max_active"], 2)

    def test_parallel_queue_creates_log_files(self):
        queue = self.make_queue(max_workers=2)
        queue.add_task(FunctionTask("first", lambda: 0))
        queue.add_task(FunctionTask("second", lambda: 0))

        self.run_queue(queue)

        self.assertTrue(os.path.exists(os.path.join(queue.dir_path, 'log.txt')))
        self.assertTrue(os.path.exists(os.path.join(queue.dir_path, 'first.txt')))
        self.assertTrue(os.path.exists(os.path.join(queue.dir_path, 'second.txt')))

    def test_parallel_queue_stops_submitting_after_failure(self):
        started = []
        error_calls = []
        running_started = threading.Event()
        lock = threading.Lock()

        def fail_task():
            running_started.wait(timeout=0.2)
            with lock:
                started.append("fail")
            return 1

        def running_task():
            with lock:
                started.append("running")
            running_started.set()
            time.sleep(0.2)
            return 0

        def should_not_run():
            with lock:
                started.append("after_fail")
            return 0

        def on_error():
            error_calls.append("called")

        queue = self.make_queue(max_workers=2, error_function=on_error)
        queue.add_task(FunctionTask("fail", fail_task))
        queue.add_task(FunctionTask("running", running_task))
        queue.add_task(FunctionTask("after_fail", should_not_run))

        self.run_queue(queue)

        self.assertCountEqual(started, ["fail", "running"])
        self.assertNotIn("after_fail", started)
        self.assertEqual(error_calls, ["called"])
