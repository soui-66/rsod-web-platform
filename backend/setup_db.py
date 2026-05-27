"""
数据库初始化和迁移脚本
用于确保数据库表结构正确
"""
import sqlite3
import os
from sqlalchemy import inspect
from database import engine, init_db


def check_and_migrate_database():
    """检查并迁移数据库"""
    db_path = "rsod_platform.db"
    
    print("=" * 50)
    print("数据库初始化和迁移工具")
    print("=" * 50)
    
    # 检查数据库文件是否存在
    if os.path.exists(db_path):
        print("\n[INFO] 找到现有数据库: %s" % db_path)
        
        # 检查表是否存在
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查 detection_records 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detection_records'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("[OK] detection_records 表已存在")
            
            # 检查字段
            cursor.execute("PRAGMA table_info(detection_records)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print("   当前字段: %s" % ', '.join(column_names))
            
            # 检查需要添加的字段
            required_fields = ['user_id', 'batch_data']
            missing_fields = [f for f in required_fields if f not in column_names]
            
            if missing_fields:
                print("[WARN] 缺少字段: %s，正在添加..." % ', '.join(missing_fields))
                
                try:
                    # SQLite 不支持直接添加带默认值的列，需要分步操作
                    # 1. 备份数据
                    cursor.execute("CREATE TABLE detection_records_backup AS SELECT * FROM detection_records")
                    
                    # 2. 删除原表
                    cursor.execute("DROP TABLE detection_records")
                    
                    # 3. 重新创建表（包含所有必需字段）
                    cursor.execute("""
                        CREATE TABLE detection_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            file_name VARCHAR(255) NOT NULL,
                            original_image TEXT NOT NULL,
                            result_image TEXT,
                            mode VARCHAR(20) DEFAULT 'single',
                            model_name VARCHAR(50) DEFAULT 'yolo11n',
                            detections TEXT,
                            target_count INTEGER DEFAULT 0,
                            duration REAL DEFAULT 0.0,
                            max_confidence REAL DEFAULT 0.0,
                            created_at DATETIME,
                            batch_data TEXT
                        )
                    """)
                    
                    # 4. 恢复数据
                    cursor.execute("""
                        INSERT INTO detection_records 
                        (id, file_name, original_image, result_image, mode, model_name, detections, 
                         target_count, duration, max_confidence, created_at)
                        SELECT id, file_name, original_image, result_image, mode, model_name, detections,
                               target_count, duration, max_confidence, created_at
                        FROM detection_records_backup
                    """)
                    
                    # 5. 删除备份表
                    cursor.execute("DROP TABLE detection_records_backup")
                    
                    conn.commit()
                    print("[OK] 字段 %s 添加成功！" % ', '.join(missing_fields))
                    
                except Exception as e:
                    conn.rollback()
                    print("[ERROR] 添加字段失败: %s" % str(e))
                    print("   建议：删除 rsod_platform.db 文件后重新运行")
                    return False
            else:
                print("[OK] 所有必需字段都已存在")
        else:
            print("[WARN] detection_records 表不存在，将创建新表")
            
        conn.close()
    else:
        print("\n[INFO] 数据库文件不存在，将创建新数据库: %s" % db_path)
    
    # 使用 SQLAlchemy 初始化数据库
    print("\n正在使用 SQLAlchemy 初始化数据库...")
    try:
        init_db()
        print("\n[OK] 数据库初始化完成！")
        return True
    except Exception as e:
        print("\n[ERROR] 数据库初始化失败: %s" % str(e))
        return False


def verify_database():
    """验证数据库结构"""
    print("\n" + "=" * 50)
    print("数据库结构验证")
    print("=" * 50)
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\n[INFO] 数据库表列表: %s" % ', '.join(tables))
        
        if "detection_records" in tables:
            columns = inspector.get_columns('detection_records')
            print("\n[INFO] detection_records 表字段:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = " DEFAULT %s" % col['default'] if col['default'] else ""
                print("   - %s: %s %s%s" % (col['name'], col['type'], nullable, default))
            
            # 验证关键字段
            required_fields = ['id', 'user_id', 'file_name', 'original_image', 'result_image', 'mode', 
                             'model_name', 'detections', 'target_count', 'duration', 
                             'max_confidence', 'created_at', 'batch_data']
            
            existing_fields = [col['name'] for col in columns]
            missing_fields = [f for f in required_fields if f not in existing_fields]
            
            if missing_fields:
                print("\n[ERROR] 缺少字段: %s" % ', '.join(missing_fields))
                return False
            else:
                print("\n[OK] 所有必需字段都存在")
                return True
        else:
            print("\n[ERROR] detection_records 表不存在")
            return False
            
    except Exception as e:
        print("\n[ERROR] 验证失败: %s" % str(e))
        return False


if __name__ == "__main__":
    # 初始化和迁移数据库
    success = check_and_migrate_database()
    
    if success:
        # 验证数据库结构
        verify_database()
        
        print("\n" + "=" * 50)
        print("[OK] 数据库设置完成！可以启动后端服务了。")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("[ERROR] 数据库设置失败！")
        print("建议：删除 rsod_platform.db 文件后重新运行此脚本")
        print("=" * 50)