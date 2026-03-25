# Milestones

## Milestone 1: Core Stability
目标：稳定当前串行 / 并发执行、日志系统与异常处理行为。

### Issues
- [ ] 增加 `PythonTask` stdout / stderr 转发测试
- [ ] 增加任务异常 traceback 写入测试
- [ ] 增加并发失败停止策略边界测试
- [ ] 修复同名 `TaskQueue` 重复创建时的 logger / handler 重复绑定问题
- [ ] 补充队列日志与任务输出日志边界测试
- [ ] 评估并明确 `import taskmanager` 自动创建日志目录的保留策略

## Milestone 2: Task Model
目标：让任务定义更适合真实自动化场景。

### Issues
- [ ] 为 `PythonTask` 增加 `cwd` 支持
- [ ] 为 `PythonTask` 增加 `env` 支持
- [ ] 为任务增加 `timeout` 能力
- [ ] 为任务增加 `retry` 能力
- [ ] 设计统一任务状态模型（success / failed / exception / skipped）
- [ ] 评估并设计任务上下文对象

## Milestone 3: Scheduling
目标：增强调度能力，同时保持当前 API 简洁。

### Issues
- [ ] 明确并发模式下失败后的停止与汇总语义
- [ ] 为队列运行结果增加成功 / 失败汇总
- [ ] 为任务和队列增加耗时统计
- [ ] 设计任务依赖能力的最小实现方案
- [ ] 评估任务分组 / 阶段执行是否需要纳入核心模型

## Milestone 4: DX & Docs
目标：提升开发体验和项目可维护性。

### Issues
- [ ] 为 `taskmanager/manager.py` 补充类型标注
- [ ] 为 `taskmanager/task.py` 补充类型标注
- [ ] 为 `taskmanager/asyncSubprocess.py` 补充类型标注
- [ ] 为 `taskmanager/logging_system.py` 补充类型标注
- [ ] 完善 README 中的串行、并发、失败处理示例
- [ ] 完善 README 中的日志结构说明与使用建议

## Milestone 5: CLI & Release
目标：提升项目可用性，并为发布做准备。

### Issues
- [ ] 设计简单 CLI 入口
- [ ] 支持通过配置文件加载任务定义
- [ ] 明确公共 API 与内部模块边界
- [ ] 建立 changelog / 版本策略
- [ ] 整理构建、验证与发布流程
