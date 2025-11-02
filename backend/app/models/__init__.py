"""
数据库模型
统一导入所有模型以保持兼容性
"""

# 导入基础模型
from .base import User, Setting

# 导入学习相关模型
from .learning import Stage, Category, SubCategory, LogEntry

# 导入数据分析模型
from .analytics import WeeklyData, DailyData

# 导入应用功能模型
from .features import CountdownEvent, Motto, Todo

# 导入里程碑模型
from .milestones import MilestoneCategory, Milestone, MilestoneAttachment

# 导入日程计划模型
from .planning import DailyPlanItem

# 导出所有模型，保持向后兼容性
__all__ = [
    # 基础模型
    "User",
    "Setting",
    # 学习相关模型
    "Stage",
    "Category",
    "SubCategory",
    "LogEntry",
    # 数据分析模型
    "WeeklyData",
    "DailyData",
    # 应用功能模型
    "CountdownEvent",
    "Motto",
    "Todo",
    # 里程碑模型
    "MilestoneCategory",
    "Milestone",
    "MilestoneAttachment",
    # 日程计划模型
    "DailyPlanItem",
]
