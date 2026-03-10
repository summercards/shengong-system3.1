# app.py - M5-1 Streamlit UI
"""
Streamlit Web UI for GodCraft
提供可视化的项目管理、章节写作、任务监控界面

功能：
1. 项目管理 - 创建、查看、编辑项目
2. 章节写作 - 触发 Story Cycle
3. 任务监控 - 查看写作任务状态
4. 输出展示 - 查看已生成的章节
"""

import os
import sys
import json
import yaml
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

import streamlit as st
import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入项目模块
from database import (
    get_connection, execute_query, execute_write,
    create_project as db_create_project,
    get_project as db_get_project,
    get_all_projects,
    create_job as db_create_job,
    get_job as db_get_job,
    get_project_jobs,
    update_job_status,
    log_event as db_log_event
)
from orchestrator import Orchestrator, run_story_cycle
from job_controller import JobController, JobStatus
from structured_store import StructuredStore


# === 页面配置 ===
st.set_page_config(
    page_title="神工系统 - GodCraft",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# === 样式 ===
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4ECDC4;
        margin-top: 1rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #D4EDDA;
        border-radius: 0.5rem;
        border-left: 4px solid #28A745;
    }
    .warning-box {
        padding: 1rem;
        background-color: #FFF3CD;
        border-radius: 0.5rem;
        border-left: 4px solid #FFC107;
    }
    .error-box {
        padding: 1rem;
        background-color: #F8D7DA;
        border-radius: 0.5rem;
        border-left: 4px solid #DC3545;
    }
    .info-box {
        padding: 1rem;
        background-color: #D1ECF1;
        border-radius: 0.5rem;
        border-left: 4px solid #17A2B8;
    }
</style>
""", unsafe_allow_html=True)


# === 工具函数 ===

def get_db_path() -> str:
    """获取数据库路径"""
    return os.path.join(PROJECT_ROOT, "data", "godcraft.db")


def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(PROJECT_ROOT, "config", "world_setting.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def load_world_setting() -> dict:
    """加载世界设置"""
    return load_config()


def get_output_dir() -> str:
    """获取输出目录"""
    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def load_chapters(project_id: str) -> List[Dict]:
    """加载项目的章节列表"""
    output_dir = get_output_dir()
    chapters = []
    
    for f in os.listdir(output_dir):
        if f.startswith(f"chapter_") and f.endswith(".md"):
            chapter_num = f.replace("chapter_", "").replace(".md", "")
            meta_path = os.path.join(output_dir, f"chapter_{chapter_num}_meta.json")
            
            chapter_data = {
                "number": chapter_num,
                "file": f,
                "exists": True
            }
            
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as mf:
                    chapter_data["meta"] = json.load(mf)
            
            chapters.append(chapter_data)
    
    return sorted(chapters, key=lambda x: x["number"], reverse=True)


def render_chapter_content(chapter_file: str) -> str:
    """渲染章节内容"""
    path = os.path.join(get_output_dir(), chapter_file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


# === 侧边栏 ===

def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("📖 神工系统")
    st.sidebar.markdown("---")
    
    # 导航
    page = st.sidebar.radio(
        "导航",
        ["🏠 首页", "📚 项目管理", "✍️ 章节写作", "📊 任务监控", "📄 输出查看", "⚙️ 设置"]
    )
    
    st.sidebar.markdown("---")
    
    # 快速状态
    st.sidebar.subheader("快速状态")
    
    # 获取项目数
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM novel_projects")
    project_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM writing_jobs WHERE status = 'pending'")
    pending_jobs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM writing_jobs WHERE status = 'running'")
    running_jobs = cursor.fetchone()[0]
    conn.close()
    
    st.sidebar.info(f"📁 项目数: {project_count}")
    st.sidebar.info(f"⏳ 待处理: {pending_jobs}")
    st.sidebar.info(f"🔄 进行中: {running_jobs}")
    
    return page


# === 页面 ===

def render_home():
    """首页"""
    st.markdown('<p class="main-header">🌀 神工系统 - GodCraft</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📁 项目数", "0")
    
    with col2:
        st.metric("📝 章节数", "0")
    
    with col3:
        st.metric("⏳ 待处理", "0")
    
    st.markdown("---")
    
    # 欢迎信息
    st.markdown("""
    <div class="info-box">
        <h3>🎉 欢迎使用神工系统</h3>
        <p>AI 驱动的自动化小说创作系统</p>
        <ul>
            <li>📚 项目管理 - 创建和管理你的小说项目</li>
            <li>✍️ 章节写作 - AI 自动生成章节内容</li>
            <li>📊 任务监控 - 跟踪写作进度</li>
            <li>📄 输出查看 - 浏览已生成的章节</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 快速开始
    st.subheader("🚀 快速开始")
    
    if st.button("创建新项目"):
        st.session_state["page"] = "📚 项目管理"
        st.rerun()


