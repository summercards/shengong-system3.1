import json
import datetime
import os

log_entry = {
    "task_id": "P3-3-Loop-1",
    "phase": "P3-3",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "planner_agent.py"},
    "summary": "实现了伏笔引用逻辑。Planner Agent 现在能自动检测未决伏笔并在提示词中加入‘重要提醒’，引导模型在规划章节时主动考虑伏笔的回收（Resolving）。",
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
content = content.replace("| P3-3 | 伏笔引用 | 待执行 | 待执行 | 待执行 |", "| P3-3 | 伏笔引用 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P3-3 / Loop-1", "## 当前执行任务： P3-3 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
