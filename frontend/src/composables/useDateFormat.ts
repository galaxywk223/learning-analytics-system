/**
 * 日期处理组合式函数
 * 基于 dayjs 的常用日期操作
 */
import dayjs from "dayjs";

export function useDateFormat() {
  /**
   * 格式化日期
   * @param {string|Date} date - 日期
   * @param {string} format - 格式模板，默认 'YYYY-MM-DD'
   */
  const formatDate = (date, format = "YYYY-MM-DD") => {
    if (!date) return "";
    return dayjs(date).format(format);
  };

  /**
   * 格式化日期时间
   * @param {string|Date} date - 日期时间
   */
  const formatDateTime = (date) => {
    return formatDate(date, "YYYY-MM-DD HH:mm:ss");
  };

  /**
   * 格式化相对时间（多久之前）
   * @param {string|Date} date - 日期
   */
  const formatRelativeTime = (date) => {
    if (!date) return "";
    const now = dayjs();
    const target = dayjs(date);
    const diffDays = now.diff(target, "day");

    if (diffDays === 0) {
      const diffHours = now.diff(target, "hour");
      if (diffHours === 0) {
        const diffMinutes = now.diff(target, "minute");
        return diffMinutes <= 0 ? "刚刚" : `${diffMinutes}分钟前`;
      }
      return `${diffHours}小时前`;
    } else if (diffDays === 1) {
      return "昨天";
    } else if (diffDays === 2) {
      return "前天";
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return formatDate(date);
    }
  };

  /**
   * 获取日期范围
   * @param {string} type - 类型：today, week, month, year
   */
  const getDateRange = (type) => {
    const now = dayjs();
    let start, end;

    switch (type) {
      case "today":
        start = now.startOf("day");
        end = now.endOf("day");
        break;
      case "week":
        start = now.startOf("week");
        end = now.endOf("week");
        break;
      case "month":
        start = now.startOf("month");
        end = now.endOf("month");
        break;
      case "year":
        start = now.startOf("year");
        end = now.endOf("year");
        break;
      default:
        start = now.startOf("day");
        end = now.endOf("day");
    }

    return {
      start: start.format("YYYY-MM-DD"),
      end: end.format("YYYY-MM-DD"),
    };
  };

  /**
   * 计算两个日期之间的天数差
   */
  const daysBetween = (date1, date2) => {
    return dayjs(date2).diff(dayjs(date1), "day");
  };

  /**
   * 判断日期是否为今天
   */
  const isToday = (date) => {
    return dayjs(date).isSame(dayjs(), "day");
  };

  return {
    formatDate,
    formatDateTime,
    formatRelativeTime,
    getDateRange,
    daysBetween,
    isToday,
  };
}
