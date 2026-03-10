# yaml_utils.py - YAML 原子写入工具
"""
YAML 原子写入工具
提供安全的 YAML 读写操作，支持原子替换
"""

import os
import yaml
import tempfile
import shutil
from typing import Any, Optional


def load_yaml(file_path: str) -> Optional[Any]:
    """
    安全加载 YAML 文件
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML from {file_path}: {e}")
        return None


def save_yaml(data: Any, file_path: str) -> bool:
    """
    安全保存 YAML 文件（直接覆盖）
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving YAML to {file_path}: {e}")
        return False


def atomic_write_yaml(file_path: str, data: Any) -> bool:
    """
    原子写入 YAML 文件
    1. 写入临时文件 (tmp)
    2. 原子替换目标文件
    
    这样可以确保：
    - 写入失败不会影响原文件
    - 读取时不会得到部分写入的内容
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 创建临时文件
        fd, tmp_path = tempfile.mkstemp(suffix='.yaml', dir=dir_path or '.')
        os.close(fd)
        
        # 写入临时文件
        with open(tmp_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
        
        # 原子替换
        shutil.move(tmp_path, file_path)
        
        return True
    except Exception as e:
        print(f"Error in atomic write to {file_path}: {e}")
        # 清理临时文件
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        return False


def atomic_update_yaml(file_path: str, update_func) -> bool:
    """
    原子更新 YAML 文件（读取-修改-写入模式）
    
    Args:
        file_path: 目标文件路径
        update_func: 接收旧数据，返回新数据的函数
        
    Returns:
        是否成功
    """
    # 读取现有数据
    old_data = load_yaml(file_path) or {}
    
    # 计算新数据
    new_data = update_func(old_data)
    
    # 原子写入
    return atomic_write_yaml(file_path, new_data)


def merge_yaml(target_path: str, source_data: dict, overwrite: bool = False) -> bool:
    """
    合并 YAML 数据
    
    Args:
        target_path: 目标文件路径
        source_data: 要合并的数据
        overwrite: 是否覆盖现有值（False 则递归合并）
        
    Returns:
        是否成功
    """
    existing = load_yaml(target_path) or {}
    
    if overwrite:
        merged = source_data
    else:
        merged = _deep_merge(existing, source_data)
    
    return atomic_write_yaml(target_path, merged)


def _deep_merge(base: dict, update: dict) -> dict:
    """深度合并两个字典"""
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


# 导出
__all__ = [
    'load_yaml',
    'save_yaml',
    'atomic_write_yaml',
    'atomic_update_yaml',
    'merge_yaml'
]
