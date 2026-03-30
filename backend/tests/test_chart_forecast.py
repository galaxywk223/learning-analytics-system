import threading
import time
from datetime import date, timedelta

import numpy as np

from app import db
from app.models import DailyData, LogEntry, Stage
from app.services import chart_service, forecast_service
from app.services.chart_service import get_chart_data_for_user


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
            start_date=date.today() - timedelta(days=170),
            days=140,
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


def test_chart_overview_forecast_status_can_be_polled_async(
    app,
    client,
    db_session,
    register_and_login,
    auth_headers,
    monkeypatch,
):
    with app.app_context():
        app.config["CHART_FORECAST_SYNC_MODE"] = False
        chart_service._overview_cache.clear()
        chart_service._overview_inflight.clear()
        chart_service._forecast_cache.clear()
        chart_service._forecast_inflight.clear()

        token, user_id = register_and_login("forecast-async", "forecast-async@test.com")
        _create_history(
            user_id,
            start_date=date.today() - timedelta(days=119),
            days=100,
        )

        started = threading.Event()
        release = threading.Event()

        def slow_builder(**kwargs):
            started.set()
            release.wait(timeout=2)
            return {
                "daily_duration_data": {
                    "labels": ["2099-01-01"],
                    "prediction": [1.23],
                    "lower": [1.0],
                    "upper": [1.4],
                    "model_name": "Test Async Model",
                    "history_points": 60,
                    "horizon": 14,
                    "trained_on": "all_history",
                    "confidence_level": 0.8,
                    "accuracy_threshold": 0.4,
                    "selection_strategy": "lowest_wape_then_rmse_with_weighted_blend",
                    "validation_wape": 0.2,
                    "validation_rmse": 1.0,
                    "baseline_wape": 0.3,
                    "baseline_rmse": 1.4,
                    "model_candidates": [],
                    "available": True,
                    "reason": "",
                },
                "daily_efficiency_data": {
                    "labels": ["2099-01-01"],
                    "prediction": [2.34],
                    "lower": [2.0],
                    "upper": [2.6],
                    "model_name": "Test Async Model",
                    "history_points": 60,
                    "horizon": 14,
                    "trained_on": "all_history",
                    "confidence_level": 0.8,
                    "accuracy_threshold": 0.4,
                    "selection_strategy": "lowest_wape_then_rmse_with_weighted_blend",
                    "validation_wape": 0.18,
                    "validation_rmse": 0.8,
                    "baseline_wape": 0.29,
                    "baseline_rmse": 1.1,
                    "model_candidates": [],
                    "available": True,
                    "reason": "",
                },
                "weekly_duration_data": {
                    "labels": ["2099-W01"],
                    "prediction": [3.45],
                    "lower": [3.0],
                    "upper": [4.0],
                    "model_name": "Test Async Model",
                    "history_points": 20,
                    "horizon": 8,
                    "trained_on": "all_history",
                    "confidence_level": 0.8,
                    "accuracy_threshold": 0.4,
                    "selection_strategy": "lowest_wape_then_rmse_with_weighted_blend",
                    "validation_wape": 0.21,
                    "validation_rmse": 1.2,
                    "baseline_wape": 0.32,
                    "baseline_rmse": 1.5,
                    "model_candidates": [],
                    "available": True,
                    "reason": "",
                },
                "weekly_efficiency_data": {
                    "labels": ["2099-W01"],
                    "prediction": [4.56],
                    "lower": [4.2],
                    "upper": [4.8],
                    "model_name": "Test Async Model",
                    "history_points": 20,
                    "horizon": 8,
                    "trained_on": "all_history",
                    "confidence_level": 0.8,
                    "accuracy_threshold": 0.4,
                    "selection_strategy": "lowest_wape_then_rmse_with_weighted_blend",
                    "validation_wape": 0.16,
                    "validation_rmse": 0.9,
                    "baseline_wape": 0.28,
                    "baseline_rmse": 1.3,
                    "model_candidates": [],
                    "available": True,
                    "reason": "",
                },
            }

        monkeypatch.setattr(chart_service, "build_trend_forecasts", slow_builder)

        response = client.get("/api/charts/overview", headers=auth_headers(token))
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["forecast_status"]["state"] == "pending"
        assert payload["forecast_status"]["trained_for_date"] == date.today().isoformat()
        assert (
            payload["daily_duration_data"]["forecast"]["status"] == "pending"
        )
        assert payload["daily_duration_data"]["forecast"]["reason"] == "预测计算中，请稍后刷新"

        assert started.wait(timeout=1)
        status_response = client.get(
            "/api/charts/overview_forecast",
            headers=auth_headers(token),
        )
        assert status_response.status_code == 200
        status_payload = status_response.get_json()["data"]
        assert status_payload["status"] == "pending"
        assert status_payload["trained_for_date"] == date.today().isoformat()

        retrain_response = client.post(
            "/api/charts/overview_forecast/retrain",
            headers=auth_headers(token),
        )
        assert retrain_response.status_code == 200

        release.set()

        ready_payload = None
        for _ in range(40):
            status_response = client.get(
                "/api/charts/overview_forecast",
                headers=auth_headers(token),
            )
            ready_payload = status_response.get_json()["data"]
            if ready_payload["status"] == "ready":
                break
            time.sleep(0.05)

        assert ready_payload is not None
        assert ready_payload["status"] == "ready"
        assert ready_payload["forecasts"]["daily_duration_data"]["status"] == "ready"
        assert ready_payload["forecasts"]["daily_duration_data"]["available"] is True

        app.config["CHART_FORECAST_SYNC_MODE"] = True


