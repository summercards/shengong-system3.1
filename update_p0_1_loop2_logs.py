import json
import datetime
import os

log_entry = {
    "task_id": "P0-1-Loop-2",
    "phase": "P0-1",
    "loop": "Loop-2",
    "status": "APPROVED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P0-1_Loop-2_report.md"},
    "summary": "审查 world_setting.yaml，验证了故事大纲、题材标签、禁用元素及自动运行控制的完整性。符合 P0-1 验收标准。",
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

with open("tasks_list.md", "r", encoding="utf-8") as f:
    content = f.read()
    
content = content.replace("| P0-1 | 世界观配置生成 | COMPLETED | 待执行 | 待执行 |", "| P0-1 | 世界观配置生成 | COMPLETED | APPROVED | 待执行 |")
content = content.replace("## 当前执行任务： P1-2 / Loop-1", "## 当前执行任务： P0-1 / Loop-3")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
