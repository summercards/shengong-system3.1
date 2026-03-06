import json
import datetime
import os

log_entry = {
    "task_id": "P1-1-Loop-3",
    "phase": "P1-1",
    "loop": "Loop-3",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P1-1_Loop-3_acceptance.md"},
    "summary": "最终验收 P1-1 阶段，复核 Loop-2 的 APPROVED 状态，所有功能均符合 MVP 要求，将 P1-1 阶段标记为 DONE，即将开始 P1-2。",
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
    
content = content.replace("| P1-1 | Orchestrator 框架搭建 | COMPLETED | APPROVED | 待执行 |", "| P1-1 | Orchestrator 框架搭建 | COMPLETED | APPROVED | COMPLETED |")
content = content.replace("## 当前执行任务： P1-1 / Loop-3", "## 当前执行任务： P1-2 / Loop-1")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)

# 更新验收列表 artifacts/acceptance_list.json
acceptance_list_file = "artifacts/acceptance_list.json"
if os.path.exists(acceptance_list_file):
    with open(acceptance_list_file, "r", encoding="utf-8") as f:
        try:
            acc_list = json.load(f)
        except json.JSONDecodeError:
            acc_list = []
else:
    acc_list = []

acc_list.append({
    "phase": "P1-1",
    "status": "DONE",
    "last_completed_loop": "Loop-3",
    "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat()
})

with open(acceptance_list_file, "w", encoding="utf-8") as f:
    json.dump(acc_list, f, indent=2, ensure_ascii=False)
