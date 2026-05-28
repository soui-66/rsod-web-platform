from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
from models import ModelVersion
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/api/model", tags=["模型管理"])

MODEL_DIR = "models"


@router.post("/upload")
async def upload_model(
        file: UploadFile = File(...),
        name: str = Form(""),
        description: str = Form(""),
        version: str = Form("1.0"),
        db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pt"):
        raise HTTPException(status_code=400, detail="只支持 .pt 格式的模型文件")

    os.makedirs(MODEL_DIR, exist_ok=True)

    file_path = os.path.join(MODEL_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    model_name = name if name else file.filename.replace(".pt", "")

    record = ModelVersion(
        name=model_name,
        description=description,
        file_path=file_path,
        file_name=file.filename,
        version=version,
        created_at=datetime.now()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"code": 200, "message": "模型上传成功", "data": {"id": record.id, "name": record.name}}


@router.get("/list")
async def list_models(db: Session = Depends(get_db)):
    models = db.query(ModelVersion).filter(ModelVersion.is_active == True).all()

    result = []
    for m in models:
        result.append({
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "file_name": m.file_name,
            "model_type": m.model_type,
            "version": m.version,
            "accuracy": m.accuracy,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return {"code": 200, "data": result}


@router.get("/{model_id}")
async def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    return {"code": 200, "data": {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "file_path": model.file_path,
        "file_name": model.file_name,
        "model_type": model.model_type,
        "version": model.version,
        "accuracy": model.accuracy
    }}


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    if os.path.exists(model.file_path):
        os.remove(model.file_path)

    db.delete(model)
    db.commit()

    return {"code": 200, "message": "模型删除成功"}


@router.put("/{model_id}")
async def update_model(
        model_id: int,
        name: str = None,
        description: str = None,
        accuracy: float = None,
        db: Session = Depends(get_db)
):
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    if name:
        model.name = name
    if description:
        model.description = description
    if accuracy:
        model.accuracy = accuracy
    model.updated_at = datetime.now()

    db.commit()

    return {"code": 200, "message": "模型更新成功"}