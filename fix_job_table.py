from database import get_connection
conn = get_connection()
# 添加缺失字段
conn.execute('ALTER TABLE writing_jobs ADD COLUMN schedule_strategy TEXT DEFAULT "manual"')
conn.execute('ALTER TABLE writing_jobs ADD COLUMN scheduled_time TIMESTAMP')
conn.execute('ALTER TABLE writing_jobs ADD COLUMN retry_count INTEGER DEFAULT 0')
conn.execute('ALTER TABLE writing_jobs ADD COLUMN max_retries INTEGER DEFAULT 3')
conn.execute('ALTER TABLE writing_jobs ADD COLUMN error_message TEXT')
conn.execute('ALTER TABLE writing_jobs ADD COLUMN result TEXT')
conn.execute('ALTER TABLE writing_jobs ADD COLUMN metadata TEXT DEFAULT "{}"')
conn.commit()
print('Columns added successfully')