def test_chart_forecast_signature_ignores_ongoing_buckets_and_last_log_date():
    base_dataset = {
        "training_labels": ["2025-03-01", "2025-03-02", "2025-03-03"],
        "training_actuals": [1.2, 2.4, 3.6],
        "training_stage_features": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
        "future_stage_features": [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0]],
    }

    trend_data_a = {
        dataset_key: {
            **base_dataset,
            "ongoing": True,
            "ongoing_label": "2025-03-11" if "daily" in dataset_key else "2025-W11",
            "ongoing_value": 4.2,
        }
        for dataset_key in chart_service._FORECAST_DATASET_KEYS
    }
    trend_data_b = {
        dataset_key: {
            **base_dataset,
            "ongoing": False,
            "ongoing_label": "2025-03-12" if "daily" in dataset_key else "2025-W12",
            "ongoing_value": 9.9,
        }
        for dataset_key in chart_service._FORECAST_DATASET_KEYS
    }

    signature_a = chart_service._build_forecast_signature(
        trend_data_a,
        global_start_date=date(2025, 1, 1),
        last_log_date=date(2025, 3, 11),
    )
    signature_b = chart_service._build_forecast_signature(
        trend_data_b,
        global_start_date=date(2025, 1, 1),
        last_log_date=date(2025, 3, 12),
    )

    assert signature_a == signature_b


def test_chart_forecast_signature_changes_when_completed_history_changes():
    trend_data_a = {
        dataset_key: {
            "training_labels": ["2025-03-01", "2025-03-02", "2025-03-03"],
            "training_actuals": [1.2, 2.4, 3.6],
            "training_stage_features": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
            "future_stage_features": [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0]],
        }
        for dataset_key in chart_service._FORECAST_DATASET_KEYS
    }
    trend_data_b = {
        dataset_key: {
            **trend_data_a[dataset_key],
            "training_actuals": [1.2, 9.9, 3.6],
        }
        for dataset_key in chart_service._FORECAST_DATASET_KEYS
    }

    signature_a = chart_service._build_forecast_signature(
        trend_data_a,
        global_start_date=date(2025, 1, 1),
        last_log_date=date(2025, 3, 10),
    )
    signature_b = chart_service._build_forecast_signature(
        trend_data_b,
        global_start_date=date(2025, 1, 1),
        last_log_date=date(2025, 3, 10),
    )

    assert signature_a != signature_b


