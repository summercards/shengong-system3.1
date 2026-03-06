import json
import datetime
import os

log_entry = {
    "task_id": "P1-2-Loop-1",
    "phase": "P1-2",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "writer_agent.py"},
    "summary": "封装 Writer Agent 调用逻辑，设计生成章节的 Prompt 模板。通过分批注入上下文实现输入限制，单次 Prompt 长度受控（< 3000 token），返回格式化 JSON。",
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
    
content = content.replace("| P1-2 | Writer Agent 实现 | 待执行 | 待执行 | 待执行 |", "| P1-2 | Writer Agent 实现 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P1-2 / Loop-1", "## 当前执行任务： P1-2 / Loop-2")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
