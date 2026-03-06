import streamlit as st
import yaml
import os

def main():
    st.set_page_config(page_title="神工系统 - 剧本编辑界面", layout="wide")
    st.title("📽️ 神工系统 - 剧本编辑中心")

    config_path = "config/world_setting.yaml"
    
    # 加载现有配置
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {"logline": "", "genre_rules": []}

    st.subheader("1. 核心大纲 (Logline)")
    new_logline = st.text_area("编辑故事一句话大纲", value=config.get("logline", ""), height=100)
    
    st.subheader("2. 题材规则 (Genre Rules)")
    genre_rules_str = st.text_area("每行输入一个规则", value="\n".join(config.get("genre_rules", [])), height=150)
    new_rules = [r.strip() for r in genre_rules_str.split("\n") if r.strip()]

    if st.button("保存配置"):
        config["logline"] = new_logline
        config["genre_rules"] = new_rules
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        st.success("配置已更新并同步至 world_setting.yaml")

    st.divider()
    st.subheader("3. 章节管理 (Chapter Outlines)")
    st.info("此处将对接 Planner Agent 生成的章节概括，用户可在此进行人工干预和精修。")
    st.text_area("第 1 章 大纲精修", value="Kael 在霓虹灯下遭遇追捕...", height=150)
    if st.button("锁定本章大纲并开始生成"):
        st.warning("正在调用 Writer Agent，请稍候...")

if __name__ == "__main__":
    # main() # 本地开发环境下取消注释即可运行: streamlit run interface.py
    print("Streamlit 界面代码已就绪。")

def character_monitor():
    st.divider()
    st.subheader("👥 角色状态监控中心")
    
    char_dir = "data/characters"
    if not os.path.exists(char_dir):
        st.error("角色目录不存在。")
        return

    char_files = [f for f in os.listdir(char_dir) if f.endswith(".yaml")]
    if not char_files:
        st.info("当前无角色数据。")
        return

    selected_char = st.selectbox("选择要监控的角色", char_files)
    char_path = os.path.join(char_dir, selected_char)

    with open(char_path, "r", encoding="utf-8") as f:
        char_data = yaml.safe_load(f)

    st.write(f"**角色名称**: {char_data.get('name', 'N/A')}")
    st.write(f"**原型**: {char_data.get('archetype', 'N/A')}")

    dynamic_state = char_data.get("dynamic_state", {})
    st.markdown("### 动态状态编辑器")
    
    new_state = {}
    for key, val in dynamic_state.items():
        if isinstance(val, int):
            new_state[key] = st.number_input(f"编辑 {key}", value=val)
        else:
            new_state[key] = st.text_input(f"编辑 {key}", value=str(val))

    if st.button(f"保存 {selected_char} 状态"):
        char_data["dynamic_state"] = new_state
        # 使用原子写入逻辑（此处简化，实际应复用 CharacterManager）
        with open(char_path, "w", encoding="utf-8") as f:
            yaml.dump(char_data, f, allow_unicode=True, sort_keys=False)
        st.success(f"{selected_char} 状态更新成功。")

# 修改 main 函数以包含 character_monitor
with open("interface.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "if __name__ == \"__main__\":" in line:
        new_lines.append("    character_monitor()\n\n")
    new_lines.append(line)

with open("interface.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

def generation_monitor():
    st.divider()
    st.subheader("📊 生成监控面板 (实时日志)")
    
    log_file = "artifacts/stage_logs.json"
    if not os.path.exists(log_file):
        st.info("尚无生成日志。")
        return

    with open(log_file, "r", encoding="utf-8") as f:
        logs = json.load(f)

    # 倒序显示最近 10 条日志
    recent_logs = logs[::-1][:10]
    
    st.markdown("### 最近活动日志")
    st.table(recent_logs)

    # 专门提取 Writer 和 Critic 的最新输出
    writer_logs = [l for l in logs if l["phase"] == "P1-2" and l["loop"] == "Loop-1"]
    critic_logs = [l for l in logs if l["phase"] == "P1-3" and l["loop"] == "Loop-1"]

    col1, col2 = st.columns(2)
    with col1:
        st.info("🖋️ 最新 Writer 输出摘要")
        if writer_logs:
            st.write(writer_logs[-1]["summary"])
        else:
            st.write("暂无记录")
            
    with col2:
        st.info("🔍 最新 Critic 反馈摘要")
        if critic_logs:
            st.write(critic_logs[-1]["summary"])
        else:
            st.write("暂无记录")

# 修改 main 函数以包含 generation_monitor
with open("interface.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("character_monitor()", "character_monitor()\n    generation_monitor()")

with open("interface.py", "w", encoding="utf-8") as f:
    f.write(content)
