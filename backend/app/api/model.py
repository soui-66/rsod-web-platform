"""
模型管理 API 路由
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

# 导入数据库模型和依赖
from database import get_db
from models import ModelVersion
from app.services.detection_service import DetectionService

# 创建API路由实例
router = APIRouter(prefix="/models", tags=["模型管理"])

# 模型存储目录
MODEL_DIR = "models"

# 获取BASE_DIR
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)

# 单例检测服务
_detection_service = None

def get_detection_service():
    """获取检测服务实例（单例）"""
    global _detection_service
    if _detection_service is None:
        model_path = os.path.join(BASE_DIR, "runs", "detect", "best_model.pt")
        _detection_service = DetectionService(model_path, BASE_DIR)
        print("[模型管理接口] 检测服务初始化完成")
    return _detection_service

@router.post("/upload")
async def upload_model(
    file: UploadFile = File(...),
    model_name: str = None,
    db: Session = Depends(get_db)
):
    """
    上传模型文件
    """
    try:
        # 确保模型目录存在
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        # 确定文件名
        filename = model_name or file.filename
        if not filename.endswith(".pt") and not filename.endswith(".onnx"):
            raise HTTPException(status_code=400, detail="模型文件必须是 .pt 或 .onnx 格式")
        
        # 保存文件
        file_path = os.path.join(MODEL_DIR, filename)
        contents = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 检查是否已存在同名模型
        existing_model = db.query(ModelVersion).filter(ModelVersion.file_name == filename).first()
        
        if existing_model:
            # 更新现有记录
            existing_model.file_path = file_path
            existing_model.is_active = False
        else:
            # 创建新记录
            new_model = ModelVersion(
                name=filename.replace(".pt", "").replace(".onnx", ""),
                file_name=filename,
                file_path=file_path,
                is_active=False
            )
            db.add(new_model)
        
        db.commit()
        
        return {"success": True, "message": "模型上传成功", "model_name": filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型上传失败: {str(e)}")

@router.get("/list")
def list_models(db: Session = Depends(get_db)):
    """
    获取模型列表
    """
    try:
        models = db.query(ModelVersion).all()
        
        model_list = []
        for model in models:
            model_list.append({
                "id": model.id,
                "model_name": model.file_name,
                "name": model.name,
                "file_path": model.file_path,
                "status": "active" if model.is_active else "inactive",
                "model_type": model.model_type,
                "version": model.version,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            })
        
        return {"success": True, "data": model_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.post("/switch/{model_name}")
def switch_model(model_name: str, db: Session = Depends(get_db)):
    """
    切换当前使用的模型
    """
    try:
        # 检查模型是否存在
        model = db.query(ModelVersion).filter(ModelVersion.file_name == model_name).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 尝试加载模型
        try:
            service = get_detection_service()
            service.load_model(model.file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"模型加载失败: {str(e)}")
        
        # 更新所有模型状态
        db.query(ModelVersion).update({ModelVersion.is_active: False})
        model.is_active = True
        db.commit()
        
        return {"success": True, "message": f"模型切换成功: {model_name}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型切换失败: {str(e)}")

@router.get("/current")
def get_current_model(db: Session = Depends(get_db)):
    """
    获取当前使用的模型
    """
    try:
        model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
        
        if model:
            return {
                "success": True,
                "data": {
                    "id": model.id,
                    "model_name": model.file_name,
                    "name": model.name,
                    "file_path": model.file_path,
                    "status": "active" if model.is_active else "inactive"
                }
            }
        else:
            return {"success": True, "data": None, "message": "当前没有激活的模型"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当前模型失败: {str(e)}")

@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    """
    删除模型
    """
    try:
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 如果是当前活跃模型，不允许删除
        if model.is_active:
            raise HTTPException(status_code=400, detail="不能删除当前活跃的模型")
        
        # 删除文件
        if os.path.exists(model.file_path):
            os.remove(model.file_path)
        
        # 删除数据库记录
        db.delete(model)
        db.commit()
        
        return {"success": True, "message": "模型删除成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型删除失败: {str(e)}")
