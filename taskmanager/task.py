import time
import subprocess

class Task:
    def __init__(self, name):
        self.name = name

    def __call__(self):
        time.sleep(2)
        return self.name
        

class NormalTask(Task):
    def __init__(self, name):
        super().__init__(name)

    def __call__(self):
        print('This is normal task1')
        time.sleep(2)

class PythonTask(Task):
    def __init__(self, name, python_entry, is_async=False):
        super().__init__(name)
        self.python_entry = python_entry
        self.is_async = is_async

    def __call__(self):
        process = subprocess.Popen(['python', self.python_entry], stdout=subprocess.PIPE)
        output = process.communicate()[0]
        if self.is_async:
            process.wait()
        return output.decode('utf-8')