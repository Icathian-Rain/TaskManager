# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言与沟通

- 本仓库中的文档与回复默认使用中文。

## 项目概览

这是一个轻量级 Python 任务队列库，用于顺序执行本地任务，并为每个任务保存独立日志。

核心能力：
- 在一个 `TaskQueue` 中串行执行多个任务
- 支持普通占位任务、Python 脚本任务、Python 函数任务
- 为每个任务写入单独日志文件，并维护队列级日志
- 任务失败时可选择立即停止或继续执行

## 常用命令

> 仓库当前没有 `pyproject.toml`、`requirements.txt`、测试框架配置或 lint/build 配置。以下命令基于当前仓库的实际可运行方式。

### 环境与运行

- 验证包可导入：
  - `python -c "import taskmanager; print('ok')"`
- 运行示例任务队列：
  - `python example.py`
- 运行单个示例脚本：
  - `python pythonTask/task1.py`
  - `python pythonTask/task2.py --args1 arg1 --args2 arg2`
  - `python pythonTask/task3.py`

### 测试

- 当前仓库未包含正式测试目录或测试配置。
- 若只是验证核心流程，直接运行：
  - `python example.py`
- 若只想验证某个模块可导入：
  - `python -c "from taskmanager import TaskQueue, PythonTask"`

## 高层架构

### 1. 包入口与初始化

- 包入口在 [taskmanager/__init__.py](taskmanager/__init__.py)
- 导入 `taskmanager` 时会：
  - 对外导出 `TaskQueue`、`Task`、`NormalTask`、`PythonTask`、`FunctionTask`
  - 立即调用 `init()` 创建默认 `logs/` 目录

这意味着任何仅仅 `import taskmanager` 的代码都会触发日志目录初始化，是当前包的重要副作用。

### 2. 队列执行模型

- 队列实现位于 [taskmanager/manager.py](taskmanager/manager.py)
- `TaskQueue` 维护一个按顺序执行的 `tasks` 列表
- `run()` 的执行流程：
  1. 遍历已添加的任务
  2. 为当前队列创建时间戳日志目录：`logs/<queue_name>_<timestamp>/`
  3. 为每个任务创建 `<task_name>.txt` 日志文件
  4. 调用任务对象本身（`task(file_handler)`）并读取返回码
  5. 根据返回码决定记录成功/失败，以及是否中断整个队列

关键行为：
- 队列是**严格串行**执行，不做并发调度
- 失败判定基于任务返回码是否为 `0`
- `ignore_fail=False` 时，任一失败任务都会终止后续任务
- `errorFunction` 是失败钩子，在任务失败时调用

### 3. 任务抽象层

- 任务类型定义在 [taskmanager/task.py](taskmanager/task.py)
- `Task` 是最小基类，约定 `__call__()` 返回整数状态码
- 现有三种任务实现：
  - `NormalTask`：示例/占位任务，打印文本并 `sleep`
  - `FunctionTask`：同步调用传入的 Python 函数，可传参数
  - `PythonTask`：启动外部 Python 子进程执行脚本

理解这个仓库时，最重要的约定是：
- **任务不是通过统一的 `run()` 接口，而是通过 `__call__()` 执行**
- `TaskQueue` 不关心具体任务类型，只依赖“可调用 + 返回码”这一协议

### 4. PythonTask 与异步子进程

- 子进程封装位于 [taskmanager/asyncSubprocess.py](taskmanager/asyncSubprocess.py)
- `PythonTask` 内部通过 `AsyncSubprocess` 启动命令：
  - 基础命令固定为 `['python', <python_entry>]`
  - 追加可选参数列表 `args`
- `AsyncSubprocess.run()` 使用 `asyncio.create_subprocess_exec()` 并发读取 `stdout` / `stderr`
- `PythonTask.__call__()` 再通过 `asyncio.run(...)` 在同步上下文中执行该异步流程

因此整体模型是：
- `TaskQueue` 是同步串行队列
- `PythonTask` 的“异步”仅用于**实时读取子进程输出流**，不是为了并行执行多个任务

### 5. 日志结构

默认日志根目录由 [taskmanager/manager.py](taskmanager/manager.py) 中的全局变量 `LOG_PATH` 控制，可通过 `set_log_path(path)` 修改。

日志落盘结构：
- 队列目录：`logs/<queue_name>_<timestamp>/`
- 队列总日志：`log.txt`
- 单任务日志：`<task_name>.txt`

如果需要排查执行问题，优先看对应队列目录下的这些文件。

## 代码阅读优先级

初次进入仓库时，建议按这个顺序理解：
1. [example.py](example.py)：看库的预期使用方式
2. [taskmanager/manager.py](taskmanager/manager.py)：看队列如何调度任务与处理失败
3. [taskmanager/task.py](taskmanager/task.py)：看任务抽象和具体任务类型
4. [taskmanager/asyncSubprocess.py](taskmanager/asyncSubprocess.py)：看 `PythonTask` 如何转发子进程输出

## 当前仓库状态说明

- 没有发现现成的 `CLAUDE.md`
- 没有发现 Cursor rules、Copilot instructions
- README 信息非常少，实际可运行方式主要以 [example.py](example.py) 和包源码为准
- 当前仓库未配置正式 build/lint/test 工作流；若未来补充这些配置，需要同步更新此文件
