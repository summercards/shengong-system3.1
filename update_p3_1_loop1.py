import json
import datetime
import os

log_entry = {
    "task_id": "P3-1-Loop-1",
    "phase": "P3-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "config", "url": "config/beat_scheduler.json"},
    "summary": "定义了剧情节奏调度器（Beat Scheduler）的配置格式，支持固定章节、区间范围和循环周期（interval）三种节奏点触发模式。编写了基础逻辑类用于判定章节目标。",
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
content = content.replace("| P3-1 | Beat Scheduler 配置 | 待执行 | 待执行 | 待执行 |", "| P3-1 | Beat Scheduler 配置 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P3-1 / Loop-1", "## 当前执行任务： P3-1 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
