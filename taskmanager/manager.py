from tqdm.rich import tqdm
import time
import logging
import subprocess
import os

LOG_PATH = 'logs'

if not os.path.exists('logs'):
    os.makedirs('logs')

class TaskQueue:
    def __init__(self, name='TaskQueue', ):
        self.tasks = []
        self.name = name
        self.dir_path = os.path.join(LOG_PATH, f"{name}_{time.strftime('%Y%m%d%H%M%S')}") 
        
        # logger
        self.logger = logging.getLogger(name)
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        self.logger.addHandler(logging.FileHandler(os.path.join(self.dir_path, 'log.txt')))
        self.logger.addHandler(logging.StreamHandler())
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger.handlers[0].setFormatter(formatter)
        self.logger.handlers[1].setFormatter(formatter)
        self.logger.setLevel(logging.INFO)

    def add_task(self, task):
        self.tasks.append(task)

    def run(self):
        for task in tqdm(self.tasks):
            self.logger.info('Running task: %s', task.name)
            output = task()
            self.logger.info('Task %s completed', task.name)
            with open(os.path.join(self.dir_path, task.name + '.txt'), 'w') as f:
                if output:
                    f.write(output)