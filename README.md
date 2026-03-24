# TaskManager

一个轻量的 Python 任务队列，用于**串行执行**本地任务、Python 脚本和函数，并为队列和单个任务分别保存日志。

## 功能概览

- 按添加顺序串行执行任务
- 支持 `NormalTask`、`FunctionTask`、`PythonTask`
- 自动为每次队列运行创建独立日志目录
- 为每个任务保存单独日志文件
- 通过返回码判断成功/失败
- 支持失败后停止或继续执行
- 支持任务失败回调 `errorFunction`

## 安装

本仓库默认使用 `uv` 管理依赖与运行命令。

```bash
uv sync
```

如果只想在当前环境中运行命令，也可以直接使用：

```bash
uv run python -c "import taskmanager; print('ok')"
```

## 快速开始

下面的示例与 [example.py](example.py) 保持一致：

```python
import time
from taskmanager import TaskQueue, PythonTask, NormalTask, FunctionTask


def function1():
    print('Function1 is running...')
    time.sleep(2)
    return 0


task_queue = TaskQueue(name='ExampleQueue', log_in_console=True, ignore_fail=True)
task_queue.add_task(NormalTask('Hello'))
task_queue.add_task(PythonTask('PythonTask1', 'pythonTask/task1.py'))
task2_args = ['--args1', 'arg1', '--args2', 'arg2']
task_queue.add_task(PythonTask('PythonTask2', 'pythonTask/task2.py', args=task2_args))
task_queue.add_task(PythonTask('PythonTask3', 'pythonTask/task3.py'))
task_queue.add_task(FunctionTask('FunctionTask1', function1))
task_queue.add_task(NormalTask('World'))
task_queue.run()
```

运行示例：

```bash
uv run python example.py
```

## 核心概念

### TaskQueue

`TaskQueue` 负责管理任务列表并按顺序执行。

主要参数：

- `name`：队列名称，同时用于生成日志目录名
- `log_in_file`：是否写入队列级日志文件
- `log_in_console`：是否输出日志到控制台
- `ignore_fail`：任务失败后是否继续执行后续任务
- `errorFunction`：任务失败时调用的回调函数

任务通过 `add_task()` 添加，通过 `run()` 启动执行。

### Task

`Task` 是基础任务协议。当前队列通过调用任务对象本身执行任务，即任务对象需要实现 `__call__(file_handler=None)`，并返回整数状态码：

- `0`：成功
- 非 `0`：失败

### NormalTask

`NormalTask` 是一个简单示例任务，会输出提示并暂停 2 秒，适合占位或快速演示。

### FunctionTask

`FunctionTask` 用于包装普通 Python 函数。函数返回值会被当作任务返回码。

### PythonTask

`PythonTask` 用于运行外部 Python 脚本，底层会启动子进程并异步读取 `stdout` / `stderr`，再写入日志。

可通过 `args` 传入脚本参数，例如：

```python
PythonTask('PythonTask2', 'pythonTask/task2.py', args=['--args1', 'arg1'])
```

## 日志说明

导入 `taskmanager` 包时会自动初始化日志目录。

每次运行队列时，会在日志根目录下创建一个新目录：

```text
logs/<queue_name>_<timestamp>/
```

目录中包含：

- `log.txt`：队列级总日志
- `<task_name>.txt`：单个任务的输出日志

如果需要修改日志根目录，可使用 `taskmanager.manager.set_log_path(path)`。当前实现会在导入时先创建默认 `logs/` 目录，之后新建队列时再使用最新的 `LOG_PATH`。

## 失败处理

队列通过任务返回码判断是否失败：

- 返回 `0`：任务成功
- 返回非 `0`：任务失败

失败时的行为：

- `ignore_fail=False`：立即停止后续任务
- `ignore_fail=True`：记录失败并继续执行后续任务
- 如果提供了 `errorFunction`，失败时会先调用该回调

`pythonTask/task3.py` 就是一个失败示例任务。

## 当前限制

- 当前队列是**串行执行**，不支持并行调度多个任务
- `PythonTask` 的“异步”仅用于异步读取子进程输出，不代表多个任务并发执行
- `PythonTask` 当前使用 `python <script>` 形式启动脚本，因此依赖运行环境中可用的 `python` 命令
- `taskmanager` 在导入时会创建默认日志目录，这是当前包的导入副作用
- 仓库当前没有单独的 lint 或 build 工作流，主要通过示例和测试验证功能

## 运行与测试

运行示例：

```bash
uv run python example.py
```

运行全部测试：

```bash
uv run python -m unittest discover -s tests
```

运行单个测试文件：

```bash
uv run python -m unittest tests.test_smoke
```

## 项目结构

```text
taskmanager/        核心包
pythonTask/         示例脚本任务
example.py          示例入口
tests/              最小 smoke tests
```

## License

[MIT](LICENSE)