def render_project_management():
    """项目管理页面"""
    st.markdown('<p class="sub-header">📚 项目管理</p>', unsafe_allow_html=True)
    
    # 创建新项目
    st.subheader("创建新项目")
    
    with st.form("create_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_id = st.text_input("项目 ID", value=f"project_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            title = st.text_input("小说标题", placeholder="例如：星辰大海")
        
        with col2:
            genre = st.selectbox("类型", ["奇幻", "科幻", "都市", "历史", "仙侠", "其他"])
            target_chapters = st.number_input("目标章节数", min_value=1, value=50)
        
        logline = st.text_area("一句话简介", placeholder="用一句话描述你的小说...")
        interval = st.number_input("写作间隔（分钟）", min_value=1, value=60)
        
        submit = st.form_submit_button("创建项目")
        
        if submit and project_id and title:
            try:
                db_create_project(
                    project_id=project_id,
                    title=title,
                    genre=genre,
                    logline=logline,
                    target_chapters=target_chapters,
                    interval_minutes=interval
                )
                db_log_event(project_id, 0, "project_created", "Project created via UI")
                st.success(f"✅ 项目 '{title}' 创建成功！")
            except Exception as e:
                st.error(f"❌ 创建失败: {str(e)}")
    
    st.markdown("---")
    
    # 项目列表
    st.subheader("项目列表")
    
    try:
        projects = get_all_projects()
        
        if projects:
            # 转换为 DataFrame 显示
            df = pd.DataFrame(projects)
            df = df[['project_id', 'title', 'genre', 'status', 'current_chapter', 'target_chapters', 'created_at']]
            df.columns = ['ID', '标题', '类型', '状态', '当前章节', '目标章节', '创建时间']
            
            st.dataframe(df, use_container_width=True)
            
            # 项目详情
            st.subheader("项目详情")
            
            selected_id = st.selectbox("选择项目", [p['project_id'] for p in projects])
            
            if selected_id:
                project = db_get_project(selected_id)
                
                if project:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("标题", project.get('title', ''))
                    with col2:
                        st.metric("类型", project.get('genre', ''))
                    with col3:
                        st.metric("状态", project.get('status', ''))
                    with col4:
                        st.metric("章节", f"{project.get('current_chapter', 0)}/{project.get('target_chapters', 0)}")
                    
                    st.markdown(f"**简介:** {project.get('logline', '无')}")
        else:
            st.info("暂无项目，请创建新项目")
            
    except Exception as e:
        st.error(f"加载项目失败: {str(e)}")


def render_chapter_writing():
    """章节写作页面"""
    st.markdown('<p class="sub-header">✍️ 章节写作</p>', unsafe_allow_html=True)
    
    # 选择项目
    try:
        projects = get_all_projects()
        
        if not projects:
            st.warning("请先创建项目")
            return
        
        project_id = st.selectbox(
            "选择项目",
            [p['project_id'] for p in projects],
            format_func=lambda x: f"{x} - {next((p['title'] for p in projects if p['project_id'] == x), x)}"
        )
        
        if not project_id:
            return
            
        project = db_get_project(project_id)
        
        if not project:
            st.error("项目不存在")
            return
        
        st.info(f"当前项目: {project.get('title', '')} | 章节: {project.get('current_chapter', 0)}/{project.get('target_chapters', 0)}")
        
        st.markdown("---")
        
        # 写作选项
        st.subheader("写作选项")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chapter_num = st.number_input(
                "写作章节号",
                min_value=1,
                value=project.get('current_chapter', 0) + 1,
                step=1
            )
        
        with col2:
            writing_mode = st.radio(
                "写作模式",
                ["完整流程 (规划→写作→审查)", "仅写作", "仅规划"]
            )
        
        # 写作参数
        with st.expander("高级选项"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                target_length = st.slider("目标字数", 500, 5000, 1200)
            
            with col_b:
                review_enabled = st.checkbox("启用审查", value=True)
        
        # 触发写作
        st.markdown("---")
        
        if st.button("🚀 开始写作", type="primary", use_container_width=True):
            with st.spinner("写作中，请稍候..."):
                try:
                    # 创建写作任务
                    job_id = db_create_job(
                        project_id=project_id,
                        job_type="chapter_write",
                        chapter_number=chapter_num,
                        status="pending",
                        schedule_strategy="immediate"
                    )
                    
                    db_log_event(project_id, chapter_num, "chapter_write_started", f"Chapter {chapter_num} write started")
                    
                    # 初始化 Orchestrator 并运行
                    orchestrator = Orchestrator(project_id=project_id)
                    
                    # 运行故事循环
                    result = orchestrator.story_cycle(
                        chapter_number=chapter_num,
                        target_length=target_length,
                        enable_review=review_enabled
                    )
                    
                    # 更新任务状态
                    if result.get("success"):
                        update_job_status(job_id, "completed")
                        st.success(f"✅ 第 {chapter_num} 章写作完成！")
                        
                        # 显示结果
                        with st.expander("查看生成内容", expanded=True):
                            content = result.get("content", "")
                            st.text_area("章节内容", value=content[:2000] + "..." if len(content) > 2000 else content, height=300)
                    else:
                        update_job_status(job_id, "failed")
                        st.error(f"❌ 写作失败: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ 执行失败: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def render_task_monitoring():
    """任务监控页面"""
    st.markdown('<p class="sub-header">📊 任务监控</p>', unsafe_allow_html=True)
    
    # 刷新按钮
    if st.button("🔄 刷新"):
        st.rerun()
    
    try:
        # 获取任务统计
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # 任务统计
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM writing_jobs 
            GROUP BY status
        """)
        stats = cursor.fetchall()
        
        st.subheader("任务统计")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        stat_dict = {s[0]: s[1] for s in stats}
        
        with col1:
            st.metric("待处理", stat_dict.get('pending', 0))
        with col2:
            st.metric("进行中", stat_dict.get('running', 0))
        with col3:
            st.metric("已完成", stat_dict.get('completed', 0))
        with col4:
            st.metric("失败", stat_dict.get('failed', 0))
        with col5:
            st.metric("总计", sum(stat_dict.values()))
        
        st.markdown("---")
        
        # 任务列表
        st.subheader("任务列表")
        
        # 筛选
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            status_filter = st.selectbox(
                "状态筛选",
                ["全部", "pending", "running", "completed", "failed", "cancelled"]
            )
        
        with col_f2:
            project_filter = st.text_input("项目筛选", "")
        
        # 查询任务
        query = "SELECT * FROM writing_jobs"
        conditions = []
        params = []
        
        if status_filter != "全部":
            conditions.append("status = ?")
            params.append(status_filter)
        
        if project_filter:
            conditions.append("project_id LIKE ?")
            params.append(f"%{project_filter}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        conn.close()
        
        if jobs:
            # 转换为 DataFrame
            df = pd.DataFrame([dict(row) for row in jobs])
            df = df[['job_id', 'project_id', 'job_type', 'chapter_number', 'status', 'schedule_strategy', 'created_at', 'completed_at']]
            df.columns = ['ID', '项目', '类型', '章节', '状态', '调度', '创建时间', '完成时间']
            
            st.dataframe(df, use_container_width=True)
            
            # 任务详情
            if len(jobs) > 0:
                selected_job_id = st.selectbox(
                    "查看任务详情",
                    [row['job_id'] for row in jobs]
                )
                
                job = db_get_job(selected_job_id)
                
                if job:
                    st.json(job)
        else:
            st.info("暂无任务记录")
            
    except Exception as e:
        st.error(f"加载失败: {str(e)}")


def render_output_view():
    """输出查看页面"""
    st.markdown('<p class="sub-header">📄 输出查看</p>', unsafe_allow_html=True)
    
    # 选择项目
    try:
        projects = get_all_projects()
        
        if not projects:
            st.warning("暂无项目")
            return
        
        project_id = st.selectbox(
            "选择项目",
            [p['project_id'] for p in projects],
            key="output_project"
        )
        
        # 加载章节
        chapters = load_chapters(project_id)
        
        if chapters:
            st.subheader(f"章节列表 ({len(chapters)} 章)")
            
            # 章节选择
            chapter_options = [f"第 {c['number']} 章" for c in chapters]
            selected = st.selectbox("选择章节", chapter_options)
            
            # 查找选中的章节
            selected_num = selected.replace("第", "").replace("章", "").strip()
            chapter = next((c for c in chapters if c["number"] == selected_num), None)
            
            if chapter:
                # 显示元数据
                if "meta" in chapter:
                    with st.expander("章节元数据"):
                        st.json(chapter["meta"])
                
                # 显示内容
                content = render_chapter_content(chapter["file"])
                
                if content:
                    st.text_area("章节内容", value=content, height=500)
                else:
                    st.warning("章节内容为空")
        else:
            st.info("暂无生成的章节")
            
    except Exception as e:
        st.error(f"加载失败: {str(e)}")


def render_settings():
    """设置页面"""
    st.markdown('<p class="sub-header">⚙️ 设置</p>', unsafe_allow_html=True)
    
    # 世界设置
    st.subheader("世界设置")
    
    config = load_world_setting()
    
    with st.form("settings_form"):
        world_name = st.text_input("世界名称", value=config.get("world", {}).get("name", ""))
        world_desc = st.text_area("世界描述", value=config.get("world", {}).get("description", ""))
        
        submit = st.form_submit_button("保存设置")
        
        if submit:
            # 更新配置
            config["world"] = {
                "name": world_name,
                "description": world_desc
            }
            
            config_path = os.path.join(PROJECT_ROOT, "config", "world_setting.yaml")
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            
            st.success("✅ 设置已保存")
    
    st.markdown("---")
    
    # 数据库信息
    st.subheader("数据库信息")
    
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # 表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        st.write("数据表:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            st.write(f"- {table_name}: {count} 条记录")
        
        conn.close()
        
    except Exception as e:
        st.error(f"数据库错误: {str(e)}")
    
    st.markdown("---")
    
    # 开发工具
    st.subheader("开发工具")
    
    if st.button("运行测试"):
        st.info("运行测试功能开发中...")


# === 主函数 ===

def main():
    """主函数"""
    # 初始化 session state
    if "page" not in st.session_state:
        st.session_state["page"] = "🏠 首页"
    
    # 获取页面
    page = render_sidebar()
    
    # 路由
    if page == "🏠 首页":
        render_home()
    elif page == "📚 项目管理":
        render_project_management()
    elif page == "✍️ 章节写作":
        render_chapter_writing()
    elif page == "📊 任务监控":
        render_task_monitoring()
    elif page == "📄 输出查看":
        render_output_view()
    elif page == "⚙️ 设置":
        render_settings()


if __name__ == "__main__":
    main()
