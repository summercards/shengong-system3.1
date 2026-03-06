import json
import datetime
import os

log_entry = {
    "task_id": "P5-1-Loop-1",
    "phase": "P5-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "tests/test_core.py"},
    "summary": "编写并执行了针对核心管理模块的自动化测试脚本。成功验证了 CharacterManager 的原子写入逻辑、YAML/DB 同步功能，以及 EventManager 的事件落库与查询功能。",
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
content = content.replace("| P5-1 | 单元测试编写 | 待执行 | 待执行 | 待执行 |", "| P5-1 | 单元测试编写 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P5-1 / Loop-1", "## 当前执行任务： P5-1 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
