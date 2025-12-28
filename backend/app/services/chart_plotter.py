"""
图表绘制服务
使用matplotlib生成学习统计图表
"""

import io
from typing import cast, Sequence
import matplotlib

matplotlib.use("Agg")  # 使用非GUI后端
import matplotlib.pyplot as plt
import numpy as np

# 配置matplotlib中文显示
plt.style.use("seaborn-v0_8-whitegrid")
try:
    plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    print(
        "Warning: Chinese font 'SimHei' not found. Chart labels may not render correctly."
    )

# 图表颜色配置
COLORS = {
    "duration_bar": (96 / 255, 165 / 255, 250 / 255, 0.6),
    "duration_line": "#2563EB",
    "efficiency_bar": (248 / 255, 113 / 255, 113 / 255, 0.6),
    "efficiency_line": "#B91C1C",
    "category_palette": [
        "#60A5FA",
        "#F87171",
        "#FBBF24",
        "#4ADE80",
        "#A78BFA",
        "#2DD4BF",
        "#F472B6",
        "#818CF8",
    ],
}


def _plot_weekly_duration(ax, data):
    """在给定的 Axes 上绘制每周学习时长图"""
    ax.bar(
        data["labels"],
        data["actuals"],
        label="平均时长 (小时/天)",
        color=COLORS["duration_bar"],
        width=0.6,
    )

    trends_y = np.array(data["trends"], dtype=float)
    trends_x = np.arange(len(data["labels"]))
    valid_mask = ~np.isnan(trends_y)

    ax.plot(
        trends_x[valid_mask],
        trends_y[valid_mask],
        label="趋势线 (3周)",
        color=COLORS["duration_line"],
        marker="o",
        markersize=4,
        linewidth=2.5,
    )

    ax.set_title("每周平均学习时长", fontsize=16, weight="bold")
    ax.tick_params(axis="x", rotation=45, labelsize=10)
    ax.legend()


def _plot_weekly_efficiency(ax, data):
    """在给定的 Axes 上绘制每周学习效率图"""
    eff_y = np.array(data["actuals"], dtype=float)
    eff_x_labels = data["labels"]
    valid_eff_mask = ~np.isnan(eff_y)

    ax.bar(
        np.array(eff_x_labels)[valid_eff_mask],
        eff_y[valid_eff_mask],
        label="实际效率",
        color=COLORS["efficiency_bar"],
        width=0.6,
    )

    trends_eff_y = np.array(data["trends"], dtype=float)
    trends_eff_x = np.arange(len(eff_x_labels))
    valid_trends_mask = ~np.isnan(trends_eff_y)

    ax.plot(
        trends_eff_x[valid_trends_mask],
        trends_eff_y[valid_trends_mask],
        label="趋势线 (3周)",
        color=COLORS["efficiency_line"],
        marker="o",
        markersize=4,
        linewidth=2.5,
    )

    ax.set_title("每周学习效率", fontsize=16, weight="bold")
    ax.tick_params(axis="x", rotation=45, labelsize=10)
    ax.legend()


def _plot_daily_duration(ax, data):
    """在给定的 Axes 上绘制每日学习时长图"""
    ax.plot(
        data["labels"],
        data["actuals"],
        label="实际时长 (小时)",
        color=COLORS["duration_line"],
        alpha=0.5,
    )

    daily_trends_y = np.array(data["trends"], dtype=float)
    daily_trends_x = np.arange(len(data["labels"]))
    valid_daily_mask = ~np.isnan(daily_trends_y)

    ax.plot(
        daily_trends_x[valid_daily_mask],
        daily_trends_y[valid_daily_mask],
        label="趋势线 (7日)",
        color=COLORS["duration_line"],
        linewidth=2.5,
    )

    ax.set_title("每日学习时长", fontsize=16, weight="bold")
    ax.set_xticks([])
    ax.legend()


def _plot_daily_efficiency(ax, data):
    """在给定的 Axes 上绘制每日学习效率图"""
    ax.plot(
        data["labels"],
        data["actuals"],
        label="实际效率",
        color=COLORS["efficiency_line"],
        alpha=0.5,
    )

    daily_eff_y = np.array(data["trends"], dtype=float)
    daily_eff_x = np.arange(len(data["labels"]))
    valid_daily_eff_mask = ~np.isnan(daily_eff_y)

    ax.plot(
        daily_eff_x[valid_daily_eff_mask],
        daily_eff_y[valid_daily_eff_mask],
        label="趋势线 (7日)",
        color=COLORS["efficiency_line"],
        linewidth=2.5,
    )

    ax.set_title("每日学习效率", fontsize=16, weight="bold")
    ax.set_xticks([])
    ax.legend()


