import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from asi_project.config import get_contract, load_project_config
from asi_project.data import make_xy, split_train_test
from asi_project.metrics import (
    build_metrics_record,
    compute_metrics,
    validate_metrics_record,
)
from asi_project.model import build_baseline_pipeline, make_dummy
from asi_project.system_metrics import system_metrics, timed
from asi_project.tracking import build_run_config, build_run_metrics, log_run

BASELINE_MODEL = "logistic_regression"


def split_data(
    intermediate_data: pd.DataFrame,
    split_params: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    config = load_project_config()
    contract = get_contract(config)
    X, y = make_xy(intermediate_data, contract, config.model_features)
    return split_train_test(
        X,
        y,
        contract,
        test_size=split_params["test_size"],
        random_state=split_params["random_state"],
    )


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    model_params: dict[str, Any],
) -> Pipeline:
    config = load_project_config()
    pipeline = build_baseline_pipeline(
        list(config.numeric_features),
        list(config.categorical_features),
        model_params=model_params,
    )
    pipeline.fit(X_train, y_train)
    return pipeline


def evaluate_model(
    model: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    data_mode: str,
    split_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = load_project_config()
    if split_params is not None:
        config = replace(
            config,
            test_size=float(split_params["test_size"]),
            random_state=int(split_params["random_state"]),
        )
    contract = get_contract(config)

    dummy = make_dummy()
    dummy.fit(X_train, y_train)
    dummy_pred = dummy.predict(X_test)

    lr_pred = model.predict(X_test)

    results = {
        "dummy": compute_metrics(y_test, dummy_pred),
        "logistic_regression": compute_metrics(y_test, lr_pred),
    }

    record = build_metrics_record(
        contract=contract,
        config=config,
        features=list(model.feature_names_in_),
        n_train=len(X_train),
        n_test=len(X_test),
        data_mode=data_mode,
        results=results,
    )
    problems = validate_metrics_record(record, contract)
    if problems:
        raise ValueError("Metryki nie spełniają kontraktu:\n" + "\n".join(problems))
    return record


def measure_baseline(model: Pipeline, X_test: pd.DataFrame) -> dict[str, float]:
    _, prediction_time = timed(lambda: model.predict(X_test))
    with tempfile.TemporaryDirectory() as tmp:
        model_path = Path(tmp) / "model"
        joblib.dump(model, model_path)
        return system_metrics(prediction_time, model_path, kind="sklearn")


def log_baseline_wandb(
    metrics: dict[str, Any],
    baseline_system_metrics: dict[str, float],
    model_params: dict[str, Any],
    wandb_params: dict[str, Any],
) -> str:
    models = metrics["models"]
    return log_run(
        wandb_params=wandb_params,
        name=wandb_params.get("baseline_run_name", "baseline-logreg"),
        job_type="baseline",
        run_config=build_run_config(
            model_type=BASELINE_MODEL,
            model_params=model_params,
            data_mode=metrics["data_mode"],
            split=metrics["split"],
            features=metrics["features"],
        ),
        run_metrics=build_run_metrics(
            models[BASELINE_MODEL],
            system_metrics=baseline_system_metrics,
            reference_metrics={"dummy": models["dummy"]},
        ),
    )


def run_autogluon(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    ag_params: dict[str, Any],
    data_mode: str,
    split_params: dict[str, Any],
    wandb_params: dict[str, Any],
) -> dict[str, Any]:
    if not ag_params.get("enabled", True):
        return {}

    from autogluon.tabular import TabularPredictor

    target = y_train.name or "target"
    train_data = X_train.assign(**{target: y_train})
    split = {**split_params, "n_train": len(X_train), "n_test": len(X_test)}

    results = {}
    for cfg in ag_params["configs"]:
        name = cfg["name"]
        model_path = Path(ag_params["save_path"]) / name

        presets = [cfg["presets"]]
        if cfg.get("optimize_for_deployment", False):
            presets.append("optimize_for_deployment")

        predictor = TabularPredictor(
            label=target,
            eval_metric=ag_params["eval_metric"],
            path=str(model_path),
        ).fit(
            train_data=train_data,
            presets=presets,
            time_limit=cfg["time_limit"],
        )

        y_pred, prediction_time = timed(lambda p=predictor: p.predict(X_test))
        best_model = predictor.model_best
        del predictor

        ml_metrics = compute_metrics(y_test, y_pred)
        sys_metrics = system_metrics(prediction_time, model_path, kind="autogluon")
        run_id = log_run(
            wandb_params=wandb_params,
            name=name,
            job_type="autogluon",
            run_config=build_run_config(
                model_type="autogluon",
                model_params={
                    **cfg,
                    "presets": presets,
                    "eval_metric": ag_params["eval_metric"],
                    "best_model": best_model,
                },
                data_mode=data_mode,
                split=split,
                features=list(X_train.columns),
            ),
            run_metrics=build_run_metrics(ml_metrics, system_metrics=sys_metrics),
        )
        results[name] = {
            "ml_metrics": ml_metrics,
            "system_metrics": sys_metrics,
            "best_model": best_model,
            "wandb_run_id": run_id,
        }

    return results
