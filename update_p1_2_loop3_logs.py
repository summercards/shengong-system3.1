import json
import datetime
import os

log_entry = {
    "task_id": "P1-2-Loop-3",
    "phase": "P1-2",
    "loop": "Loop-3",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P1-2_Loop-3_acceptance.md"},
    "summary": "最终验收 P1-2 阶段，确认 Writer Agent 完成封装并成功处理 prompt 及 json 返回限制。阶段完成，标记为 DONE。",
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

# 更新 tasks_list.md
with open("tasks_list.md", "r", encoding="utf-8") as f:
    content = f.read()
    
content = content.replace("| P1-2 | Writer Agent 实现 | COMPLETED | APPROVED | 待执行 |", "| P1-2 | Writer Agent 实现 | COMPLETED | APPROVED | COMPLETED |")
content = content.replace("## 当前执行任务： P1-2 / Loop-3", "## 当前执行任务： P1-3 / Loop-1")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)

# 更新验收列表
acceptance_list_file = "artifacts/acceptance_list.json"
acc_list = []
if os.path.exists(acceptance_list_file):
    with open(acceptance_list_file, "r", encoding="utf-8") as f:
        try: acc_list = json.load(f)
        except: pass

acc_list.append({
    "phase": "P1-2",
    "status": "DONE",
    "last_completed_loop": "Loop-3",
    "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat()
})

with open(acceptance_list_file, "w", encoding="utf-8") as f:
    json.dump(acc_list, f, indent=2, ensure_ascii=False)
