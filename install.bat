@echo off
echo >> 开始安装神工系统 V3.1...

:: 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+。
    pause
    exit /b 1
)

:: 2. 安装依赖
echo >> 正在安装依赖库 (pyyaml, streamlit, pytest)...
pip install pyyaml streamlit pytest

:: 3. 创建目录结构
echo >> 正在创建项目目录...
if not exist data\characters mkdir data\characters
if not exist config mkdir config
if not exist artifacts mkdir artifacts
if not exist tests mkdir tests

:: 4. 初始化数据库
if exist init_project.py (
    echo >> 正在初始化 SQLite 数据库...
    python init_project.py
)

echo >> 安装完成！使用 "streamlit run interface.py" 启动界面。
pause