def export_trends_image(username, trend_data):
    """
    根据传入的趋势数据,生成并返回趋势图表的图片缓冲

    Args:
        username: 用户名,用于图表标题
        trend_data: 从 chart_service 获取的数据

    Returns:
        BytesIO: 包含 PNG 图片的缓冲区, 如果失败返回None
    """
    if not trend_data.get("has_data"):
        return None

    try:
        fig, axes = plt.subplots(2, 2, figsize=(20, 14), dpi=120)
        fig.suptitle(f"{username} 的学习趋势总览", fontsize=24, weight="bold", y=0.98)

        _plot_weekly_duration(axes[0, 0], trend_data["weekly_duration_data"])
        _plot_weekly_efficiency(axes[0, 1], trend_data["weekly_efficiency_data"])
        _plot_daily_duration(axes[1, 0], trend_data["daily_duration_data"])
        _plot_daily_efficiency(axes[1, 1], trend_data["daily_efficiency_data"])

        fig.tight_layout(rect=(0, 0.03, 1, 0.95))

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer
    except Exception as e:
        plt.close("all")
        raise e


def export_category_image(username, category_data):
    """
    根据传入的分类数据,生成并返回分类图表的图片缓冲

    Args:
        username: 用户名,用于图表标题
        category_data: 从 chart_service 获取的数据

    Returns:
        BytesIO: 包含 PNG 图片的缓冲区
    """
    try:
        if not category_data or not category_data["main"]["labels"]:
            # 没有数据时显示提示
            fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
            ax.text(
                0.5,
                0.5,
                "没有可用于导出的分类数据",
                ha="center",
                va="center",
                fontsize=18,
            )
            ax.axis("off")
        else:
            # 计算图表高度
            num_sub_charts = len(category_data["drilldown"])
            figure_height = 8 + (num_sub_charts * 4)

            fig = plt.figure(figsize=(12, figure_height), dpi=120)
            gs = fig.add_gridspec(
                num_sub_charts + 1, 1, height_ratios=[4] + [2] * num_sub_charts
            )
            fig.suptitle(f"{username} 的学习分类总览", fontsize=24, weight="bold")

            # 绘制主分类饼图
            main_cat_ax = fig.add_subplot(gs[0, 0])
            main_data = category_data["main"]

            pie_result = main_cat_ax.pie(
                main_data["data"],
                labels=main_data["labels"],
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.85,
                colors=cast(Sequence[str], COLORS["category_palette"]),
                wedgeprops=dict(width=0.4, edgecolor="w"),
            )
            autotexts = pie_result[2] if len(pie_result) > 2 else []  # type: ignore[index]

            plt.setp(autotexts, size=10, weight="bold", color="white")
            main_cat_ax.set_title("主分类时长占比", fontsize=16, weight="bold", pad=20)
            main_cat_ax.axis("equal")

            # 绘制子分类柱状图
            sorted_main_categories = category_data["main"]["labels"]
            for i, cat_name in enumerate(sorted_main_categories):
                sub_data = category_data["drilldown"].get(cat_name)
                if not sub_data or not sub_data["labels"]:
                    continue

                sub_ax = fig.add_subplot(gs[i + 1, 0])
                bar_color = COLORS["category_palette"][
                    i % len(COLORS["category_palette"])
                ]

                sub_ax.barh(
                    sub_data["labels"], sub_data["data"], color=bar_color, height=0.5
                )

                sub_ax.set_title(
                    f'"{cat_name}" 分类下的标签详情 (小时)', fontsize=14, weight="bold"
                )
                sub_ax.invert_yaxis()

                # 添加数值标签
                for index, value in enumerate(sub_data["data"]):
                    sub_ax.text(
                        value, index, f" {value:.1f}h", va="center", fontsize=10
                    )

                # 隐藏不必要的边框
                sub_ax.spines["top"].set_visible(False)
                sub_ax.spines["right"].set_visible(False)
                sub_ax.spines["left"].set_visible(False)

        fig.tight_layout(rect=(0, 0.03, 1, 0.96))

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer
    except Exception as e:
        plt.close("all")
        raise e
