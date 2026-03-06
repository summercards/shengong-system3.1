import json
import datetime
import os

log_entry = {
    "task_id": "P1-3-Loop-1",
    "phase": "P1-3",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "critic_agent.py"},
    "summary": "编写 Critic Agent 伪代码骨架，实现内容审查逻辑。能够根据 Genre Rules、OOC 规则、Forbidden Elements 等进行审查，并输出 JSON 反馈，限制单次处理 2000 token 预警。",
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
    
content = content.replace("| P1-3 | Critic Agent 实现 | 待执行 | 待执行 | 待执行 |", "| P1-3 | Critic Agent 实现 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P1-3 / Loop-1", "## 当前执行任务： P1-3 / Loop-2")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