def test_chart_forecast_reuses_ready_cache_when_only_today_changes(
    app,
    db_session,
    register_and_login,
    monkeypatch,
):
    with app.app_context():
        app.config["CHART_FORECAST_SYNC_MODE"] = False
        chart_service._overview_cache.clear()
        chart_service._overview_inflight.clear()
        chart_service._forecast_cache.clear()
        chart_service._forecast_inflight.clear()

        _token, user_id = register_and_login(
            "forecast-today-cache",
            "forecast-today-cache@test.com",
        )
        stage = _create_history(
            user_id,
            start_date=date.today() - timedelta(days=40),
            days=40,
        )

        call_count = {"value": 0}
        original_builder = chart_service.build_trend_forecasts

        def counting_builder(**kwargs):
            call_count["value"] += 1
            return original_builder(**kwargs)

        monkeypatch.setattr(chart_service, "build_trend_forecasts", counting_builder)

        ready_status = None
        for _ in range(40):
            ready_status = chart_service.get_chart_forecast_status_for_user(user_id)
            if ready_status["status"] == "ready":
                break
            time.sleep(0.05)

        assert ready_status is not None
        assert ready_status["status"] == "ready"
        assert call_count["value"] == 1

        today = date.today()
        db.session.add(
            LogEntry(
                log_date=today,
                task="今日新增",
                actual_duration=95,
                stage_id=stage.id,
            )
        )
        db.session.add(
            DailyData(
                log_date=today,
                efficiency=68.0,
                stage_id=stage.id,
            )
        )
        db.session.commit()

        chart_service._overview_cache.clear()
        chart_service._overview_inflight.clear()

        reused_status = chart_service.get_chart_forecast_status_for_user(user_id)
        payload = chart_service.get_chart_data_for_user(user_id)

        assert reused_status["status"] == "ready"
        assert call_count["value"] == 1
        assert payload["forecast_status"]["state"] == "ready"
        assert today.isoformat() in payload["daily_duration_data"]["labels"]
        assert payload["daily_duration_data"]["forecast"]["status"] == "ready"

        app.config["CHART_FORECAST_SYNC_MODE"] = True


def test_chart_forecast_manual_retrain_still_rebuilds_when_signature_unchanged(
    app,
    db_session,
    register_and_login,
    monkeypatch,
):
    with app.app_context():
        app.config["CHART_FORECAST_SYNC_MODE"] = False
        chart_service._overview_cache.clear()
        chart_service._overview_inflight.clear()
        chart_service._forecast_cache.clear()
        chart_service._forecast_inflight.clear()

        _token, user_id = register_and_login(
            "forecast-retrain-force",
            "forecast-retrain-force@test.com",
        )
        _create_history(
            user_id,
            start_date=date.today() - timedelta(days=45),
            days=45,
        )

        call_count = {"value": 0}
        original_builder = chart_service.build_trend_forecasts

        def counting_builder(**kwargs):
            call_count["value"] += 1
            return original_builder(**kwargs)

        monkeypatch.setattr(chart_service, "build_trend_forecasts", counting_builder)

        initial_status = None
        for _ in range(40):
            initial_status = chart_service.get_chart_forecast_status_for_user(user_id)
            if initial_status["status"] == "ready":
                break
            time.sleep(0.05)

        assert initial_status is not None
        assert initial_status["status"] == "ready"
        assert call_count["value"] == 1

        retrain_status = chart_service.retrain_chart_forecasts_for_user(user_id)
        if retrain_status["status"] != "ready":
            for _ in range(40):
                retrain_status = chart_service.get_chart_forecast_status_for_user(user_id)
                if retrain_status["status"] == "ready":
                    break
                time.sleep(0.05)

        assert retrain_status["status"] == "ready"
        assert call_count["value"] >= 2

        app.config["CHART_FORECAST_SYNC_MODE"] = True
