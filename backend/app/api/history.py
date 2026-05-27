# 历史记录接口
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

from database import get_db
from models import DetectionRecord

router = APIRouter(prefix="/api/history", tags=["历史记录"])


@router.get("/list")
async def get_history_list(
    page: int = 1,
    page_size: int = 10,
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """
    获取历史记录列表

    参数：
        page: 页码（从1开始）
        page_size: 每页数量
        user_id: 用户ID，用于筛选当前用户的记录

    返回：
        分页的历史记录列表
    """
    try:
        print(f"获取历史记录列表 - page: {page}, page_size: {page_size}, user_id: {user_id}")
        
        query = db.query(DetectionRecord)
        
        # 如果提供了有效的user_id，只返回该用户的记录
        if user_id is not None and user_id > 0:
            print(f"筛选用户ID: {user_id}")
            query = query.filter(DetectionRecord.user_id == user_id)
        
        query = query.order_by(DetectionRecord.created_at.desc())
        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for r in records:
            record_data = {
                "id": r.id,
                "file_name": r.file_name,
                "file_path": r.original_image,
                "result_path": r.result_image,
                "mode": r.mode,
                "model_name": r.model_name,
                "detections": json.loads(r.detections) if r.detections else [],
                "target_count": r.target_count,
                "duration": r.duration,
                "max_confidence": r.max_confidence,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
            }
            # 如果是批量检测，添加批量数据
            if r.batch_data:
                record_data["batch_data"] = json.loads(r.batch_data)
            result.append(record_data)

        print(f"返回记录数: {len(result)}")
        return {"code": 200, "data": {"total": total, "records": result}}
    except Exception as e:
        print(f"获取历史记录列表错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"code": 500, "message": str(e)}


@router.get("/detail/{record_id}")
async def get_history_detail(record_id: int, user_id: int = None, db: Session = Depends(get_db)):
    """
    获取历史记录详情

    参数：
        record_id: 记录ID
        user_id: 用户ID，用于验证记录归属

    返回：
        记录详细信息
    """
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 如果提供了有效的user_id，验证记录是否属于该用户
    if user_id is not None and user_id > 0 and record.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此记录")

    record_data = {
        "id": record.id,
        "file_name": record.file_name,
        "file_path": record.original_image,
        "result_path": record.result_image,
        "mode": record.mode,
        "detections": json.loads(record.detections) if record.detections else [],
        "target_count": record.target_count,
        "duration": record.duration,
        "max_confidence": record.max_confidence,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    # 如果是批量检测，添加批量数据
    if record.batch_data:
        record_data["batch_data"] = json.loads(record.batch_data)
    return {
        "code": 200,
        "data": record_data
    }


@router.delete("/{record_id}")
async def delete_history_record(record_id: int, user_id: int = None, db: Session = Depends(get_db)):
    """
    删除历史记录

    参数：
        record_id: 记录ID
        user_id: 用户ID，用于验证记录归属

    返回：
        删除结果
    """
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 如果提供了有效的user_id，验证记录是否属于该用户
    if user_id is not None and user_id > 0 and record.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除此记录")
    
    db.delete(record)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.get("/stats")
async def get_history_stats(user_id: int = None, db: Session = Depends(get_db)):
    """
    获取历史记录统计信息

    参数：
        user_id: 用户ID，用于筛选当前用户的记录

    返回：
        统计数据，包括总数、今日数量、总检测目标数
    """
    print("统计API被调用")
    try:
        query = db.query(DetectionRecord)
        
        # 如果提供了有效的user_id，只统计该用户的记录
        if user_id is not None and user_id > 0:
            query = query.filter(DetectionRecord.user_id == user_id)
        
        records = query.all()
        total_count = len(records)

        total_targets = 0
        today_count = 0
        today_str = datetime.now().strftime('%Y-%m-%d')

        for record in records:
            total_targets += record.target_count
            if str(record.created_at).startswith(today_str):
                today_count += 1

        result = {"code": 200, "data": {"total_count": total_count, "today_count": today_count, "total_targets": total_targets}}
        print(f"返回结果: {result}")
        return result
    except Exception as e:
        print(f"统计API错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})