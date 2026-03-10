# Fix database schema
import sys
import os
os.chdir('I:/项目/shengong-system/godcraft_v4')
sys.path.insert(0, '.')

from database import execute_write

# Add columns to writing_jobs table
try:
    execute_write("ALTER TABLE writing_jobs ADD COLUMN content TEXT DEFAULT ''")
    print('Added content column')
except Exception as e:
    print(f'content: {e}')

try:
    execute_write("ALTER TABLE writing_jobs ADD COLUMN word_count INTEGER DEFAULT 0")
    print('Added word_count column')
except Exception as e:
    print(f'word_count: {e}')

# Also add columns to novel_projects
try:
    execute_write("ALTER TABLE novel_projects ADD COLUMN current_chapter INTEGER DEFAULT 0")
    print('Added current_chapter column')
except Exception as e:
    print(f'current_chapter: {e}')
