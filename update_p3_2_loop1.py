import json
import datetime
import os

log_entry = {
    "task_id": "P3-2-Loop-1",
    "phase": "P3-2",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "planner_agent.py"},
    "summary": "实现了 Planner Agent 核心逻辑。能够根据 Logline、前文摘要、节奏点 (Beat) 和未决伏笔 (Foreshadowing) 生成章节情节简述 (Synopsis) 和关键转折列表 (Key Turns)。",
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
content = content.replace("| P3-2 | Planner Agent 细分 | 待执行 | 待执行 | 待执行 |", "| P3-2 | Planner Agent 细分 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P3-2 / Loop-1", "## 当前执行任务： P3-2 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
