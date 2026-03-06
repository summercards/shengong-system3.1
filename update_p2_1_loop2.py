import json
import datetime
import os

log_entry = {
    "task_id": "P2-1-Loop-2",
    "phase": "P2-1",
    "loop": "Loop-2",
    "status": "APPROVED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P2-1_Loop-2_report.md"},
    "summary": "审查了 character_manager.py，确认原子写入逻辑和数据库/YAML同步逻辑符合指南要求。P2-1 审核通过。",
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

log_file = "artifacts/stage_logs.json"
logs = []
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        try: logs = json.load(f)
        except: pass
logs.append(log_entry)
with open(log_file, "w", encoding="utf-8") as f:
    json.dump(logs, f, indent=2, ensure_ascii=False)

with open("tasks_list.md", "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("| P2-1 | 角色状态读写 | COMPLETED | 待执行 | 待执行 |", "| P2-1 | 角色状态读写 | COMPLETED | APPROVED | 待执行 |")
content = content.replace("## 当前执行任务： P2-1 / Loop-2", "## 当前执行任务： P2-1 / Loop-3")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
