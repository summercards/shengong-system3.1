#!/bin/bash
set -e
echo "========================================"
echo "  正在安装神工系统 V3.1..."
echo "========================================"

# 1. 检查 Python
if ! command -v python &> /dev/null
then
    echo "[错误] 未找到 Python，请先安装 Python 3.10+。"
    exit 1
fi

# 2. 安装依赖
echo "[1/4] 正在安装依赖库 (pyyaml, streamlit, pytest)..."
pip install pyyaml streamlit pytest

# 3. 创建目录结构
echo "[2/4] 正在创建项目目录..."
mkdir -p data/characters config artifacts tests

# 4. 初始化数据库
if [ -f "init_project.py" ]; then
    echo "[3/4] 正在初始化 SQLite 数据库..."
    python init_project.py
else
    echo "[警告] 未找到 init_project.py，跳过数据库初始化。"
fi

# 5. 生成默认配置
echo "[4/4] 正在确认配置文件..."
if [ ! -f "config/world_setting.yaml" ]; then
    cat << 'EOC' > config/world_setting.yaml
logline: "默认大纲"
genre_rules: ["魔法", "科技"]
forbidden_elements: ["穿越"]
auto_run:
  enabled: false
  max_chapters_per_run: 3
EOC
fi

echo "========================================"
echo "  安装完成！"
echo "========================================"

