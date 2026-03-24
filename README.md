# TaskManager

一个轻量的 Python 任务队列，用于按顺序或并发运行本地任务、Python 脚本和函数，并为队列和单个任务分别保存日志。

## 功能概览

- 支持按添加顺序串行执行任务
- 支持通过 `max_workers` 开启并发执行多个任务
- 支持 `NormalTask`、`FunctionTask`、`PythonTask`
- 自动为每次队列运行创建独立日志目录
- 为每个任务保存单独日志文件
- 通过返回码判断成功/失败
- 支持失败后停止或继续执行
- 支持任务失败回调 `errorFunction`
- 支持通过布尔参数切换标准版或 rich 版进度条，默认使用标准版 `tqdm`

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


task_queue = TaskQueue(
    name='ExampleQueue',
    log_in_console=True,
    ignore_fail=True,
    use_rich_progress=False,
    max_workers=2,
)
task_queue.add_task(NormalTask('Hello'))
task_queue.add_task(PythonTask('PythonTask1', 'pythonTask/task1.py'))
task2_args = ['--args1', 'arg1', '--args2', 'arg2']
task_queue.add_task(PythonTask('PythonTask2', 'pythonTask/task2.py', args=task2_args))
task_queue.add_task(PythonTask('PythonTask3', 'pythonTask/task3.py'))
task_queue.add_task(FunctionTask('FunctionTask1', function1))
task_queue.add_task(NormalTask('World'))
task_queue.run()
```

如果想使用 rich 风格进度条，可将 `use_rich_progress` 设为 `True`。

如果想保持原来的串行行为，可将 `max_workers` 保持默认值 `1`。

运行示例：

```bash
uv run python example.py
```

## 核心概念

### TaskQueue

`TaskQueue` 负责管理任务列表并执行任务。

主要参数：

- `name`：队列名称，同时用于生成日志目录名
- `log_in_file`：是否写入队列级日志文件
- `log_in_console`：是否输出日志到控制台
- `ignore_fail`：任务失败后是否继续执行后续任务
- `errorFunction`：任务失败时调用的回调函数
- `use_rich_progress`：是否使用 rich 版进度条；`False` 为标准版 `tqdm`，`True` 为 rich 版，默认 `False`
- `max_workers`：最大并发任务数；默认 `1` 表示串行执行，大于 `1` 时启用并发

任务通过 `add_task()` 添加，通过 `run()` 启动执行。

补充说明：

- `max_workers=1` 时，行为与旧版本一致，任务严格串行执行
- `max_workers>1` 时，队列会并发运行多个任务
- 并发模式下每个任务仍会写入自己的独立日志文件
- 同一个队列中的 `task.name` 必须唯一，否则会抛出异常，避免日志文件冲突

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

目录中包含两类不同职责的日志：

- `log.txt`：`TaskQueue` 事件日志，记录任务开始、结束、失败、队列停止、全部完成等事件
- `<task_name>.txt`：单个任务的输出日志，记录任务运行时写入的内容，以及异常 traceback

如果启用了控制台日志，队列事件日志会通过当前选中的进度条实现写入，避免打断进度条显示。

如果需要修改日志根目录，可使用 `taskmanager.manager.set_log_path(path)`。当前实现会在导入时先创建默认 `logs/` 目录，之后新建队列时再使用最新的 `LOG_PATH`。

## 失败处理

队列通过任务返回码判断是否失败：

- 返回 `0`：任务成功
- 返回非 `0`：任务失败

失败时的行为：

### 串行模式（`max_workers=1`）

- `ignore_fail=False`：立即停止后续任务
- `ignore_fail=True`：记录失败并继续执行后续任务
- 如果提供了 `errorFunction`，每次失败时都会调用一次

### 并发模式（`max_workers>1`）

- `ignore_fail=True`：继续调度并执行剩余任务
- `ignore_fail=False`：发现失败后，不再提交尚未启动的新任务；已经开始运行的任务会继续执行到结束
- 如果提供了 `errorFunction`，每次失败时都会调用一次

`pythonTask/task3.py` 就是一个失败示例任务。

## 当前限制

- `PythonTask` 的“异步”仅用于异步读取单个子进程输出，不代表多个任务自动并发执行
- 并发模式基于线程池调度，任务本身应避免无保护地共享可变状态
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
