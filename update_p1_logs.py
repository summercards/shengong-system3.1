import json
import datetime
import os

log_entry = {
    "task_id": "P1-1-Loop-1",
    "phase": "P1-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "orchestrator.py"},
    "summary": "搭建 Orchestrator 核心骨架，包含 auto_run 配置解析、数据库查询、Writer/Critic Agent 调用接口及高风险阻断逻辑。",
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

log_file = "artifacts/stage_logs.json"

if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
else:
    logs = []

logs.append(log_entry)

with open(log_file, "w", encoding="utf-8") as f:
    json.dump(logs, f, indent=2, ensure_ascii=False)

# 更新 tasks_list.md
with open("tasks_list.md", "r", encoding="utf-8") as f:
    content = f.read()
    
content = content.replace("| P1-1 | Orchestrator 框架搭建 | 待执行 | 待执行 | 待执行 |", "| P1-1 | Orchestrator 框架搭建 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P0-1 / Loop-2", "## 当前执行任务： P1-1 / Loop-2")
content = content.replace("## 当前执行任务： P0-1 / Loop-1", "## 当前执行任务： P1-1 / Loop-2")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)

