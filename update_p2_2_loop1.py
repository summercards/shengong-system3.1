import json
import datetime
import os

log_entry = {
    "task_id": "P2-2-Loop-1",
    "phase": "P2-2",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "event_manager.py"},
    "summary": "实现了 EventManager 类，封装了将重要事件摘要写入 SQLite events_log 表以及查询历史事件的功能。这为后续章节摘要和前文回忆提供了基础支持。",
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
content = content.replace("| P2-2 | 事件日志管理 | 待执行 | 待执行 | 待执行 |", "| P2-2 | 事件日志管理 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P2-2 / Loop-1", "## 当前执行任务： P2-2 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
