import json
import os

def create_release(tag, summary):
    print(f">> [Release] 正在创建发布版本: {tag}")
    
    # 1. 更新版本文件
    with open("VERSION", "w") as f:
        f.write(tag)
        
    # 2. 更新 CHANGELOG.md
    log_content = f"## [{tag}] - 2026-03-06\n- {summary}\n\n"
    if os.path.exists("CHANGELOG.md"):
        with open("CHANGELOG.md", "r") as f:
            old_content = f.read()
    else:
        old_content = ""
        
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(log_content + old_content)
        
    # 3. 模拟 Git 操作
    print(f"执行: git add .")
    print(f"执行: git commit -m 'Release {tag}: {summary}'")
    print(f"执行: git tag -a {tag} -m '{summary}'")
    print(f"执行: git push origin --tags")
    
    return True

if __name__ == "__main__":
    create_release("v3.1.0-final", "神工系统 V3.1 正式发布，核心管道、记忆系统及 UI 监控全部就绪。")
