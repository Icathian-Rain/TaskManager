import time
from taskmanager import TaskQueue, Task, PythonTask, NormalTask, FunctionTask

def function1():
    print('Function1 is running...')
    time.sleep(2)
    return 0


if __name__ == '__main__':
    task_queue = TaskQueue(name='Test', log_in_console=True, ignore_fail=True)
    # 普通任务
    task_queue.add_task(NormalTask('Hello'))
    # 普通python任务
    task_queue.add_task(PythonTask('PythonTask1', 'pythonTask/task1.py', is_async=False))
    # 带参数的python任务
    task2_args = ['--args1', 'arg1', '--args2', 'arg2']
    task_queue.add_task(PythonTask('PythonTask2', 'pythonTask/task2.py', is_async=False, args=task2_args))
    # 错误退出的python任务
    task_queue.add_task(PythonTask('PythonTask3', 'pythonTask/task3.py', is_async=False))
    # 函数任务
    task_queue.add_task(FunctionTask('FunctionTask1', function1))
    # 普通任务
    task_queue.add_task(NormalTask('World'))

    task_queue.run()