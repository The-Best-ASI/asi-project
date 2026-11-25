import os
from collections.abc import Sequence
from typing import Any

from asi_project.config import get_contract, load_project_config
from asi_project.metrics import CONFUSION_KEYS, METRIC_NAMES
from asi_project.model_package import get_data_fingerprint, get_git_sha, get_library_versions

PRIMARY_METRIC = "recall"
DISABLED_RUN_ID = "disabled"


def flatten_model_metrics(values: dict[str, Any], prefix: str) -> dict[str, float | int]:
    flat: dict[str, float | int] = {}
    for metric in METRIC_NAMES:
        if metric in values:
            flat[f"{prefix}/{metric}"] = float(values[metric])
    matrix = values.get("confusion_matrix", {})
    for key in CONFUSION_KEYS:
        if key in matrix:
            flat[f"{prefix}/confusion_matrix/{key}"] = int(matrix[key])
    return flat


def build_run_metrics(
    model_metrics: dict[str, Any],
    system_metrics: dict[str, float] | None = None,
    reference_metrics: dict[str, dict[str, Any]] | None = None,
) -> dict[str, float | int]:
    flat: dict[str, float | int] = dict(flatten_model_metrics(model_metrics, "test"))
    for name, values in (reference_metrics or {}).items():
        flat.update(flatten_model_metrics(values, name))
    for key, value in (system_metrics or {}).items():
        flat[f"system/{key}"] = value
    flat["primary_metric_value"] = float(model_metrics[PRIMARY_METRIC])
    return flat


def build_run_config(
    *,
    model_type: str,
    model_params: dict[str, Any],
    data_mode: str,
    split: dict[str, Any],
    features: Sequence[str],
) -> dict[str, Any]:
    config = load_project_config()
    contract = get_contract(config)
    return {
        "dataset": contract.dataset_id,
        "target": contract.target,
        "positive_class": contract.positive_class,
        "data_mode": data_mode,
        "model_type": model_type,
        "primary_metric": PRIMARY_METRIC,
        "model_params": dict(model_params),
        "split": {"strategy": contract.split_strategy, **dict(split)},
        "features": [str(name) for name in features],
        "git_sha": get_git_sha(config.root),
        "data_fingerprint": get_data_fingerprint(config, contract),
        "library_versions": get_library_versions(repo_root=config.root),
    }


def log_run(
    *,
    wandb_params: dict[str, Any],
    name: str,
    job_type: str,
    run_config: dict[str, Any],
    run_metrics: dict[str, float | int],
) -> str:
    if not wandb_params.get("enabled", True):
        return DISABLED_RUN_ID

    import wandb

    with wandb.init(
        project=os.environ.get("WANDB_PROJECT") or wandb_params.get("project"),
        entity=os.environ.get("WANDB_ENTITY") or wandb_params.get("entity"),
        job_type=job_type,
        name=name,
        tags=[job_type, str(run_config["data_mode"])],
        config=run_config,
    ) as run:
        run.log(run_metrics)
        run.summary.update(run_metrics)
        return str(run.id)
