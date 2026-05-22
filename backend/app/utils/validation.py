#!/usr/bin/env python3
"""
数据验证子系统
提供可扩展的数据质量保障体系，用于验证数据集的完整性和一致性

核心特性：
- 检查结果分级（PASS, INFO, WARNING, ERROR）
- 检查上下文封装，统一验证器输入
- 验证器注册表模式，支持插件化扩展
- 内置验证器：目录、文件、匹配、类别
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class CheckLevel(Enum):
    """
    检查结果级别

    为什么分级而不是简单的 True/False？
    - 不同级别的错误需要不同的处理方式
    - ERROR 应该阻断流程，WARNING 可以继续
    - INFO 用于展示额外信息，不影响判断
    - PASS 用于确认正常状态
    """
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    """
    单个检查结果

    为什么用 dataclass？
    - 自动生成 __init__、__repr__ 等方法
    - 类型提示清晰
    - 方便序列化和比较
    """
    level: CheckLevel
    message: str
    check_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def __str__(self):
        """友好字符串表示"""
        level_symbols = {
            CheckLevel.PASS: "✅",
            CheckLevel.INFO: "ℹ️ ",
            CheckLevel.WARNING: "⚠️ ",
            CheckLevel.ERROR: "❌"
        }
        symbol = level_symbols.get(self.level, "•")
        name_part = f"[{self.check_name}] " if self.check_name else ""
        return f"{symbol} [{self.level.value.upper()}] {name_part}{self.message}"

    def is_blocking(self):
        """判断是否为阻断性错误"""
        return self.level == CheckLevel.ERROR


@dataclass
class CheckContext:
    """
    检查上下文 - 验证器的输入数据

    为什么用 dataclass？
    - 自动生成 __init__、__repr__ 等方法
    - 类型提示清晰
    - 方便扩展新参数
    - 验证器之间可以共享上下文
    """
    annotations_dir: Optional["Path"] = None
    images_dir: Optional["Path"] = None
    classes: Optional[List[str]] = None
    image_extensions: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png"]
    )
    min_files_count: int = 1
    extra: Dict[str, Any] = field(default_factory=dict)

    def get_xml_files(self) -> List["Path"]:
        """获取所有 XML 标注文件"""
        if self.annotations_dir and self.annotations_dir.exists():
            return list(self.annotations_dir.glob("*.xml"))
        return []

    def get_image_files(self) -> Set[str]:
        """获取所有图片文件的基础名（不含扩展名）"""
        if not self.images_dir or not self.images_dir.exists():
            return set()
        
        image_files = set()
        for ext in self.image_extensions:
            image_files.update({f.stem for f in self.images_dir.glob(f"*{ext}")})
        return image_files


class ValidationReport:
    """
    验证报告 - 收集和展示验证结果
    """

    def __init__(self):
        self.results: List[CheckResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def add_result(self, result: CheckResult):
        """添加检查结果"""
        self.results.append(result)

    def add_results(self, results: List[CheckResult]):
        """批量添加检查结果"""
        self.results.extend(results)

    @property
    def passed(self) -> bool:
        """是否有任何 ERROR 级别的问题"""
        return not any(r.level == CheckLevel.ERROR for r in self.results)

    @property
    def error_count(self) -> int:
        """ERROR 级别结果数量"""
        return sum(1 for r in self.results if r.level == CheckLevel.ERROR)

    @property
    def warning_count(self) -> int:
        """WARNING 级别结果数量"""
        return sum(1 for r in self.results if r.level == CheckLevel.WARNING)

    @property
    def info_count(self) -> int:
        """INFO 级别结果数量"""
        return sum(1 for r in self.results if r.level == CheckLevel.INFO)

    @property
    def pass_count(self) -> int:
        """PASS 级别结果数量"""
        return sum(1 for r in self.results if r.level == CheckLevel.PASS)

    def get_blocking_errors(self) -> List[CheckResult]:
        """获取所有阻断性错误"""
        return [r for r in self.results if r.is_blocking()]

    def get_results_by_level(self, level: CheckLevel) -> List[CheckResult]:
        """按级别筛选结果"""
        return [r for r in self.results if r.level == level]

    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("数据验证报告")
        print("=" * 60)
        
        for result in self.results:
            print(result)
        
        print("-" * 60)
        print(f"总计: {self.pass_count} 通过, {self.warning_count} 警告, {self.error_count} 错误")
        print("=" * 60)

    def __str__(self):
        lines = []
        lines.append("=" * 60)
        lines.append("数据验证报告")
        lines.append("=" * 60)
        
        for result in self.results:
            lines.append(str(result))
        
        lines.append("-" * 60)
        lines.append(f"总计: {self.pass_count} 通过, {self.warning_count} 警告, {self.error_count} 错误")
        lines.append("=" * 60)
        return "\n".join(lines)


_validators: Dict[str, Callable] = {}


def register_validator(name: str):
    """
    验证器装饰器

    使用方式：
        @register_validator("my_check")
        def check_something(ctx):
            return [CheckResult(...)]

    工作原理：
    1. 被装饰的函数会被注册到 _validators 字典
    2. 字典的 key 是验证器名称，value 是验证函数
    3. 调用 run_validators() 时会根据名称查找并执行

    优势：
    - 验证器定义和使用分离
    - 新增验证器不需要修改框架代码
    - 可以动态控制哪些验证器被使用
    """
    def decorator(func: Callable):
        _validators[name] = func
        func._validator_name = name
        return func
    return decorator


def get_validator(name: str) -> Optional[Callable]:
    """获取指定名称的验证器"""
    return _validators.get(name)


def list_validators() -> List[str]:
    """列出所有已注册的验证器名称"""
    return list(_validators.keys())


def run_validators(context: CheckContext, validator_names: Optional[List[str]] = None) -> List[CheckResult]:
    """
    运行验证器

    参数：
        context: 检查上下文
        validator_names: 指定运行的验证器列表
                        None 表示运行所有注册的验证器

    返回：
        List[CheckResult]: 所有检查结果
    """
    results = []
    names = validator_names if validator_names is not None else list_validators()

    for name in names:
        validator = get_validator(name)
        if validator:
            try:
                check_results = validator(context)
                for r in check_results:
                    if not r.check_name:
                        r.check_name = name
                results.extend(check_results)
            except Exception as e:
                results.append(CheckResult(
                    level=CheckLevel.ERROR,
                    message=f"验证器执行失败: {str(e)}",
                    check_name=name
                ))

    return results


@register_validator("directories_exist")
def check_directories(ctx: CheckContext) -> List[CheckResult]:
    """
    检查必要目录是否存在

    这个验证器检查：
    1. 标注目录是否存在
    2. 图片目录是否存在
    """
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
    """
    检查标注文件

    这个验证器：
    1. 查找 XML 标注文件
    2. 报告找到的数量
    3. 如果没有找到，报告 ERROR
    """
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


@register_validator("image_annotation_match")
def check_image_annotation_match(ctx: CheckContext) -> List[CheckResult]:
    """
    检查图片和标注文件是否匹配

    这个验证器找出：
    1. 有标注但无对应图片的文件
    2. 有图片但无对应标注的文件

    为什么是 WARNING 而不是 ERROR？
    - 缺少部分文件不影响整体转换
    - 可能是正常的测试数据或预留数据
    - 用户可能需要这些信息来决定如何处理
    """
    results = []

    if not ctx.annotations_dir or not ctx.images_dir:
        return results

    xml_files = {f.stem for f in ctx.annotations_dir.glob("*.xml")}
    image_files = ctx.get_image_files()

    missing_images = xml_files - image_files
    if missing_images:
        missing_list = list(missing_images)[:10]
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_images)} 个标注文件缺少对应图片",
            details={"missing": missing_list, "total": len(missing_images)}
        ))

    missing_annotations = image_files - xml_files
    if missing_annotations:
        missing_list = list(missing_annotations)[:10]
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_annotations)} 个图片缺少对应标注",
            details={"missing": missing_list, "total": len(missing_annotations)}
        ))

    if not missing_images and not missing_annotations:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"图片和标注文件完全匹配，共 {len(xml_files & image_files)} 对"
        ))

    return results


@register_validator("class_validation")
def check_classes(ctx: CheckContext) -> List[CheckResult]:
    """
    检查标注中的类别是否有效

    这个验证器：
    1. 从 XML 文件中提取所有类别名
    2. 与期望的类别列表对比
    3. 报告发现的未知类别
    """
    results = []

    if not ctx.annotations_dir or not ctx.classes:
        return results

    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        results.append(CheckResult(
            level=CheckLevel.ERROR,
            message="无法导入 xml.etree.ElementTree 模块"
        ))
        return results

    classes_set = set(ctx.classes)
    found_classes = set()
    unknown_classes = set()
    invalid_files = []

    for xml_file in list(ctx.annotations_dir.glob("*.xml"))[:100]:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall("object"):
                name_elem = obj.find("name")
                if name_elem is not None and name_elem.text:
                    class_name = name_elem.text
                    found_classes.add(class_name)

                    if class_name not in classes_set:
                        unknown_classes.add(class_name)
        except Exception:
            invalid_files.append(xml_file.name)

    if found_classes:
        results.append(CheckResult(
            level=CheckLevel.INFO,
            message=f"数据集中发现的类别: {sorted(found_classes)}"
        ))

    if unknown_classes:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"发现未知类别: {sorted(unknown_classes)}"
        ))

    if invalid_files:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"无法解析的 XML 文件: {len(invalid_files)} 个"
        ))

    if not unknown_classes and not invalid_files:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message="类别验证通过"
        ))

    return results


@register_validator("file_count")
def check_file_count(ctx: CheckContext) -> List[CheckResult]:
    """
    检查文件数量是否满足最低要求
    """
    results = []

    xml_files = ctx.get_xml_files()
    image_count = len(ctx.get_image_files())

    if len(xml_files) < ctx.min_files_count:
        results.append(CheckResult(
            level=CheckLevel.ERROR,
            message=f"标注文件数量不足: 找到 {len(xml_files)} 个，需要至少 {ctx.min_files_count} 个"
        ))
    else:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"标注文件数量满足要求: {len(xml_files)} 个"
        ))

    return results


class DataValidator:
    """
    数据验证器主类

    使用示例：
        context = CheckContext(
            annotations_dir=Paths.rsod_annotations(),
            images_dir=Paths.rsod_images(),
            classes=["aircraft", "oiltank", "overpass", "playground"]
        )
        
        validator = DataValidator(context)
        report = validator.validate()
        
        if not report.passed:
            print(report)
            return False
    """

    def __init__(self, context: CheckContext, validators: Optional[List[str]] = None):
        """
        初始化验证器

        参数：
            context: 检查上下文
            validators: 指定运行的验证器列表，None 表示运行所有
        """
        self.context = context
        self.validator_names = validators

    def validate(self) -> ValidationReport:
        """
        执行验证并返回报告
        """
        report = ValidationReport()
        results = run_validators(self.context, self.validator_names)
        report.add_results(results)
        return report

    def validate_and_report(self, verbose: bool = True) -> bool:
        """
        执行验证并打印报告

        参数：
            verbose: 是否打印详细报告

        返回：
            bool: 是否通过所有验证（没有 ERROR 级别问题）
        """
        report = self.validate()
        
        if verbose:
            report.print_report()
        
        return report.passed
