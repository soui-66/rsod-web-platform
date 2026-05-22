#!/usr/bin/env python3
"""
数据验证子系统测试脚本

演示如何使用数据验证子系统来验证数据集的完整性和一致性
"""

from pathlib import Path
from app.utils.validation import (
    CheckContext,
    DataValidator,
    CheckLevel,
    list_validators,
    register_validator
)


def test_basic_validation():
    """基本验证测试"""
    print("\n" + "=" * 60)
    print("测试1: 基本验证")
    print("=" * 60)

    context = CheckContext(
        annotations_dir=Path("datasets/rsod"),
        images_dir=Path("datasets/rsod"),
        classes=["aircraft", "oiltank", "overpass", "playground"]
    )

    validator = DataValidator(context)
    report = validator.validate()

    print(report)
    print(f"\n验证结果: {'通过' if report.passed else '失败'}")
    return report.passed


def test_selective_validation():
    """选择性验证测试"""
    print("\n" + "=" * 60)
    print("测试2: 选择性验证（只验证目录）")
    print("=" * 60)

    context = CheckContext(
        annotations_dir=Path("datasets/rsod"),
        images_dir=Path("datasets/rsod"),
        classes=["aircraft", "oiltank", "overpass", "playground"]
    )

    validator = DataValidator(context, validators=["directories_exist"])
    report = validator.validate()

    print(report)
    return report.passed


def test_custom_validator():
    """自定义验证器测试"""
    print("\n" + "=" * 60)
    print("测试3: 自定义验证器")
    print("=" * 60)

    @register_validator("custom_check")
    def custom_check(ctx):
        """自定义检查示例"""
        from app.utils.validation import CheckResult, CheckLevel

        results = []
        if ctx.annotations_dir:
            if ctx.annotations_dir.exists():
                results.append(CheckResult(
                    level=CheckLevel.INFO,
                    message=f"自定义检查：标注目录存在 - {ctx.annotations_dir}"
                ))
            else:
                results.append(CheckResult(
                    level=CheckLevel.WARNING,
                    message="自定义检查：标注目录不存在"
                ))
        return results

    context = CheckContext(
        annotations_dir=Path("datasets/rsod"),
        images_dir=Path("datasets/rsod")
    )

    validator = DataValidator(context, validators=["custom_check"])
    report = validator.validate()

    print(report)
    return report.passed


def test_validation_report():
    """验证报告测试"""
    print("\n" + "=" * 60)
    print("测试4: 验证报告详细分析")
    print("=" * 60)

    context = CheckContext(
        annotations_dir=Path("datasets/rsod"),
        images_dir=Path("datasets/rsod"),
        classes=["aircraft", "oiltank", "overpass", "playground"]
    )

    validator = DataValidator(context)
    report = validator.validate()

    print(f"\n统计信息:")
    print(f"  通过: {report.pass_count}")
    print(f"  警告: {report.warning_count}")
    print(f"  错误: {report.error_count}")
    print(f"  信息: {report.info_count}")

    print(f"\n阻断性错误:")
    blocking_errors = report.get_blocking_errors()
    if blocking_errors:
        for error in blocking_errors:
            print(f"  - {error}")
    else:
        print("  无")

    print(f"\nWARNING 级别结果:")
    warnings = report.get_results_by_level(CheckLevel.WARNING)
    if warnings:
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("  无")

    return report.passed


def list_available_validators():
    """列出所有可用的验证器"""
    print("\n" + "=" * 60)
    print("可用的验证器列表")
    print("=" * 60)

    validators = list_validators()
    print(f"\n共有 {len(validators)} 个内置验证器:")
    for i, name in enumerate(validators, 1):
        print(f"  {i}. {name}")

    print("\n验证器说明:")
    validator_descriptions = {
        "directories_exist": "检查标注目录和图片目录是否存在",
        "annotation_files": "检查 XML 标注文件是否存在及数量",
        "image_annotation_match": "检查图片和标注文件是否匹配",
        "class_validation": "检查标注中的类别是否有效",
        "file_count": "检查文件数量是否满足最低要求"
    }

    for name, desc in validator_descriptions.items():
        print(f"  - {name}: {desc}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("数据验证子系统测试")
    print("=" * 60)

    # 列出所有验证器
    list_available_validators()

    # 执行各项测试
    all_passed = True

    all_passed &= test_basic_validation()
    all_passed &= test_selective_validation()
    all_passed &= test_custom_validator()
    all_passed &= test_validation_report()

    # 最终结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"\n所有测试: {'✅ 通过' if all_passed else '❌ 失败'}")

    print("\n使用提示:")
    print("  1. 使用 CheckContext 创建验证上下文")
    print("  2. 使用 DataValidator 执行验证")
    print("  3. 使用 ValidationReport 分析结果")
    print("  4. 使用 @register_validator 添加自定义验证器")
