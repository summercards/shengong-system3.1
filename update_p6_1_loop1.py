import json
import datetime
import os

log_entry = {
    "task_id": "P6-1-Loop-1",
    "phase": "P6-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "script", "url": "install.sh"},
    "summary": "完善了项目安装脚本（提供 Bash 和 Bat 两个版本）。脚本涵盖了依赖安装、目录初始化、数据库构建及默认配置生成等完整步骤，实现了‘一键部署’。",
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
content = content.replace("| P6-1 | 安装脚本完善 | 待执行 | 待执行 | 待执行 |", "| P6-1 | 安装脚本完善 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P6-1 / Loop-1", "## 当前执行任务： P6-1 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
