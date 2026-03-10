# Agent Context - 神工系统 V3.1 (GodCraft V4)

## 项目路径
- **工作目录**: `I:\项目\shengong-system\godcraft_v4`
- **参考文档目录**: `I:\项目\shengong-system`

## 必读文档
每次任务执行前必须交叉阅读：
1. **《神工系统 V3.1 — 工程化施工与交付指南-v3》** - 任务执行标准
2. **《神工系统-项目文档V3.1》** - 系统架构与设计规范

## 全局红线约束
1. **严禁直连大模型** - 必须通过 `openclaw_api.py` 调用 OpenClaw 平台接口
2. **SQLite 为唯一权威数据源** - YAML 仅作模板参考，数据库为唯一可信记录
3. **必须记录 audit_log 审计日志** - 每次关键操作写入审计日志
4. **统一通过 openclaw_api.py 进行 LLM 调用** - 禁止 Agent 直接调用外部 LLM
5. **结构化更新采用 trust_delta 机制** - delta > 3 且绝对值 >5 时标记 pending_review

## 任务清单 (M1-M5)
| Loop | 任务 |
|------|------|
| M1-1 | 初始化项目结构 (init_project.py) |
| M1-2 | 配置 world_setting.yaml |
| M2-1 | 数据库结构设计 |
| M2-2 | 结构化存取与 JSON Schema 验证 |
| M2-3 | LoreKeeper 读写 & YAML 原始同步 |
| M3-1 | Orchestrator / StoryCycle 核心实现 |
| M3-2 | Planner/Writer/Critic prompts 定义 |
| M4-1 | Job Controller (job_controller.py) |
| M4-2 | Scheduler Adapter 注册任务 |
| M5-1 | Streamlit UI / Minimal API |
| M5-2 | 导入、导出、监控 |

## 数据库结构
- SQLite: `data/godcraft.db`
- 表: novel_projects, writing_jobs, events_log, character_relationships, world_graph_edges, foreshadowing_ledger, audit_log

## 命名规范
- 任务命名: `GodCraft_Loop_[阶段]_[任务名]`
- 文件前缀: `godcraft_` 或按功能模块命名
