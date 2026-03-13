from datetime import date, timedelta

import numpy as np

from app import db
from app.models import DailyData, LogEntry, Stage
from app.services.chart_service import get_chart_data_for_user
from app.services import forecast_service


def _create_history(
    user_id: int,
    *,
    start_date: date,
    days: int,
    gap_step: int = 1,
) -> Stage:
    stage = Stage(name="预测阶段", start_date=start_date, user_id=user_id)
    db.session.add(stage)
    db.session.flush()

    for offset in range(days):
        current = start_date + timedelta(days=offset)
        if offset % gap_step != 0:
            continue
        duration = 90 + ((offset % 7) * 12)
        efficiency = 55 + ((offset % 5) * 3)
        db.session.add(
            LogEntry(
                log_date=current,
                task=f"任务{offset}",
                actual_duration=duration,
                stage_id=stage.id,
            )
        )
        db.session.add(
            DailyData(
                log_date=current,
                efficiency=float(efficiency),
                stage_id=stage.id,
            )
        )

    db.session.commit()
    return stage


def test_chart_forecast_available_with_full_history(app, client, db_session, register_and_login):
    with app.app_context():
        _token, user_id = register_and_login("forecast-ok", "forecast-ok@test.com")
        _create_history(
            user_id,
            start_date=date.today() - timedelta(days=119),
            days=100,
        )

        payload = get_chart_data_for_user(user_id)

        daily_duration = payload["daily_duration_data"]["forecast"]
        daily_efficiency = payload["daily_efficiency_data"]["forecast"]
        weekly_duration = payload["weekly_duration_data"]["forecast"]
        weekly_efficiency = payload["weekly_efficiency_data"]["forecast"]

        assert daily_duration["available"] is True
        assert daily_efficiency["available"] is True
        assert weekly_duration["available"] is True
        assert weekly_efficiency["available"] is True
        assert len(daily_duration["labels"]) == 14
        assert len(daily_duration["prediction"]) == 14
        assert len(weekly_duration["labels"]) == 8
        assert len(weekly_duration["prediction"]) == 8
        assert daily_duration["trained_on"] == "all_history"
        assert daily_duration["confidence_level"] == 0.8
        assert daily_duration["accuracy_threshold"] == 0.4
        assert (
            daily_duration["selection_strategy"]
            == "lowest_wape_then_rmse_with_weighted_blend"
        )
        assert isinstance(daily_duration["validation_wape"], float)
        assert isinstance(daily_duration["validation_rmse"], float)
        assert isinstance(daily_duration["model_candidates"], list)
        assert any(item["selected"] is True for item in daily_duration["model_candidates"])
        assert weekly_duration["model_name"] in {
            "Seasonal Naive",
            "Ridge Autoregression",
            "Recent Ridge Autoregression",
            "Two-Stage Duration Autoregression",
            "Log-HistGradientBoosting Autoregression",
            "Poisson-HistGradientBoosting Autoregression",
            "Recent Poisson-HistGradientBoosting Autoregression",
            "Recent Log-HistGradientBoosting Autoregression",
            "Weighted Blend",
        }


def test_chart_forecast_unavailable_when_history_insufficient(
    app, client, db_session, register_and_login
):
    with app.app_context():
        _token, user_id = register_and_login("forecast-short", "forecast-short@test.com")
        _create_history(
            user_id,
            start_date=date.today() - timedelta(days=20),
            days=14,
        )

        payload = get_chart_data_for_user(user_id)

        daily_duration = payload["daily_duration_data"]["forecast"]
        weekly_duration = payload["weekly_duration_data"]["forecast"]

        assert daily_duration["available"] is False
        assert weekly_duration["available"] is False
        assert daily_duration["reason"] == "历史数据不足，暂不提供预测"
        assert weekly_duration["reason"] == "历史数据不足，暂不提供预测"
        assert daily_duration["history_points"] < 28


def test_chart_overview_forecast_handles_gaps_and_response_shape(
    app, client, db_session, register_and_login, auth_headers
):
    with app.app_context():
        token, user_id = register_and_login("forecast-gap", "forecast-gap@test.com")
        _create_history(
            user_id,
            start_date=date.today() - timedelta(days=139),
            days=110,
            gap_step=2,
        )

        response = client.get("/api/charts/overview", headers=auth_headers(token))
        assert response.status_code == 200

        payload = response.get_json()
        assert payload["has_data"] is True
        assert "forecast" in payload["daily_duration_data"]
        assert "forecast" in payload["weekly_duration_data"]
        assert payload["daily_duration_data"]["forecast"]["available"] is True
        assert payload["weekly_duration_data"]["forecast"]["available"] is True
        assert len(payload["daily_duration_data"]["forecast"]["lower"]) == 14
        assert len(payload["daily_duration_data"]["forecast"]["upper"]) == 14
        assert "validation_wape" in payload["daily_duration_data"]["forecast"]
        assert "model_candidates" in payload["weekly_duration_data"]["forecast"]


def test_chart_forecast_hides_prediction_when_backtest_accuracy_is_too_low(monkeypatch):
    start_date = date(2025, 1, 1)
    labels = [
        (start_date + timedelta(days=offset)).isoformat()
        for offset in range(42)
    ]
    series = [1.0 + ((offset % 3) * 0.2) for offset in range(42)]

    def always_bad_predictor(
        input_series,
        config,
        horizon,
        _future_exog=None,
        *,
        exog_history=None,
    ):
        del exog_history
        return np.asarray([999.0] * horizon, dtype=float)

    monkeypatch.setattr(
        forecast_service,
        "_available_model_predictors",
        lambda **kwargs: (("Always Bad", always_bad_predictor),),
    )

    forecast = forecast_service._create_forecast(
        labels,
        series,
        forecast_service.DAILY_CONFIG,
        global_start_date=start_date,
        last_log_date=start_date + timedelta(days=len(labels) - 1),
    )

    assert forecast["available"] is False
    assert forecast["reason"] == forecast_service.LOW_CONFIDENCE_REASON
    assert forecast["model_name"] == "Always Bad"
    assert forecast["validation_wape"] > forecast_service.ACCURACY_GATE_WAPE
    assert forecast["prediction"] == []


def test_chart_forecast_skips_candidates_with_nan_metrics(monkeypatch):
    start_date = date(2025, 1, 1)
    labels = [
        (start_date + timedelta(days=offset)).isoformat()
        for offset in range(42)
    ]
    base_pattern = [1.2, 1.5, 1.8, 1.6, 1.9, 2.1, 1.4]
    series = [base_pattern[offset % 7] for offset in range(42)]

    def nan_predictor(
        input_series,
        config,
        horizon,
        _future_exog=None,
        *,
        exog_history=None,
    ):
        del exog_history
        return np.asarray([np.nan] * horizon, dtype=float)

    monkeypatch.setattr(
        forecast_service,
        "_available_model_predictors",
        lambda **kwargs: (
            ("Broken Nan", nan_predictor),
            ("Seasonal Naive", forecast_service._predict_seasonal_naive),
        ),
    )

    forecast = forecast_service._create_forecast(
        labels,
        series,
        forecast_service.DAILY_CONFIG,
        global_start_date=start_date,
        last_log_date=start_date + timedelta(days=len(labels) - 1),
    )

    assert forecast["available"] is True
    assert forecast["model_name"] == "Seasonal Naive"
    assert forecast["validation_wape"] is not None
    assert forecast["validation_rmse"] is not None
    assert all(candidate["model_name"] != "Broken Nan" for candidate in forecast["model_candidates"])
