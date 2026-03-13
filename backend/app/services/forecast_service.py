"""趋势预测服务。

为图表概览接口生成日/周的未来预测结果，包含：
- 候选模型回测选优
- 点预测
- 基于残差分位数的 80% 置信区间
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Sequence

import numpy as np

from .helpers import get_custom_week_info

try:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - 由运行环境决定
    HistGradientBoostingClassifier = None
    HistGradientBoostingRegressor = None
    Ridge = None
    Pipeline = None
    StandardScaler = None
    SKLEARN_AVAILABLE = False

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    STATSMODELS_AVAILABLE = True
except Exception:  # pragma: no cover - 由运行环境决定
    ExponentialSmoothing = None
    STATSMODELS_AVAILABLE = False


UNAVAILABLE_REASON = "历史数据不足，暂不提供预测"
DEPENDENCY_REASON = "预测依赖未安装，暂不提供预测"
MODEL_FAILURE_REASON = "预测模型训练失败，暂不提供预测"
LOW_CONFIDENCE_REASON = "历史回测误差较高，暂不显示预测"
CONFIDENCE_LEVEL = 0.8
ACCURACY_GATE_WAPE = 0.4
MODEL_SELECTION_STRATEGY = "lowest_wape_then_rmse_with_weighted_blend"


@dataclass(frozen=True)
class ForecastConfig:
    frequency: str
    horizon: int
    min_history: int
    season_length: int
    validation_window: int
    lag_features: tuple[int, ...]
    rolling_windows: tuple[int, ...]
    slope_window: int


DAILY_CONFIG = ForecastConfig(
    frequency="daily",
    horizon=14,
    min_history=28,
    season_length=7,
    validation_window=28,
    lag_features=(1, 7, 14, 28),
    rolling_windows=(7, 14, 28),
    slope_window=7,
)

WEEKLY_CONFIG = ForecastConfig(
    frequency="weekly",
    horizon=8,
    min_history=12,
    season_length=4,
    validation_window=8,
    lag_features=(1, 2, 4, 8),
    rolling_windows=(4, 8),
    slope_window=4,
)


def _empty_forecast(
    *,
    labels: Sequence[str] | None = None,
    horizon: int,
    history_points: int,
    reason: str,
    model_name: str | None = None,
    validation_wape: float | None = None,
    validation_rmse: float | None = None,
    baseline_wape: float | None = None,
    baseline_rmse: float | None = None,
    model_candidates: Sequence[dict] | None = None,
) -> dict:
    return {
        "labels": list(labels or []),
        "prediction": [],
        "lower": [],
        "upper": [],
        "model_name": model_name,
        "history_points": history_points,
        "horizon": horizon,
        "trained_on": "all_history",
        "confidence_level": CONFIDENCE_LEVEL,
        "accuracy_threshold": ACCURACY_GATE_WAPE,
        "selection_strategy": MODEL_SELECTION_STRATEGY,
        "validation_wape": _round_metric(validation_wape),
        "validation_rmse": _round_metric(validation_rmse),
        "baseline_wape": _round_metric(baseline_wape),
        "baseline_rmse": _round_metric(baseline_rmse),
        "model_candidates": list(model_candidates or []),
        "available": False,
        "reason": reason,
    }


def _round_series(values: Sequence[float]) -> list[float]:
    return [round(float(v), 2) for v in values]


def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if not np.isfinite(numeric):
        return None
    return round(numeric, 4)


def _is_finite_metric(value: float | None) -> bool:
    if value is None:
        return False
    return bool(np.isfinite(float(value)))


def _wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denominator = float(np.sum(np.abs(actual)))
    numerator = float(np.sum(np.abs(actual - predicted)))
    if denominator <= 1e-8:
        return numerator / max(len(actual), 1)
    return numerator / denominator


def _rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(actual - predicted))))


def _compute_slope(values: np.ndarray) -> float:
    if len(values) <= 1:
        return 0.0
    x_axis = np.arange(len(values), dtype=float)
    x_mean = float(np.mean(x_axis))
    y_mean = float(np.mean(values))
    denominator = float(np.sum((x_axis - x_mean) ** 2))
    if denominator <= 1e-8:
        return 0.0
    numerator = float(np.sum((x_axis - x_mean) * (values - y_mean)))
    return numerator / denominator


def _seasonal_reference_values(
    history: np.ndarray,
    target_index: int,
    season_length: int,
    *,
    max_periods: int = 4,
) -> np.ndarray:
    references: list[float] = []
    for period in range(1, max_periods + 1):
        ref_index = target_index - (season_length * period)
        if ref_index < 0:
            break
        references.append(float(history[ref_index]))
    if not references:
        return np.asarray([0.0], dtype=float)
    return np.asarray(references, dtype=float)


def _calendar_features(index: int, config: ForecastConfig) -> list[float]:
    if config.frequency == "daily":
        day_slot = index % 7
        return [1.0 if i == day_slot else 0.0 for i in range(7)]
    week_slot = index % config.season_length
    return [1.0 if i == week_slot else 0.0 for i in range(config.season_length)]


def _normalize_exog_matrix(exog_values) -> np.ndarray | None:
    if exog_values is None:
        return None
    exog_array = np.asarray(exog_values, dtype=float)
    if exog_array.size == 0:
        return None
    if exog_array.ndim == 1:
        return exog_array.reshape(-1, 1)
    return exog_array


def _combine_exog_columns(*columns) -> list[list[float]] | None:
    matrices = [_normalize_exog_matrix(column) for column in columns if column is not None]
    matrices = [matrix for matrix in matrices if matrix is not None]
    if not matrices:
        return None
    expected_length = matrices[0].shape[0]
    for matrix in matrices:
        if matrix.shape[0] != expected_length:
            raise ValueError("exogenous feature length mismatch")
    return np.hstack(matrices).tolist()


def _extend_exog_matrix(
    exog_history,
    future_exog,
    horizon: int,
) -> np.ndarray | None:
    history_matrix = _normalize_exog_matrix(exog_history)
    if history_matrix is None:
        return None

    future_matrix = _normalize_exog_matrix(future_exog)
    feature_count = history_matrix.shape[1]
    if future_matrix is None:
        future_matrix = np.repeat(history_matrix[-1:].copy(), horizon, axis=0)
    elif future_matrix.shape[1] != feature_count:
        raise ValueError("exogenous feature dimension mismatch")
    elif len(future_matrix) < horizon:
        fill_row = future_matrix[-1] if len(future_matrix) else history_matrix[-1]
        extension = np.repeat(fill_row.reshape(1, -1), horizon - len(future_matrix), axis=0)
        future_matrix = np.vstack([future_matrix, extension])

    return np.vstack([history_matrix, future_matrix[:horizon]])


def _build_feature_row(
    target_history: Sequence[float],
    target_index: int,
    config: ForecastConfig,
    exog_values=None,
) -> np.ndarray:
    target_array = np.asarray(target_history, dtype=float)
    feature_row: list[float] = []

    for lag in config.lag_features:
        feature_row.append(float(target_array[target_index - lag]))

    for window in config.rolling_windows:
        window_slice = target_array[target_index - window : target_index]
        feature_row.append(float(np.mean(window_slice)))
        feature_row.append(float(np.std(window_slice)))
        feature_row.append(float(np.max(window_slice)))
        feature_row.append(float(np.min(window_slice)))

    slope_slice = target_array[target_index - config.slope_window : target_index]
    feature_row.append(_compute_slope(np.asarray(slope_slice, dtype=float)))
    seasonal_refs = _seasonal_reference_values(
        target_array,
        target_index,
        config.season_length,
    )
    feature_row.append(float(np.mean(seasonal_refs)))
    feature_row.append(float(np.std(seasonal_refs)))
    feature_row.append(float(seasonal_refs[0]))
    active_threshold = 0.25 if config.frequency == "daily" else 1.0
    recent_activity_slice = target_array[
        max(0, target_index - config.season_length) : target_index
    ]
    if len(recent_activity_slice):
        feature_row.append(
            float(np.mean((recent_activity_slice > active_threshold).astype(float)))
        )
    else:
        feature_row.append(0.0)
    feature_row.extend(_calendar_features(target_index, config))

    if exog_values is not None:
        exog_array = _normalize_exog_matrix(exog_values)
        if exog_array is not None:
            for column_index in range(exog_array.shape[1]):
                column = exog_array[:, column_index]
                feature_row.append(float(column[target_index]))
                feature_row.append(float(column[target_index - 1]))
                for window in config.rolling_windows:
                    window_slice = column[target_index - window : target_index]
                    feature_row.append(float(np.mean(window_slice)))
                    feature_row.append(float(np.std(window_slice)))

    return np.asarray(feature_row, dtype=float)


def _build_supervised_dataset(
    series: Sequence[float],
    config: ForecastConfig,
    exog_values=None,
) -> tuple[np.ndarray, np.ndarray]:
    history = np.asarray(series, dtype=float)
    max_lookback = max(
        max(config.lag_features),
        max(config.rolling_windows),
        config.slope_window,
    )
    rows: list[np.ndarray] = []
    targets: list[float] = []
    for index in range(max_lookback, len(history)):
        rows.append(_build_feature_row(history, index, config, exog_values))
        targets.append(float(history[index]))

    if not rows:
        return np.empty((0, 0), dtype=float), np.empty((0,), dtype=float)
    return np.vstack(rows), np.asarray(targets, dtype=float)


def _build_sample_weights(size: int) -> np.ndarray:
    if size <= 0:
        return np.empty((0,), dtype=float)
    if size == 1:
        return np.asarray([1.0], dtype=float)
    return np.linspace(0.7, 1.3, num=size, dtype=float)


def _predict_seasonal_naive(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    _future_exog: Sequence[float] | None = None,
    *,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    del exog_history
    history = np.asarray(series, dtype=float)
    season = config.season_length
    if len(history) < season:
        raise ValueError("insufficient history for seasonal naive")
    return np.asarray(
        [history[-season + ((step - 1) % season)] for step in range(1, horizon + 1)],
        dtype=float,
    )


def _build_seed_forecast(
    series: Sequence[float | None],
    config: ForecastConfig,
    horizon: int,
) -> np.ndarray:
    numeric_series = np.asarray(
        [0.0 if value is None else float(value) for value in series],
        dtype=float,
    )
    if len(numeric_series) == 0:
        return np.zeros(horizon, dtype=float)
    if len(numeric_series) >= config.season_length:
        return _predict_seasonal_naive(numeric_series, config, horizon)
    fill_value = float(numeric_series[-1])
    return np.asarray([fill_value] * horizon, dtype=float)


def _sanitize_exog_values(exog_values):
    exog_array = _normalize_exog_matrix(exog_values)
    if exog_array is None:
        return None
    return np.nan_to_num(exog_array, nan=0.0).tolist()


def _predict_holt_winters(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    _future_exog: Sequence[float] | None = None,
    *,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    del exog_history
    if not STATSMODELS_AVAILABLE:
        raise RuntimeError(DEPENDENCY_REASON)
    history = np.asarray(series, dtype=float)
    if len(history) < max(config.min_history, config.season_length * 2):
        raise ValueError("insufficient history for holt-winters")

    model = ExponentialSmoothing(
        history,
        trend="add",
        seasonal="add",
        seasonal_periods=config.season_length,
        initialization_method="estimated",
    )
    fitted = model.fit(optimized=True, use_brute=False)
    return np.asarray(fitted.forecast(horizon), dtype=float)


def _predict_ridge_autoregression(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    future_exog: Sequence[float] | None = None,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    if not SKLEARN_AVAILABLE:
        raise RuntimeError(DEPENDENCY_REASON)

    x_train, y_train = _build_supervised_dataset(series, config, exog_history)
    if len(y_train) < max(config.min_history // 2, 8):
        raise ValueError("insufficient training rows for ridge autoregression")

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.2)),
        ]
    )
    sample_weights = _build_sample_weights(len(y_train))
    model.fit(x_train, y_train, ridge__sample_weight=sample_weights)

    history = [float(v) for v in series]
    exog_extended = _extend_exog_matrix(exog_history, future_exog, horizon)

    predictions: list[float] = []
    for _ in range(horizon):
        target_index = len(history)
        feature_row = _build_feature_row(history, target_index, config, exog_extended)
        predicted = float(model.predict(feature_row.reshape(1, -1))[0])
        predicted = max(predicted, 0.0)
        predictions.append(predicted)
        history.append(predicted)
    return np.asarray(predictions, dtype=float)


def _predict_hist_gradient_boosting_autoregression(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    future_exog: Sequence[float] | None = None,
    *,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    if not SKLEARN_AVAILABLE:
        raise RuntimeError(DEPENDENCY_REASON)

    x_train, y_train = _build_supervised_dataset(series, config, exog_history)
    if len(y_train) < max(config.min_history // 2, 10):
        raise ValueError("insufficient training rows for gradient boosting autoregression")

    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.08,
        max_depth=3,
        max_iter=60,
        min_samples_leaf=5,
        l2_regularization=0.08,
        random_state=42,
    )
    sample_weights = _build_sample_weights(len(y_train))
    model.fit(x_train, y_train, sample_weight=sample_weights)

    history = [float(v) for v in series]
    exog_extended = _extend_exog_matrix(exog_history, future_exog, horizon)

    predictions: list[float] = []
    for _ in range(horizon):
        target_index = len(history)
        feature_row = _build_feature_row(history, target_index, config, exog_extended)
        predicted = float(model.predict(feature_row.reshape(1, -1))[0])
        predictions.append(max(predicted, 0.0))
        history.append(max(predicted, 0.0))
    return np.asarray(predictions, dtype=float)


def _compute_duration_activity_threshold(
    target_values: Sequence[float],
    config: ForecastConfig,
) -> float:
    values = np.asarray(target_values, dtype=float)
    positive_floor = 0.25 if config.frequency == "daily" else 1.0
    positive_values = values[values > positive_floor]

    if config.frequency == "daily":
        reference = positive_values if len(positive_values) >= 8 else values
        if len(reference) == 0:
            return positive_floor
        return max(0.5, float(np.quantile(reference, 0.35)))

    reference = values if len(values) else np.asarray([7.0], dtype=float)
    return max(7.0, float(np.quantile(reference, 0.45)))


def _predict_two_stage_duration_autoregression(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    future_exog: Sequence[float] | None = None,
    *,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    if not SKLEARN_AVAILABLE:
        raise RuntimeError(DEPENDENCY_REASON)

    x_train, y_train = _build_supervised_dataset(series, config, exog_history)
    if len(y_train) < max(config.min_history // 2, 10):
        raise ValueError("insufficient training rows for two-stage duration autoregression")

    threshold = _compute_duration_activity_threshold(y_train, config)
    active_labels = (y_train >= threshold).astype(int)
    sample_weights = _build_sample_weights(len(y_train))
    active_rate = float(np.mean(active_labels))

    classifier = None
    if len(np.unique(active_labels)) > 1:
        classifier = HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_depth=3,
            max_iter=70,
            min_samples_leaf=5,
            l2_regularization=0.08,
            random_state=42,
        )
        classifier.fit(x_train, active_labels, sample_weight=sample_weights)

    active_mask = active_labels == 1
    regressor_x = x_train[active_mask]
    regressor_y = y_train[active_mask]
    regressor_weights = sample_weights[active_mask]
    if len(regressor_y) < 8:
        regressor_x = x_train
        regressor_y = y_train
        regressor_weights = sample_weights

    intensity_regressor = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.07,
        max_depth=3,
        max_iter=70,
        min_samples_leaf=5,
        l2_regularization=0.08,
        random_state=42,
    )
    intensity_regressor.fit(
        regressor_x,
        np.log1p(np.maximum(regressor_y, 0.0)),
        sample_weight=regressor_weights,
    )

    inactive_values = y_train[~active_mask]
    inactive_level = (
        float(np.median(inactive_values))
        if len(inactive_values)
        else min(threshold * 0.5, float(np.median(y_train)))
    )

    history = [float(v) for v in series]
    exog_extended = _extend_exog_matrix(exog_history, future_exog, horizon)

    predictions: list[float] = []
    for _ in range(horizon):
        target_index = len(history)
        feature_row = _build_feature_row(history, target_index, config, exog_extended)
        feature_matrix = feature_row.reshape(1, -1)
        if classifier is None:
            active_prob = active_rate
        else:
            active_prob = float(classifier.predict_proba(feature_matrix)[0][1])
        active_prob = float(np.clip(active_prob, 0.05, 0.98))
        active_prediction = max(
            float(np.expm1(intensity_regressor.predict(feature_matrix)[0])),
            0.0,
        )
        predicted = (active_prob * active_prediction) + (
            (1.0 - active_prob) * inactive_level
        )
        predicted = max(predicted, 0.0)
        predictions.append(predicted)
        history.append(predicted)

    return np.asarray(predictions, dtype=float)


def _predict_poisson_hist_gradient_boosting_autoregression(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    future_exog: Sequence[float] | None = None,
    *,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    if not SKLEARN_AVAILABLE:
        raise RuntimeError(DEPENDENCY_REASON)

    x_train, y_train = _build_supervised_dataset(series, config, exog_history)
    if len(y_train) < max(config.min_history // 2, 10):
        raise ValueError(
            "insufficient training rows for poisson gradient boosting autoregression"
        )

    model = HistGradientBoostingRegressor(
        loss="poisson",
        learning_rate=0.06,
        max_depth=3,
        max_iter=70,
        min_samples_leaf=5,
        l2_regularization=0.08,
        random_state=42,
    )
    sample_weights = _build_sample_weights(len(y_train))
    strictly_positive_y = np.maximum(y_train, 1e-4)
    model.fit(x_train, strictly_positive_y, sample_weight=sample_weights)

    history = [float(v) for v in series]
    exog_extended = _extend_exog_matrix(exog_history, future_exog, horizon)

    predictions: list[float] = []
    for _ in range(horizon):
        target_index = len(history)
        feature_row = _build_feature_row(history, target_index, config, exog_extended)
        predicted = float(model.predict(feature_row.reshape(1, -1))[0])
        predicted = max(predicted, 0.0)
        predictions.append(predicted)
        history.append(predicted)
    return np.asarray(predictions, dtype=float)


def _predict_log_hist_gradient_boosting_autoregression(
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    future_exog: Sequence[float] | None = None,
    *,
    exog_history: Sequence[float] | None = None,
) -> np.ndarray:
    if not SKLEARN_AVAILABLE:
        raise RuntimeError(DEPENDENCY_REASON)

    x_train, y_train = _build_supervised_dataset(series, config, exog_history)
    if len(y_train) < max(config.min_history // 2, 10):
        raise ValueError(
            "insufficient training rows for log gradient boosting autoregression"
        )

    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.08,
        max_depth=3,
        max_iter=80,
        min_samples_leaf=5,
        l2_regularization=0.08,
        random_state=42,
    )
    sample_weights = _build_sample_weights(len(y_train))
    transformed_y = np.log1p(np.maximum(y_train, 0.0))
    model.fit(x_train, transformed_y, sample_weight=sample_weights)

    history = [float(v) for v in series]
    exog_extended = _extend_exog_matrix(exog_history, future_exog, horizon)

    predictions: list[float] = []
    for _ in range(horizon):
        target_index = len(history)
        feature_row = _build_feature_row(history, target_index, config, exog_extended)
        predicted_log = float(model.predict(feature_row.reshape(1, -1))[0])
        predicted = max(float(np.expm1(predicted_log)), 0.0)
        predictions.append(predicted)
        history.append(predicted)
    return np.asarray(predictions, dtype=float)


def _available_model_predictors(
    *,
    include_nonlinear: bool,
    target_kind: str,
) -> tuple[tuple[str, Callable[..., np.ndarray]], ...]:
    recent_window_size = 56 if target_kind != "weekly" else 16
    predictors: list[tuple[str, Callable[..., np.ndarray]]] = [
        ("Seasonal Naive", _predict_seasonal_naive),
    ]
    if SKLEARN_AVAILABLE:
        predictors.append(("Ridge Autoregression", _predict_ridge_autoregression))
        predictors.append(
            (
                "Recent Ridge Autoregression",
                _build_recent_window_predictor(
                    _predict_ridge_autoregression,
                    window_size=recent_window_size,
                ),
            )
        )
        if include_nonlinear:
            if target_kind == "duration":
                predictors.append(
                    (
                        "Two-Stage Duration Autoregression",
                        _predict_two_stage_duration_autoregression,
                    )
                )
                predictors.append(
                    (
                        "Poisson-HistGradientBoosting Autoregression",
                        _predict_poisson_hist_gradient_boosting_autoregression,
                    )
                )
                predictors.append(
                    (
                        "Recent Poisson-HistGradientBoosting Autoregression",
                        _build_recent_window_predictor(
                            _predict_poisson_hist_gradient_boosting_autoregression,
                            window_size=recent_window_size,
                        ),
                    )
                )
            else:
                predictors.append(
                    (
                        "Log-HistGradientBoosting Autoregression",
                        _predict_log_hist_gradient_boosting_autoregression,
                    )
                )
                predictors.append(
                    (
                        "Recent Log-HistGradientBoosting Autoregression",
                        _build_recent_window_predictor(
                            _predict_log_hist_gradient_boosting_autoregression,
                            window_size=recent_window_size,
                        ),
                    )
                )
    return tuple(predictors)


def _run_predictor(
    model_name: str,
    predictor: Callable[..., np.ndarray],
    series: Sequence[float],
    config: ForecastConfig,
    horizon: int,
    *,
    exog_history: Sequence[float] | None = None,
    future_exog: Sequence[float] | None = None,
) -> np.ndarray:
    return predictor(
        series,
        config,
        horizon,
        future_exog,
        exog_history=exog_history,
    )


def _backtest_candidate(
    model_name: str,
    predictor: Callable[..., np.ndarray],
    series: Sequence[float],
    config: ForecastConfig,
    *,
    exog_history: Sequence[float] | None = None,
) -> tuple[float, float, dict[int, list[float]]]:
    target = np.asarray(series, dtype=float)
    if len(target) < config.min_history:
        raise ValueError("insufficient history for backtest")

    start_origin = max(config.min_history, len(target) - config.validation_window)
    actual_points: list[float] = []
    predicted_points: list[float] = []
    residuals_by_horizon: dict[int, list[float]] = {
        step: [] for step in range(1, config.horizon + 1)
    }

    for origin in range(start_origin, len(target)):
        train_series = target[:origin]
        steps = min(config.horizon, len(target) - origin)
        if steps <= 0:
            continue

        train_exog = None if exog_history is None else exog_history[:origin]
        future_exog = None if exog_history is None else exog_history[origin : origin + steps]

        prediction = _run_predictor(
            model_name,
            predictor,
            train_series,
            config,
            steps,
            exog_history=train_exog,
            future_exog=future_exog,
        )

        actual_slice = target[origin : origin + steps]
        actual_points.extend(actual_slice.tolist())
        predicted_points.extend(prediction.tolist())

        for step, (predicted, actual) in enumerate(zip(prediction, actual_slice), start=1):
            residuals_by_horizon[step].append(float(actual - predicted))

    if not actual_points:
        raise ValueError("backtest produced no predictions")

    actual_arr = np.asarray(actual_points, dtype=float)
    predicted_arr = np.asarray(predicted_points, dtype=float)
    return (
        _wape(actual_arr, predicted_arr),
        _rmse(actual_arr, predicted_arr),
        residuals_by_horizon,
    )


def _build_intervals(
    prediction: Sequence[float],
    residuals_by_horizon: dict[int, list[float]],
) -> tuple[list[float], list[float]]:
    lower: list[float] = []
    upper: list[float] = []
    aggregate_residuals = [
        residual
        for residuals in residuals_by_horizon.values()
        for residual in residuals
    ]

    for step, value in enumerate(prediction, start=1):
        residuals = residuals_by_horizon.get(step) or aggregate_residuals
        if residuals:
            lower_delta = float(np.quantile(residuals, 0.1))
            upper_delta = float(np.quantile(residuals, 0.9))
        else:
            lower_delta = 0.0
            upper_delta = 0.0

        low_value = max(float(value + lower_delta), 0.0)
        high_value = max(float(value + upper_delta), low_value)
        lower.append(round(low_value, 2))
        upper.append(round(high_value, 2))

    return lower, upper


def _serialize_candidates(
    candidate_results: Sequence[
        tuple[str, Callable[..., np.ndarray], float, float, dict[int, list[float]]]
    ],
    *,
    selected_name: str | None,
) -> list[dict]:
    ordered = sorted(candidate_results, key=lambda item: (item[2], item[3], item[0]))
    return [
        {
            "model_name": model_name,
            "validation_wape": _round_metric(wape_value),
            "validation_rmse": _round_metric(rmse_value),
            "selected": model_name == selected_name,
        }
        for model_name, _predictor, wape_value, rmse_value, _residuals in ordered
    ]


def _build_weighted_blend_predictor(
    components: Sequence[tuple[str, Callable[..., np.ndarray], float]],
) -> Callable[..., np.ndarray]:
    normalized_components = [
        (model_name, predictor, float(weight))
        for model_name, predictor, weight in components
        if weight > 0
    ]
    weight_sum = sum(weight for _model_name, _predictor, weight in normalized_components)
    if weight_sum <= 0:
        raise ValueError("invalid blend weights")
    normalized_components = [
        (model_name, predictor, weight / weight_sum)
        for model_name, predictor, weight in normalized_components
    ]

    def _predict_weighted_blend(
        series: Sequence[float],
        config: ForecastConfig,
        horizon: int,
        future_exog: Sequence[float] | None = None,
        *,
        exog_history: Sequence[float] | None = None,
    ) -> np.ndarray:
        weighted_predictions: list[np.ndarray] = []
        for model_name, predictor, weight in normalized_components:
            model_prediction = _run_predictor(
                model_name,
                predictor,
                series,
                config,
                horizon,
                exog_history=exog_history,
                future_exog=future_exog,
            )
            weighted_predictions.append(np.asarray(model_prediction, dtype=float) * weight)
        return np.sum(weighted_predictions, axis=0, dtype=float)

    return _predict_weighted_blend


def _build_recent_window_predictor(
    predictor: Callable[..., np.ndarray],
    *,
    window_size: int,
) -> Callable[..., np.ndarray]:
    def _predict_recent_window(
        series: Sequence[float],
        config: ForecastConfig,
        horizon: int,
        future_exog: Sequence[float] | None = None,
        *,
        exog_history: Sequence[float] | None = None,
    ) -> np.ndarray:
        if len(series) <= window_size:
            return predictor(
                series,
                config,
                horizon,
                future_exog,
                exog_history=exog_history,
            )

        sliced_series = list(series[-window_size:])
        sliced_exog = None
        if exog_history is not None:
            exog_matrix = _normalize_exog_matrix(exog_history)
            if exog_matrix is not None:
                sliced_exog = exog_matrix[-window_size:].tolist()

        return predictor(
            sliced_series,
            config,
            horizon,
            future_exog,
            exog_history=sliced_exog,
        )

    return _predict_recent_window


def _build_future_labels(
    existing_labels: Sequence[str],
    config: ForecastConfig,
    *,
    global_start_date: date,
    last_log_date: date,
    current_label: str | None = None,
) -> list[str]:
    if not existing_labels and not current_label:
        return []

    labels: list[str] = []
    remaining_horizon = config.horizon
    anchor_label = current_label or (existing_labels[-1] if existing_labels else None)

    if current_label:
        labels.append(current_label)
        remaining_horizon -= 1

    if config.frequency == "daily":
        last_date = date.fromisoformat(anchor_label)
        labels.extend(
            [
                (last_date + timedelta(days=step)).isoformat()
                for step in range(1, remaining_horizon + 1)
            ]
        )
        return labels

    for step in range(1, remaining_horizon + 1):
        future_anchor = last_log_date + timedelta(days=step * 7)
        year, week_num = get_custom_week_info(future_anchor, global_start_date)
        labels.append(f"{year}-W{week_num:02}")
    return labels


def _create_forecast(
    labels: Sequence[str],
    series: Sequence[float | None],
    config: ForecastConfig,
    *,
    global_start_date: date,
    last_log_date: date,
    current_label: str | None = None,
    exog_history: Sequence[float] | None = None,
    future_exog: Sequence[float] | None = None,
    display_divisor: float = 1.0,
    target_kind: str = "duration",
) -> dict:
    history_points = len(series)
    future_labels = _build_future_labels(
        labels,
        config,
        global_start_date=global_start_date,
        last_log_date=last_log_date,
        current_label=current_label,
    )

    numeric_series = [0.0 if value is None else float(value) for value in series]
    numeric_exog = _sanitize_exog_values(exog_history)
    available_predictors = _available_model_predictors(
        include_nonlinear=True,
        target_kind=target_kind,
    )

    if history_points < config.min_history:
        return _empty_forecast(
            labels=future_labels,
            horizon=config.horizon,
            history_points=history_points,
            reason=UNAVAILABLE_REASON,
        )

    candidate_results: list[tuple[str, Callable[..., np.ndarray], float, float, dict[int, list[float]]]] = []
    for model_name, predictor in available_predictors:
        try:
            wape_value, rmse_value, residuals = _backtest_candidate(
                model_name,
                predictor,
                numeric_series,
                config,
                exog_history=numeric_exog,
            )
        except Exception:
            continue
        if not _is_finite_metric(wape_value) or not _is_finite_metric(rmse_value):
            continue
        candidate_results.append(
            (model_name, predictor, wape_value, rmse_value, residuals)
        )

    ranked_candidates = sorted(candidate_results, key=lambda item: (item[2], item[3], item[0]))
    if len(ranked_candidates) >= 2:
        top_candidates = ranked_candidates[: min(3, len(ranked_candidates))]
        blend_components = [
            (
                model_name,
                predictor,
                1.0 / max(wape_value, 0.05),
            )
            for model_name, predictor, wape_value, _rmse_value, _residuals in top_candidates
        ]
        blend_predictor = _build_weighted_blend_predictor(blend_components)
        try:
            blend_wape, blend_rmse, blend_residuals = _backtest_candidate(
                "Weighted Blend",
                blend_predictor,
                numeric_series,
                config,
                exog_history=numeric_exog,
            )
        except Exception:
            blend_wape = None
            blend_rmse = None
            blend_residuals = None
        if (
            _is_finite_metric(blend_wape)
            and _is_finite_metric(blend_rmse)
            and blend_residuals is not None
        ):
            candidate_results.append(
                (
                    "Weighted Blend",
                    blend_predictor,
                    float(blend_wape),
                    float(blend_rmse),
                    blend_residuals,
                )
            )

    if not candidate_results:
        return _empty_forecast(
            labels=future_labels,
            horizon=config.horizon,
            history_points=history_points,
            reason=DEPENDENCY_REASON
            if not available_predictors
            else MODEL_FAILURE_REASON,
        )

    selected_name, selected_predictor, best_wape, best_rmse, residuals = min(
        candidate_results,
        key=lambda item: (item[2], item[3]),
    )
    baseline_result = next(
        (result for result in candidate_results if result[0] == "Seasonal Naive"),
        None,
    )
    baseline_wape = baseline_result[2] if baseline_result else None
    baseline_rmse = baseline_result[3] if baseline_result else None
    serialized_candidates = _serialize_candidates(
        candidate_results,
        selected_name=selected_name,
    )

    if best_wape > ACCURACY_GATE_WAPE:
        return _empty_forecast(
            labels=future_labels,
            horizon=config.horizon,
            history_points=history_points,
            reason=LOW_CONFIDENCE_REASON,
            model_name=selected_name,
            validation_wape=best_wape,
            validation_rmse=best_rmse,
            baseline_wape=baseline_wape,
            baseline_rmse=baseline_rmse,
            model_candidates=serialized_candidates,
        )

    try:
        prediction = _run_predictor(
            selected_name,
            selected_predictor,
            numeric_series,
            config,
            config.horizon,
            exog_history=numeric_exog,
            future_exog=future_exog,
        )
    except Exception:
        return _empty_forecast(
            labels=future_labels,
            horizon=config.horizon,
            history_points=history_points,
            reason=MODEL_FAILURE_REASON,
            model_name=selected_name,
            validation_wape=best_wape,
            validation_rmse=best_rmse,
            baseline_wape=baseline_wape,
            baseline_rmse=baseline_rmse,
            model_candidates=serialized_candidates,
        )
    if not np.all(np.isfinite(prediction)):
        return _empty_forecast(
            labels=future_labels,
            horizon=config.horizon,
            history_points=history_points,
            reason=MODEL_FAILURE_REASON,
            model_name=selected_name,
            validation_wape=best_wape,
            validation_rmse=best_rmse,
            baseline_wape=baseline_wape,
            baseline_rmse=baseline_rmse,
            model_candidates=serialized_candidates,
        )

    lower, upper = _build_intervals(prediction, residuals)
    scaled_prediction = np.maximum(prediction, 0.0) / max(display_divisor, 1.0)
    scaled_lower = [round(value / max(display_divisor, 1.0), 2) for value in lower]
    scaled_upper = [round(value / max(display_divisor, 1.0), 2) for value in upper]
    return {
        "labels": future_labels,
        "prediction": _round_series(scaled_prediction),
        "lower": scaled_lower,
        "upper": scaled_upper,
        "model_name": selected_name,
        "history_points": history_points,
        "horizon": config.horizon,
        "trained_on": "all_history",
        "confidence_level": CONFIDENCE_LEVEL,
        "accuracy_threshold": ACCURACY_GATE_WAPE,
        "selection_strategy": MODEL_SELECTION_STRATEGY,
        "validation_wape": _round_metric(best_wape),
        "validation_rmse": _round_metric(best_rmse / max(display_divisor, 1.0)),
        "baseline_wape": _round_metric(baseline_wape),
        "baseline_rmse": _round_metric(
            None if baseline_rmse is None else baseline_rmse / max(display_divisor, 1.0)
        ),
        "model_candidates": serialized_candidates,
        "available": True,
        "reason": "",
    }


def build_trend_forecasts(
    *,
    daily_labels: Sequence[str],
    daily_duration_values: Sequence[float | None],
    daily_efficiency_values: Sequence[float | None],
    daily_stage_features: Sequence[Sequence[float]] | None = None,
    daily_future_stage_features: Sequence[Sequence[float]] | None = None,
    weekly_labels: Sequence[str],
    weekly_duration_values: Sequence[float | None],
    weekly_efficiency_values: Sequence[float | None],
    weekly_stage_features: Sequence[Sequence[float]] | None = None,
    weekly_future_stage_features: Sequence[Sequence[float]] | None = None,
    global_start_date: date,
    last_log_date: date,
    daily_current_label: str | None = None,
    weekly_current_label: str | None = None,
    weekly_duration_display_divisor: float = 1.0,
) -> dict[str, dict]:
    daily_efficiency_future_seed = _build_seed_forecast(
        daily_efficiency_values,
        DAILY_CONFIG,
        DAILY_CONFIG.horizon,
    )
    daily_duration_exog_history = _combine_exog_columns(
        daily_efficiency_values,
        daily_stage_features,
    )
    daily_duration_future_exog = _combine_exog_columns(
        daily_efficiency_future_seed,
        daily_future_stage_features,
    )
    daily_duration_forecast = _create_forecast(
        daily_labels,
        daily_duration_values,
        DAILY_CONFIG,
        global_start_date=global_start_date,
        last_log_date=last_log_date,
        current_label=daily_current_label,
        exog_history=daily_duration_exog_history,
        future_exog=daily_duration_future_exog,
        target_kind="duration",
    )
    daily_efficiency_exog_history = _combine_exog_columns(
        daily_duration_values,
        daily_stage_features,
    )
    daily_efficiency_future_exog = _combine_exog_columns(
        daily_duration_forecast["prediction"]
        if daily_duration_forecast.get("available")
        else None,
        daily_future_stage_features,
    )
    daily_efficiency_forecast = _create_forecast(
        daily_labels,
        daily_efficiency_values,
        DAILY_CONFIG,
        global_start_date=global_start_date,
        last_log_date=last_log_date,
        current_label=daily_current_label,
        exog_history=daily_efficiency_exog_history,
        future_exog=daily_efficiency_future_exog,
        target_kind="efficiency",
    )
    weekly_efficiency_future_seed = _build_seed_forecast(
        weekly_efficiency_values,
        WEEKLY_CONFIG,
        WEEKLY_CONFIG.horizon,
    )
    weekly_duration_exog_history = _combine_exog_columns(
        weekly_efficiency_values,
        weekly_stage_features,
    )
    weekly_duration_future_exog = _combine_exog_columns(
        weekly_efficiency_future_seed,
        weekly_future_stage_features,
    )
    weekly_duration_forecast = _create_forecast(
        weekly_labels,
        weekly_duration_values,
        WEEKLY_CONFIG,
        global_start_date=global_start_date,
        last_log_date=last_log_date,
        current_label=weekly_current_label,
        exog_history=weekly_duration_exog_history,
        future_exog=weekly_duration_future_exog,
        display_divisor=weekly_duration_display_divisor,
        target_kind="duration",
    )
    weekly_efficiency_exog_history = _combine_exog_columns(
        weekly_duration_values,
        weekly_stage_features,
    )
    weekly_efficiency_future_exog = _combine_exog_columns(
        [
            round(value * max(weekly_duration_display_divisor, 1.0), 2)
            for value in weekly_duration_forecast["prediction"]
        ]
        if weekly_duration_forecast.get("available")
        else None,
        weekly_future_stage_features,
    )
    weekly_efficiency_forecast = _create_forecast(
        weekly_labels,
        weekly_efficiency_values,
        WEEKLY_CONFIG,
        global_start_date=global_start_date,
        last_log_date=last_log_date,
        current_label=weekly_current_label,
        exog_history=weekly_efficiency_exog_history,
        future_exog=weekly_efficiency_future_exog,
        target_kind="efficiency",
    )

    return {
        "daily_duration_data": daily_duration_forecast,
        "daily_efficiency_data": daily_efficiency_forecast,
        "weekly_duration_data": weekly_duration_forecast,
        "weekly_efficiency_data": weekly_efficiency_forecast,
    }
