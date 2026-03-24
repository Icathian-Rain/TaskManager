import time
from taskmanager import TaskQueue, PythonTask, NormalTask, FunctionTask


def function1():
    print('Function1 is running...')
    time.sleep(2)
    return 0


if __name__ == '__main__':
    # 创建一个队列；ignore_fail=True 表示某个任务失败后继续执行后续任务
    # use_rich_progress=False 使用标准版 tqdm；改为 True 可切换到 rich
    task_queue = TaskQueue(
        name='ExampleQueue',
        log_in_console=True,
        ignore_fail=True,
        use_rich_progress=False,
    )

    # 普通占位任务
    task_queue.add_task(NormalTask('Hello'))

    # 运行一个 Python 脚本任务
    task_queue.add_task(PythonTask('PythonTask1', 'pythonTask/task1.py'))

    # 运行一个带命令行参数的 Python 脚本任务
    task2_args = ['--args1', 'arg1', '--args2', 'arg2']
    task_queue.add_task(PythonTask('PythonTask2', 'pythonTask/task2.py', args=task2_args))

    # 一个会失败的脚本任务，用于演示 ignore_fail=True 的行为
    task_queue.add_task(PythonTask('PythonTask3', 'pythonTask/task3.py'))

    # 包装普通 Python 函数为任务
    task_queue.add_task(FunctionTask('FunctionTask1', function1))

    # 再添加一个普通任务，方便观察失败后是否继续执行
    task_queue.add_task(NormalTask('World'))

    task_queue.run()
