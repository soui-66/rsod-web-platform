#!/usr/bin/env python3
"""
数据验证子系统
提供可组合、可扩展的数据验证功能
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# 添加 backend 目录到 sys.path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.utils.logger import get_logger
logger = get_logger("validator")


class CheckLevel(Enum):
    """检查结果级别"""
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    """检查结果"""
    level: CheckLevel
    message: str
    check_name: str = ""
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def __str__(self):
        level_symbol = {
            CheckLevel.PASS: "✅",
            CheckLevel.INFO: "ℹ️",
            CheckLevel.WARNING: "⚠️",
            CheckLevel.ERROR: "❌"
        }.get(self.level, "")

        level_name = {
            CheckLevel.PASS: "PASS",
            CheckLevel.INFO: "INFO",
            CheckLevel.WARNING: "WARNING",
            CheckLevel.ERROR: "ERROR"
        }.get(self.level, "")

        msg = f"{level_symbol} [{level_name}] {self.message}"
        if self.details:
            for key, value in self.details.items():
                if key == "missing" and isinstance(value, list):
                    msg += f"\n   {key}: {value}"
                elif key == "count":
                    msg += f"\n   {key}: {value}"
        return msg


@dataclass
class CheckContext:
    """检查上下文"""
    annotations_dir: Optional[Path] = None
    images_dir: Optional[Path] = None
    classes: Optional[List[str]] = None
    dataset_name: str = ""
    image_extensions: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
    )
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.classes is None:
            self.classes = []


# ==================== 验证器注册表 ====================

_validators: Dict[str, callable] = {}


def register_validator(name: str):
    """验证器装饰器"""
    def decorator(func):
        _validators[name] = func
        func._validator_name = name
        return func
    return decorator


def get_validator(name: str) -> Optional[callable]:
    """获取验证器"""
    return _validators.get(name)


def list_validators() -> List[str]:
    """列出所有注册的验证器"""
    return list(_validators.keys())


def run_validators(context: CheckContext, validator_names: List[str] = None) -> List[CheckResult]:
    """
    运行验证器

    参数：
        context: 检查上下文
        validator_names: 指定运行的验证器列表，None 表示运行所有

    返回：
        List[CheckResult]: 所有检查结果
    """
    results = []
    names = validator_names if validator_names else list_validators()

    logger.info(f"开始运行 {len(names)} 个验证器...")

    for name in names:
        validator = get_validator(name)
        if validator:
            try:
                check_results = validator(context)
                for r in check_results:
                    if not r.check_name:
                        r.check_name = name
                    logger.info(str(r))
                results.extend(check_results)
            except Exception as e:
                error_result = CheckResult(
                    level=CheckLevel.ERROR,
                    message=f"验证器执行失败: {str(e)}",
                    check_name=name
                )
                logger.error(str(error_result))
                results.append(error_result)

    return results


def generate_report(results: List[CheckResult]) -> Dict[str, Any]:
    """
    生成验证报告

    返回：
        Dict: 包含统计信息和错误列表
    """
    report = {
        "total": len(results),
        "passed": 0,
        "warnings": 0,
        "errors": 0,
        "infos": 0,
        "has_error": False,
        "has_warning": False,
        "results": results
    }

    for r in results:
        if r.level == CheckLevel.PASS:
            report["passed"] += 1
        elif r.level == CheckLevel.WARNING:
            report["warnings"] += 1
            report["has_warning"] = True
        elif r.level == CheckLevel.ERROR:
            report["errors"] += 1
            report["has_error"] = True
        elif r.level == CheckLevel.INFO:
            report["infos"] += 1

    return report


def print_report(report: Dict[str, Any]):
    """打印验证报告"""
    logger.info("=" * 60)
    logger.info("验证报告汇总")
    logger.info("=" * 60)
    logger.info(f"总计检查项: {report['total']}")
    logger.info(f"  ✅ 通过: {report['passed']}")
    logger.info(f"  ℹ️  信息: {report['infos']}")
    logger.info(f"  ⚠️  警告: {report['warnings']}")
    logger.info(f"  ❌ 错误: {report['errors']}")

    if report['has_error']:
        logger.error("=" * 60)
        logger.error("验证失败！请修复上述错误后重试。")
        logger.error("=" * 60)
        return False
    elif report['has_warning']:
        logger.warning("=" * 60)
        logger.warning("验证完成，但存在警告，请留意。")
        logger.warning("=" * 60)
        return True
    else:
        logger.info("=" * 60)
        logger.info("✅ 所有验证通过！")
        logger.info("=" * 60)
        return True


# ==================== 内置验证器 ====================

@register_validator("directories_exist")
def check_directories(ctx: CheckContext) -> List[CheckResult]:
    """检查必要目录是否存在"""
    results = []

    if ctx.annotations_dir:
        if ctx.annotations_dir.exists():
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"标注目录存在: {ctx.annotations_dir}"
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"标注目录不存在: {ctx.annotations_dir}"
            ))

    if ctx.images_dir:
        if ctx.images_dir.exists():
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"图片目录存在: {ctx.images_dir}"
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"图片目录不存在: {ctx.images_dir}"
            ))

    return results


@register_validator("annotation_files")
def check_annotation_files(ctx: CheckContext) -> List[CheckResult]:
    """检查标注文件"""
    results = []

    if not ctx.annotations_dir or not ctx.annotations_dir.exists():
        return results

    xml_files = list(ctx.annotations_dir.glob("*.xml"))

    if len(xml_files) == 0:
        results.append(CheckResult(
            level=CheckLevel.ERROR,
            message="未找到任何 XML 标注文件"
        ))
    else:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"找到 {len(xml_files)} 个 XML 标注文件",
            details={"count": len(xml_files)}
        ))

    return results


@register_validator("image_files")
def check_image_files(ctx: CheckContext) -> List[CheckResult]:
    """检查图片文件"""
    results = []

    if not ctx.images_dir or not ctx.images_dir.exists():
        return results

    image_files = []
    for ext in ctx.image_extensions:
        image_files.extend(list(ctx.images_dir.glob(f"*{ext}")))

    if len(image_files) == 0:
        results.append(CheckResult(
            level=CheckLevel.ERROR,
            message="未找到任何图片文件"
        ))
    else:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"找到 {len(image_files)} 个图片文件",
            details={"count": len(image_files)}
        ))

    return results


@register_validator("image_annotation_match")
def check_image_annotation_match(ctx: CheckContext) -> List[CheckResult]:
    """检查图片和标注文件是否匹配"""
    results = []

    if not ctx.annotations_dir or not ctx.images_dir:
        return results

    if not ctx.annotations_dir.exists() or not ctx.images_dir.exists():
        return results

    # 收集所有标注文件的基础名
    xml_files = {f.stem for f in ctx.annotations_dir.glob("*.xml")}

    # 收集所有图片文件的基础名
    image_files = set()
    for ext in ctx.image_extensions:
        image_files.update({f.stem for f in ctx.images_dir.glob(f"*{ext}")})

    # 有标注但无图片
    missing_images = xml_files - image_files
    if missing_images:
        missing_list = sorted(list(missing_images))[:10]
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_images)} 个标注文件缺少对应图片",
            details={"missing": missing_list, "count": len(missing_images)}
        ))

    # 有图片但无标注
    missing_annotations = image_files - xml_files
    if missing_annotations:
        missing_list = sorted(list(missing_annotations))[:10]
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_annotations)} 个图片缺少对应标注",
            details={"missing": missing_list, "count": len(missing_annotations)}
        ))

    # 完全匹配
    if not missing_images and not missing_annotations:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"图片和标注文件完全匹配，共 {len(xml_files)} 对"
        ))

    return results


@register_validator("class_validation")
def check_classes(ctx: CheckContext) -> List[CheckResult]:
    """检查标注中的类别是否有效"""
    results = []

    if not ctx.annotations_dir or not ctx.annotations_dir.exists():
        return results

    classes_set = set(ctx.classes) if ctx.classes else set()
    found_classes: Set[str] = set()
    unknown_classes: Set[str] = set()
    invalid_files: List[str] = []

    # 遍历前100个 XML 文件
    for xml_file in list(ctx.annotations_dir.glob("*.xml"))[:100]:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall("object"):
                name_elem = obj.find("name")
                if name_elem is not None and name_elem.text:
                    class_name = name_elem.text
                    found_classes.add(class_name)

                    if classes_set and class_name not in classes_set:
                        unknown_classes.add(class_name)
        except Exception:
            invalid_files.append(xml_file.name)

    # 报告发现的类别
    if found_classes:
        results.append(CheckResult(
            level=CheckLevel.INFO,
            message=f"数据集中发现的类别: {sorted(found_classes)}"
        ))

    # 报告未知类别
    if unknown_classes:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"发现未知类别: {sorted(unknown_classes)}"
        ))

    # 报告无效文件
    if invalid_files:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"无法解析的 XML 文件: {len(invalid_files)} 个"
        ))

    # 验证通过
    if not unknown_classes and not invalid_files:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message="类别验证通过"
        ))

    return results


@register_validator("dataset_structure")
def check_dataset_structure(ctx: CheckContext) -> List[CheckResult]:
    """检查数据集目录结构（VOC格式）"""
    results = []

    if not ctx.dataset_name:
        return results

    # 检查常见的 VOC 目录结构
    expected_dirs = {
        "Annotation": ctx.annotations_dir,
        "JPEGImages": ctx.images_dir
    }

    all_exist = True
    for name, path in expected_dirs.items():
        if path and path.exists():
            results.append(CheckResult(
                level=CheckLevel.INFO,
                message=f"目录 {name} 存在"
            ))
        else:
            all_exist = False

    if all_exist:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"数据集 {ctx.dataset_name} 目录结构验证通过"
        ))

    return results


# ==================== 便捷函数 ====================

def validate_raw_dataset(
    annotations_dir: Path,
    images_dir: Path,
    dataset_name: str = "",
    classes: List[str] = None
) -> bool:
    """
    验证原始数据集

    参数：
        annotations_dir: 标注目录
        images_dir: 图片目录
        dataset_name: 数据集名称
        classes: 期望的类别列表

    返回：
        bool: 是否通过验证（无ERROR）
    """
    ctx = CheckContext(
        annotations_dir=annotations_dir,
        images_dir=images_dir,
        dataset_name=dataset_name,
        classes=classes
    )

    validators = [
        "directories_exist",
        "annotation_files",
        "image_files",
        "image_annotation_match",
        "class_validation"
    ]

    results = run_validators(ctx, validators)
    report = generate_report(results)
    return print_report(report)


def quick_validate(
    annotations_dir: Path,
    images_dir: Path
) -> bool:
    """
    快速验证（仅检查必要项）

    参数：
        annotations_dir: 标注目录
        images_dir: 图片目录

    返回：
        bool: 是否通过验证
    """
    ctx = CheckContext(
        annotations_dir=annotations_dir,
        images_dir=images_dir
    )

    validators = [
        "directories_exist",
        "annotation_files",
        "image_annotation_match"
    ]

    results = run_validators(ctx, validators)
    report = generate_report(results)
    return print_report(report)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 测试验证器
    from app.utils.paths import Paths

    rsod_path = Paths.rsod_data()
    if rsod_path.exists():
        # 检查第一个类别
        aircraft_dir = rsod_path / "aircraft"
        if aircraft_dir.exists():
            annotations_dir = aircraft_dir / "Annotation" / "xml"
            images_dir = aircraft_dir / "JPEGImages"

            print("\n" + "=" * 60)
            print("测试验证器")
            print("=" * 60)

            quick_validate(annotations_dir, images_dir)