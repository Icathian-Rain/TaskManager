from tqdm.rich import tqdm
import time
import logging
import os

LOG_PATH = 'logs'

def set_log_path(path):
    global LOG_PATH
    LOG_PATH = path

def init():
    if not os.path.exists('logs'):
        os.makedirs('logs')

class TaskQueue:
    def __init__(self, name='TaskQueue', log_in_file=True, log_in_console=True, ignore_fail=False, errorFunction=None):
        self.tasks = []
        self.name = name
        self.dir_path = os.path.join(LOG_PATH, f"{name}_{time.strftime('%Y%m%d%H%M%S')}") 
        self.ignore_fail = ignore_fail
        self.errorFunction = errorFunction
        
        # logger
        self.logger = logging.getLogger(name)
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if log_in_file:
            file_handler = logging.FileHandler(os.path.join(self.dir_path, 'log.txt'))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        if log_in_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)


    def add_task(self, task):
        self.tasks.append(task)

    def run(self):
        for task in tqdm(self.tasks):
            self.logger.info('-'*50)
            self.logger.info('[Begin] Running task: %s', task.name)
            file_handler = open(os.path.join(self.dir_path, task.name + '.txt'), 'w')
            return_code = task(file_handler)
            file_handler.close()
            self.logger.info('[ End ] Task %s completed, Return: %s', task.name, str(return_code))
            # 如果任务失败
            if return_code != 0:
                self.logger.error('Task %s failed', task.name)
                if self.errorFunction:
                    self.errorFunction()
                # 如果设置了忽略失败
                if not self.ignore_fail:
                    self.logger.error('TaskQueue stopped due to task %s failed', task.name)
                    return
            self.logger.info('-'*50)
        self.logger.info('All tasks completed')