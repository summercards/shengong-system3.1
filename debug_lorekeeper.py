# debug_lorekeeper.py - 调试 LoreKeeper
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 打印 database 模块中的函数
import database
print("database 模块中的函数:")
for name in dir(database):
    if not name.startswith('_'):
        print(f"  {name}")
