# Issue Backlog

## P0
- [ ] 修复同名 `TaskQueue` 重复创建时的 logger / handler 重复绑定问题
- [ ] 增加 `PythonTask` stdout / stderr 转发测试
- [ ] 增加任务异常 traceback 写入测试
- [ ] 增加并发失败停止策略边界测试
- [ ] 明确 `import taskmanager` 自动创建日志目录的行为是否保留

## P1
- [ ] 为任务增加 `timeout` 能力
- [ ] 为任务增加 `retry` 能力
- [ ] 为 `PythonTask` 增加 `cwd` 支持
- [ ] 为 `PythonTask` 增加 `env` 支持
- [ ] 为队列运行结果增加成功 / 失败汇总
- [ ] 为任务和队列增加耗时统计
- [ ] 设计统一任务状态模型

## P2
- [ ] 为 `taskmanager/manager.py` 补充类型标注
- [ ] 为 `taskmanager/task.py` 补充类型标注
- [ ] 为 `taskmanager/asyncSubprocess.py` 补充类型标注
- [ ] 为 `taskmanager/logging_system.py` 补充类型标注
- [ ] 完善 README 中的串行、并发、失败处理示例
- [ ] 完善 README 中的日志结构说明与使用建议

## P3
- [ ] 设计任务上下文对象
- [ ] 设计任务依赖能力的最小实现方案
- [ ] 评估任务分组 / 阶段执行能力
- [ ] 设计简单 CLI 入口
- [ ] 评估 YAML / JSON 配置文件驱动能力
- [ ] 建立 changelog / 版本策略
- [ ] 整理构建、验证与发布流程
