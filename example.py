from taskmanager import TaskQueue, Task, PythonTask


if __name__ == '__main__':
    task_queue = TaskQueue()
    task_queue.add_task(Task('Hello'))
    task_queue.add_task(Task('World'))
    task_queue.add_task(PythonTask('PythonTask1', 'pythonTask/task1.py', is_async=False))
    task_queue.add_task(Task('Python'))
    task_queue.add_task(Task('TQDM'))
    task_queue.add_task(Task('Rich'))
    task_queue.add_task(Task('Progress'))

    task_queue.run()