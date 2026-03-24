import os
import tempfile
import unittest
import uuid

from taskmanager.logging_system import QueueLogContext, TaskOutputLogManager, init, set_log_path
from taskmanager import manager as manager_module


class LoggingSystemTests(unittest.TestCase):
    def setUp(self):
        self.original_log_path = manager_module.LOG_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        set_log_path(self.temp_dir.name)
        self.loggers = []

    def tearDown(self):
        for logger in self.loggers:
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
        set_log_path(self.original_log_path)
        self.temp_dir.cleanup()

    def test_init_creates_current_log_directory(self):
        target = os.path.join(self.temp_dir.name, 'custom_logs')
        set_log_path(target)

        init()

        self.assertTrue(os.path.isdir(target))

    def test_queue_log_context_creates_log_txt(self):
        context = QueueLogContext(name=f"TestQueue_{uuid.uuid4().hex}")
        self.loggers.append(context.logger)

        self.assertTrue(os.path.isdir(context.dir_path))
        self.assertTrue(os.path.exists(os.path.join(context.dir_path, 'log.txt')))

    def test_task_output_log_manager_creates_task_log(self):
        context = QueueLogContext(name=f"TestQueue_{uuid.uuid4().hex}")
        self.loggers.append(context.logger)
        task_logs = TaskOutputLogManager(context.dir_path)

        with task_logs.open_task_log('task1') as file_handler:
            file_handler.write('hello task output\n')

        task_log_path = os.path.join(context.dir_path, 'task1.txt')
        self.assertTrue(os.path.exists(task_log_path))
        with open(task_log_path, 'r', encoding='utf-8') as file_handler:
            self.assertEqual(file_handler.read(), 'hello task output\n')

    def test_manager_log_path_stays_in_sync(self):
        target = os.path.join(self.temp_dir.name, 'synced_logs')

        set_log_path(target)

        self.assertEqual(manager_module.LOG_PATH, target)
