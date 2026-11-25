import os
from typing import Any

from asi_project.config import get_contract, load_project_config
from asi_project.metrics import CONFUSION_KEYS, METRIC_NAMES
from asi_project.model_package import get_data_fingerprint, get_git_sha, get_library_versions

PRIMARY_METRIC = "recall"
BASELINE_MODEL = "logistic_regression"
DISABLED_RUN_ID = "disabled"


def flatten_metrics(metrics: dict[str, Any]) -> dict[str, float | int]:
    flat: dict[str, float | int] = {}
    for model_name, values in metrics.get("models", {}).items():
        for metric in METRIC_NAMES:
            if metric in values:
                flat[f"{model_name}/{metric}"] = float(values[metric])
        matrix = values.get("confusion_matrix", {})
        for key in CONFUSION_KEYS:
            if key in matrix:
                flat[f"{model_name}/confusion_matrix/{key}"] = int(matrix[key])
    return flat


def build_run_config(
    metrics: dict[str, Any],
    model_params: dict[str, Any],
    split_params: dict[str, Any],
) -> dict[str, Any]:
    config = load_project_config()
    contract = get_contract(config)
    return {
        "dataset": contract.dataset_id,
        "target": contract.target,
        "positive_class": contract.positive_class,
        "data_mode": metrics.get("data_mode"),
        "model_type": BASELINE_MODEL,
        "model_params": dict(model_params),
        "split": {**dict(split_params), **metrics.get("split", {})},
        "features": list(metrics.get("features", config.model_features)),
        "git_sha": get_git_sha(config.root),
        "data_fingerprint": get_data_fingerprint(config, contract),
        "library_versions": get_library_versions(repo_root=config.root),
    }


def log_baseline_run(
    metrics: dict[str, Any],
    model_params: dict[str, Any],
    split_params: dict[str, Any],
    wandb_params: dict[str, Any],
) -> str:
    if not wandb_params.get("enabled", True):
        return DISABLED_RUN_ID

    import wandb

    run_config = build_run_config(metrics, model_params, split_params)
    flat_metrics = flatten_metrics(metrics)

    with wandb.init(
        project=os.environ.get("WANDB_PROJECT") or wandb_params.get("project"),
        entity=os.environ.get("WANDB_ENTITY") or wandb_params.get("entity"),
        job_type="baseline",
        name=wandb_params.get("baseline_run_name", "baseline-logreg"),
        tags=["baseline", str(run_config["data_mode"])],
        config=run_config,
    ) as run:
        run.log(flat_metrics)
        run.summary.update(flat_metrics)
        primary_key = f"{BASELINE_MODEL}/{PRIMARY_METRIC}"
        if primary_key in flat_metrics:
            run.summary["primary_metric"] = PRIMARY_METRIC
            run.summary["primary_metric_value"] = flat_metrics[primary_key]
        return str(run.id)
