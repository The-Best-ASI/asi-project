from typing import Any

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
) -> dict[str, Any]:
    config = load_project_config()
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
