import time
import subprocess
from .asyncSubprocess import AsyncSubprocess
import asyncio

async def file_callback(tag, line, file_handler):
    file_handler.write(f'[{tag}] {line}\n')
    file_handler.flush()

class Task:
    def __init__(self, name):
        self.name = name

    def __call__(self, file_handler=None):
        return 0
        

class NormalTask(Task):
    def __init__(self, name):
        super().__init__(name)

    def __call__(self, file_handler=None):
        if file_handler:
            file_handler.write(f"Task {self.name} is running...\n")
        else:
            print(f"Task {self.name} is running...")
        time.sleep(2)
        return 0
    
class FunctionTask(Task):
    def __init__(self, name, function, args=None):
        super().__init__(name)
        self.function = function
        self.args = args

    def __call__(self, file_handler=None):
        if file_handler:
            file_handler.write(f"Task {self.name} is running...\n")
        else:
            print(f"Task {self.name} is running...")
        if self.args:
            return_code = self.function(*self.args)
        else:
            return_code = self.function()
        return return_code

class PythonTask(Task):
    def __init__(self, name, python_entry, is_async=False, args=None):
        super().__init__(name)
        self.python_entry = python_entry
        self.is_async = is_async
        self.command = ['python', self.python_entry]
        if args:
            for arg in args:
                self.command.append(arg)

    def __call__(self, file_handler=None):
        process = AsyncSubprocess(self.command)
        if file_handler:
            call_back = lambda tag, line: file_callback(tag, line, file_handler)
        else:
            call_back = lambda tag, line: print(f'[{tag}] {line}')
        return_code = asyncio.run(process.run(stdout_callback=call_back,
                       stderr_callback=call_back))
        return return_code