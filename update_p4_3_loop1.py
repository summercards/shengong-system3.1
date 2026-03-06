import json
import datetime
import os

log_entry = {
    "task_id": "P4-3-Loop-1",
    "phase": "P4-3",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "interface.py"},
    "summary": "在 interface.py 中实现了生成监控面板。支持从 stage_logs.json 实时加载最近的开发/生成日志，并专门开辟区域显示 Writer 和 Critic 的最新输出提要。",
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
content = content.replace("| P4-3 | 生成监控面板 | 待执行 | 待执行 | 待执行 |", "| P4-3 | 生成监控面板 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P4-3 / Loop-1", "## 当前执行任务： P4-3 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
