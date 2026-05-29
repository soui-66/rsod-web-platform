"""
目标类别服务 - 处理类别初始化和自动更新
"""
from sqlalchemy.orm import Session
from models import TargetCategory
from database import get_db
from datetime import datetime


def init_categories(db: Session):
    """
    初始化目标类别表
    只确保表存在，不插入任何数据
    类别将在检测时根据检测结果自动添加
    """
    try:
        # 检查表是否存在（通过查询实现）
        existing_count = db.query(TargetCategory).count()
        print(f"[INFO] target_categories 表已存在，当前数据量: {existing_count} 条")
        return {"status": "success", "message": f"目标类别表已就绪，当前 {existing_count} 条数据"}
    
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 初始化类别表失败: {e}")
        return {"status": "error", "message": str(e)}


def add_category(db: Session, name: str, description: str = None, color: str = None):
    """
    添加新的目标类别
    :param name: 类别名称（唯一）
    :param description: 类别描述
    :param color: 显示颜色
    :return: 操作结果
    """
    try:
        # 检查是否已存在
        existing = db.query(TargetCategory).filter(TargetCategory.name == name).first()
        
        if existing:
            return {"status": "info", "message": f"类别 '{name}' 已存在"}
        
        # 创建新类别
        category = TargetCategory(
            name=name,
            description=description,
            color=color if color else f"#{hex(hash(name) % 16777215)[2:].zfill(6)}"
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        
        print(f"[OK] 新增类别: {name}")
        return {"status": "success", "message": f"新增类别 '{name}'", "data": category.__dict__}
    
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 添加类别失败: {e}")
        return {"status": "error", "message": str(e)}


def update_category_count(db: Session, category_names: list):
    """
    根据检测结果更新类别计数
    :param category_names: 检测到的类别名称列表
    """
    try:
        print(f"[类别更新] 开始处理 {len(category_names)} 个类别")
        
        for name in category_names:
            if not name:
                print(f"[类别更新] 跳过空类别名称")
                continue
                
            # 先尝试获取已有类别
            category = db.query(TargetCategory).filter(TargetCategory.name == name).first()
            
            if category:
                # 更新计数
                category.count = category.count + 1
                print(f"[类别更新] 更新类别计数: {name} -> {category.count}")
            else:
                # 自动添加新类别并设置初始计数为1
                print(f"[类别更新] 添加新类别: {name}")
                category = TargetCategory(
                    name=name,
                    count=1,
                    color=f"#{hex(hash(name) % 16777215)[2:].zfill(6)}"
                )
                db.add(category)
                print(f"[类别更新] 新类别 '{name}' 添加成功")
        
        db.commit()
        print(f"[类别更新] 成功更新 {len(category_names)} 个类别计数")
        return {"status": "success", "message": f"更新了 {len(category_names)} 个类别计数"}
    
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 更新类别计数失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def get_all_categories(db: Session):
    """获取所有目标类别"""
    return db.query(TargetCategory).order_by(TargetCategory.id).all()


def get_category_by_name(db: Session, name: str):
    """根据名称获取类别"""
    return db.query(TargetCategory).filter(TargetCategory.name == name).first()


def delete_category(db: Session, name: str):
    """删除类别"""
    try:
        category = db.query(TargetCategory).filter(TargetCategory.name == name).first()
        if not category:
            return {"status": "error", "message": f"类别 '{name}' 不存在"}
        
        db.delete(category)
        db.commit()
        return {"status": "success", "message": f"删除类别 '{name}'"}
    
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
