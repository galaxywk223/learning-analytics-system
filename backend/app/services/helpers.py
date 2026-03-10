"""
辅助函数模块
"""

import re
import numpy as np
from datetime import date, datetime, timedelta


def _coerce_to_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def get_custom_week_window(log_date, start_date):
    """
    根据阶段起始日期计算所属周窗口。

    规则:
    - 若阶段从周一开始，则按完整自然周(周一到周日)划分。
    - 若阶段从周中开始，则第一周为 start_date 到当周周日。
    - 第二周起固定按周一到周日划分。

    返回:
        tuple[date, date, int, int]: (week_start, week_end, year, week_num)
    """
    log_date = _coerce_to_date(log_date)
    start_date = _coerce_to_date(start_date)

    if log_date < start_date:
        first_week_end = start_date + timedelta(days=(6 - start_date.weekday()) % 7)
        return start_date, first_week_end, start_date.year, 1

    if start_date.weekday() == 0:
        days_diff = (log_date - start_date).days
        week_num = (days_diff // 7) + 1
        week_start = start_date + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end, week_start.year, week_num

    first_week_end = start_date + timedelta(days=6 - start_date.weekday())
    if log_date <= first_week_end:
        return start_date, first_week_end, start_date.year, 1

    first_full_week_start = first_week_end + timedelta(days=1)
    weeks_after_first = (log_date - first_full_week_start).days // 7
    week_num = weeks_after_first + 2
    week_start = first_full_week_start + timedelta(weeks=weeks_after_first)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end, week_start.year, week_num


def get_custom_week_info(log_date, start_date):
    """
    根据自定义起始日期计算周信息

    参数:
        log_date: 日志日期
        start_date: 起始日期(通常是第一个阶段的开始日期)

    返回:
        tuple: (年份, 周数)
    """
    _, _, year, week_num = get_custom_week_window(log_date, start_date)
    return year, week_num


def parse_csv_duration(duration_str):
    """
    解析CSV中的时长字符串

    支持格式:
    - "2h" -> 120分钟
    - "90min" -> 90分钟
    - "上课" -> 90分钟
    - "1.5" -> 90分钟(假设单位是小时)
    """
    if not isinstance(duration_str, str) or not duration_str.strip():
        return 0
    duration_str = duration_str.strip().lower()
    try:
        if "h" in duration_str:
            return int(float(duration_str.replace("h", "")) * 60)
        if "min" in duration_str:
            return int(float(duration_str.replace("min", "")))
        if "上课" in duration_str:
            return 90
        return int(float(duration_str) * 60)
    except (ValueError, TypeError):
        return 0


def parse_csv_date(date_str):
    """
    解析CSV中的日期字符串

    支持格式: "1月15日" -> date(当前年, 1, 15)
    """
    if not isinstance(date_str, str):
        return None
    try:
        parts = date_str.replace("月", "-").replace("日", "").split("-")
        return date(datetime.now().year, int(parts[0]), int(parts[1]))
    except (ValueError, IndexError, TypeError):
        return None


def parse_efficiency_to_numeric(eff_str):
    """
    将各种格式的效率描述转换为0-5的数值

    支持格式:
    - "4/5" -> 4.0
    - "80%" -> 4.0
    - "4.5" -> 4.5
    - "高效" -> 5.0
    - "一般" -> 3.0
    - "较差" -> 2.0

    返回 np.nan 表示缺失值
    """
    if not isinstance(eff_str, str) or not eff_str.strip():
        return np.nan

    eff_str = eff_str.strip()

    # 处理分数格式: 4/5
    match = re.match(r"(\d+\.?\d*)\s*/\s*(\d+\.?\d*)", eff_str)
    if match:
        num, den = float(match.group(1)), float(match.group(2))
        return (num / den) * 5 if den != 0 else np.nan

    # 处理百分比格式: 80%
    match = re.match(r"(\d+\.?\d*)\s*%", eff_str)
    if match:
        return (float(match.group(1)) / 100) * 5

    # 处理纯数字格式: 4.5
    match = re.match(r"(\d+\.?\d*)", eff_str)
    if match:
        val = float(match.group(1))
        return val if 0 <= val <= 5 else np.nan

    # 处理文字描述
    mapping = {
        "高效": 5,
        "良好": 4,
        "不错": 4,
        "一般": 3,
        "还行": 3,
        "及格": 3,
        "较差": 2,
        "差": 2,
        "很差": 1,
        "低效": 1,
    }
    return float(mapping.get(eff_str, np.nan))


def moving_average(data, window_size=7):
    """
    计算移动平均值，正确地忽略 NaN 值

    参数:
        data: 数据数组
        window_size: 窗口大小,默认7

    返回:
        numpy.array: 移动平均值数组
    """
    if len(data) < window_size:
        return np.array([])

    result = []
    for i in range(len(data) - window_size + 1):
        window = data[i : i + window_size]
        valid_values = window[~np.isnan(window)]

        if len(valid_values) > 0:
            result.append(np.mean(valid_values))
        else:
            result.append(np.nan)

    return np.array(result)


def format_duration(minutes):
    """
    将分钟数格式化为易读的字符串

    参数:
        minutes: 分钟数

    返回:
        str: 格式化后的字符串,如"2h 30min"或"45min"
    """
    if minutes is None or minutes == 0:
        return "0min"

    hours = minutes // 60
    mins = minutes % 60

    if hours > 0 and mins > 0:
        return f"{hours}h {mins}min"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}min"


def mood_emoji(mood_level):
    """
    将心情等级转换为表情符号

    参数:
        mood_level: 心情等级(1-5)

    返回:
        str: 对应的表情符号
    """
    emoji_map = {
        5: "😃",  # 非常好
        4: "😊",  # 良好
        3: "😐",  # 一般
        2: "😟",  # 不佳
        1: "😠",  # 很差
    }
    return emoji_map.get(mood_level, "🤔")
