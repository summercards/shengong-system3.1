import json
import datetime
import os

log_entry = {
    "task_id": "P2-4-Loop-1",
    "phase": "P2-4",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "foreshadowing_manager.py"},
    "summary": "实现了 ForeshadowingManager 类，封装了 `foreshadowing_ledger` 表的记录与查询功能。支持伏笔的录入、状态回收（PENDING/RESOLVED）及未决线索的批量查询，为 Planner 调度剧情提供数据依据。",
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
content = content.replace("| P2-4 | 伏笔跟踪表 | 待执行 | 待执行 | 待执行 |", "| P2-4 | 伏笔跟踪表 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P2-4 / Loop-1", "## 当前执行任务： P2-4 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
