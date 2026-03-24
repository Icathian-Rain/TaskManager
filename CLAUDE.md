# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言与沟通

- 本仓库中的文档与回复默认使用中文。

## 项目概览

这是一个轻量级 Python 任务队列库，用于运行本地任务、Python 脚本和 Python 函数，并为队列和单个任务分别保存日志。

当前核心能力：
- 在一个 `TaskQueue` 中按添加顺序串行执行任务
- 通过 `max_workers` 支持并发执行多个任务
- 支持 `NormalTask`、`FunctionTask`、`PythonTask`
- 为每次队列运行创建独立日志目录，并为每个任务写单独日志文件
- 根据任务返回码判断成功/失败
- 支持失败后停止或继续执行
- 支持通过 `use_rich_progress` 在标准 `tqdm` 与 rich 进度条之间切换

## 常用命令

本仓库当前使用 `uv` 管理环境、运行命令与构建。

### 安装依赖

- 同步依赖：
  - `uv sync`

### 运行与开发验证

- 验证包可导入：
  - `uv run python -c "import taskmanager; print('ok')"`
- 运行示例队列：
  - `uv run python example.py`
- 运行单个示例脚本：
  - `uv run python pythonTask/task1.py`
  - `uv run python pythonTask/task2.py --args1 arg1 --args2 arg2`
  - `uv run python pythonTask/task3.py`

### 测试

- 运行全部测试：
  - `uv run python -m unittest discover -s tests`
- 运行单个测试文件：
  - `uv run python -m unittest tests.test_smoke`
- 运行单个测试用例：
  - `uv run python -m unittest tests.test_smoke.TaskQueueSmokeTests.test_tasks_run_in_order`

### 构建

- 构建分发包：
  - `uv build`

### Lint / 格式化

- 当前仓库未配置独立的 lint / formatter 工具或对应命令。

## 高层架构

### 1. 包入口与导入副作用

- 包入口在 [taskmanager/__init__.py](taskmanager/__init__.py)
- 对外导出 `TaskQueue`、`Task`、`NormalTask`、`PythonTask`、`FunctionTask`
- 导入 `taskmanager` 时会立即调用 `init()` 创建默认 `logs/` 目录

这意味着任何仅仅 `import taskmanager` 的代码都会触发日志目录初始化，这是当前包的重要副作用。

### 2. 队列执行模型：串行与并发共存

- 队列实现位于 [taskmanager/manager.py](taskmanager/manager.py)
- `TaskQueue` 统一维护任务列表，但根据 `max_workers` 选择两套执行路径：
  - `max_workers == 1`：走 `_run_serial()`，严格按添加顺序执行
  - `max_workers > 1`：走 `_run_parallel()`，使用 `ThreadPoolExecutor` 并发调度

并发模型的关键点：
- 队列级并发是通过线程池完成的，不是通过 `asyncio` 调度多个任务
- 初始会先提交最多 `max_workers` 个任务，之后每当有任务完成，再补提交新任务
- `ignore_fail=False` 时，一旦发现失败任务，会停止提交尚未启动的新任务；已经开始运行的任务会继续执行到结束
- `ignore_fail=True` 时，即使某个任务失败，也会继续调度剩余任务

另外，`TaskQueue.run()` 在真正执行前会校验所有 `task.name` 必须唯一，因为每个任务都会映射到独立日志文件 `<task_name>.txt`。

### 3. 任务抽象协议：靠 `__call__()` 与返回码协作

- 任务定义在 [taskmanager/task.py](taskmanager/task.py)
- `TaskQueue` 不依赖某个统一的 `run()` 方法，而是直接调用任务对象本身：`task(file_handler)`
- 因此这个仓库最核心的协议是：
  - 任务对象实现 `__call__(file_handler=None)`
  - 返回整数状态码
  - `0` 表示成功，非 `0` 表示失败

