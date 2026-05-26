# 数据验证接口
from fastapi import APIRouter
from pathlib import Path
import os

from app.utils.validation import CheckContext, DataValidator, ValidationReport, CheckLevel, CheckResult

router = APIRouter(prefix="/api/validate", tags=["数据验证"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)


@router.post("/dataset")
async def validate_dataset(
    annotations_dir: str = None,
    images_dir: str = None,
    classes: str = "aircraft,oiltank,overpass,playground"
):
    # 确定标注目录和图片目录
    if annotations_dir:
        annotations_path = Path(annotations_dir)
    else:
        annotations_path = Path(BASE_DIR) / "datasets" / "rsod"

    if images_dir:
        images_path = Path(images_dir)
    else:
        images_path = Path(BASE_DIR) / "datasets" / "rsod"

    # 解析类别列表
    class_list = [c.strip() for c in classes.split(",") if c.strip()]

    # 创建验证上下文
    context = CheckContext(
        annotations_dir=annotations_path if annotations_path.exists() else None,
        images_dir=images_path if images_path.exists() else None,
        classes=class_list if class_list else None,
        image_extensions=[".jpg", ".jpeg", ".png"]
    )

    # 执行验证（使用你的原版）
    validator = DataValidator(context)
    report = validator.validate()

    # 构建返回结果
    results = []
    for result in report.results:
        results.append({
            "level": result.level.value,
            "message": result.message,
            "check_name": result.check_name,
            "details": result.details
        })

    return {
        "code": 200,
        "message": "数据验证完成",
        "data": {
            "passed": report.passed,
            "summary": {
                "passed": report.pass_count,
                "warnings": report.warning_count,
                "errors": report.error_count
            },
            "results": results
        }
    }