"""数据库迁移脚本 - 添加batch_data字段"""
import sqlite3
import os

DB_PATH = "rsod_platform.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("数据库不存在，无需迁移")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查batch_data字段是否存在
        cursor.execute("PRAGMA table_info(detection_records)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "batch_data" not in columns:
            print("正在添加batch_data字段...")
            cursor.execute("ALTER TABLE detection_records ADD COLUMN batch_data TEXT")
            conn.commit()
            print("✅ batch_data字段添加成功")
        else:
            print("batch_data字段已存在")
            
    except Exception as e:
        print(f"迁移失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