现有任务类型：
- `NormalTask`：示例/占位任务，输出文本并 `sleep`
- `FunctionTask`：同步调用 Python 函数，函数返回值直接作为任务返回码
- `PythonTask`：运行外部 Python 脚本并将输出写入日志

理解这一层后，就能明白扩展新任务类型时应复用什么接口，而不是去寻找额外的抽象基类或调度注册机制。

### 4. `PythonTask` 的异步边界

- 子进程封装位于 [taskmanager/asyncSubprocess.py](taskmanager/asyncSubprocess.py)
- `PythonTask` 内部固定以 `['python', <script>, ...args]` 构造命令
- `AsyncSubprocess.run()` 使用 `asyncio.create_subprocess_exec()` 启动子进程，并并发读取 `stdout` / `stderr`
- `PythonTask.__call__()` 再通过 `asyncio.run(...)` 在同步上下文中执行该异步流程

这里要特别注意：
- `PythonTask` 的“异步”只用于单个子进程输出流的实时转发
- 多个任务是否并行，取决于 `TaskQueue.max_workers`，而不是 `PythonTask` 自身
- 因为命令前缀固定为 `python`，运行环境里必须能直接调用 `python`

### 5. 日志与进度条是队列层的职责

- 日志根目录由 [taskmanager/manager.py](taskmanager/manager.py) 中的全局变量 `LOG_PATH` 控制
- 可通过 `set_log_path(path)` 修改后续新建队列使用的日志根目录
- 每个 `TaskQueue` 在初始化时就会创建自己的运行目录：`logs/<queue_name>_<timestamp>/`
- 目录下通常包含：
  - `log.txt`：队列级日志
  - `<task_name>.txt`：单任务输出日志

控制台日志与进度条之间通过 `TqdmLoggingHandler` 适配：
- 标准模式使用 `tqdm.write`
- rich 模式切换到 `tqdm.rich.tqdm`
- 这样日志输出不会直接打断进度条显示

### 6. 失败处理分两层：任务结果收集 + 队列策略

- 单个任务的执行、异常捕获与任务日志写入在 `_run_task()` 中完成
- 失败判定与失败回调在 `_handle_task_result()` 中完成
- `errorFunction` 是一个非常轻量的失败钩子：每次任务失败都会调用一次，不区分串行或并发模式

因此定位失败行为时，优先看：
1. 任务自己的返回码或异常
2. `_handle_task_result()` 如何解释该结果
3. 当前是否启用了 `ignore_fail`
4. 当前队列是串行还是并发模式

## 测试结构

- 测试集中在 [tests/test_smoke.py](tests/test_smoke.py)
- 这些测试更像 smoke / 行为测试，而不是细粒度单元测试
- 当前覆盖重点是：
  - 串行执行顺序
  - 失败后停止 / 继续执行
  - `use_rich_progress` 与默认进度条选择
  - `max_workers` 参数校验
  - 重名任务校验
  - 并发执行与失败后停止继续提交的行为
  - 并发模式下日志文件是否生成

如果修改 `TaskQueue` 调度逻辑、失败处理、日志目录规则或进度条选择逻辑，应先更新并运行这些测试。

## 代码阅读优先级

初次进入仓库时，建议按这个顺序理解：
1. [README.md](README.md)：看对外能力、运行方式与当前公开用法
2. [example.py](example.py)：看最直接的使用示例，尤其是 `max_workers` 与 `use_rich_progress`
3. [taskmanager/manager.py](taskmanager/manager.py)：看队列调度、日志、失败处理和并发实现
4. [taskmanager/task.py](taskmanager/task.py)：看任务协议和三种任务类型
5. [taskmanager/asyncSubprocess.py](taskmanager/asyncSubprocess.py)：看 `PythonTask` 如何转发子进程输出
6. [tests/test_smoke.py](tests/test_smoke.py)：看当前仓库实际保证了哪些行为

## 仓库规则文件情况

- 未发现 Cursor rules（`.cursor/rules/` 或 `.cursorrules`）
- 未发现 Copilot instructions（`.github/copilot-instructions.md`）
