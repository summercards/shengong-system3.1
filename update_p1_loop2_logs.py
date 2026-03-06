import json
import datetime
import os

log_entry = {
    "task_id": "P1-1-Loop-2",
    "phase": "P1-1",
    "loop": "Loop-2",
    "status": "APPROVED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P1-1_Loop-2_report.md"},
    "summary": "审查 orchestrator.py，验证通过了 yaml 读取、自动运行控制逻辑以及各项 Agent 的调用骨架。符合 P1-1 最小功能验收标准。",
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
    
content = content.replace("| P1-1 | Orchestrator 框架搭建 | COMPLETED | 待执行 | 待执行 |", "| P1-1 | Orchestrator 框架搭建 | COMPLETED | APPROVED | 待执行 |")
content = content.replace("## 当前执行任务： P1-1 / Loop-2", "## 当前执行任务： P1-1 / Loop-3")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
