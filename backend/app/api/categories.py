"""
目标类别管理接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.services.category_service import (
    init_categories,
    add_category,
    get_all_categories,
    get_category_by_name,
    delete_category,
    update_category_count
)

router = APIRouter(prefix="/api/categories", tags=["类别管理"])


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    """获取所有目标类别"""
    categories = get_all_categories(db)
    return {
        "code": 200,
        "message": "success",
        "data": [{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "color": cat.color,
            "count": cat.count,
            "created_at": cat.created_at
        } for cat in categories]
    }


@router.get("/{name}")
def get_category(name: str, db: Session = Depends(get_db)):
    """根据名称获取类别"""
    category = get_category_by_name(db, name)
    if not category:
        raise HTTPException(status_code=404, detail=f"类别 '{name}' 不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "count": category.count,
            "created_at": category.created_at
        }
    }


@router.post("/")
def create_category(
    name: str,
    description: str = None,
    color: str = None,
    db: Session = Depends(get_db)
):
    """新增目标类别"""
    result = add_category(db, name, description, color)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "code": 200,
        "message": result["message"],
        "data": result.get("data")
    }


@router.delete("/{name}")
def remove_category(name: str, db: Session = Depends(get_db)):
    """删除目标类别"""
    result = delete_category(db, name)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "code": 200,
        "message": result["message"]
    }


@router.post("/init")
def initialize_categories(db: Session = Depends(get_db)):
    """初始化目标类别（插入默认类别）"""
    result = init_categories(db)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "code": 200,
        "message": result["message"]
    }
