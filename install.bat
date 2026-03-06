@echo off
echo ========================================
echo   正在安装神工系统 V3.1...
echo ========================================

:: 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+。
    exit /b 1
)

:: 2. 安装依赖
echo [1/4] 正在安装依赖库 (pyyaml, streamlit, pytest)...
pip install pyyaml streamlit pytest

:: 3. 创建目录结构
echo [2/4] 正在创建项目目录...
if not exist data\characters mkdir data\characters
if not exist config mkdir config
if not exist artifacts mkdir artifacts
if not exist tests mkdir tests

:: 4. 初始化数据库
if exist init_project.py (
    echo [3/4] 正在初始化 SQLite 数据库...
    python init_project.py
)

echo [4/4] 正在确认配置文件...
if not exist config\world_setting.yaml (
    (
    echo logline: "默认大纲"
    echo genre_rules: ["魔法", "科技"]
    echo forbidden_elements: ["穿越"]
    echo auto_run:
    echo   enabled: false
    echo   max_chapters_per_run: 3
    ) > config\world_setting.yaml
)

echo ========================================
echo   安装完成！
echo ========================================

