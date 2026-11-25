from kedro.pipeline import Node, Pipeline

from .nodes import (
    evaluate_model,
    log_baseline_wandb,
    measure_baseline,
    run_autogluon,
    split_data,
    train_model,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=split_data,
                inputs=["intermediate_data", "params:split"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="split_data",
            ),
            Node(
                func=train_model,
                inputs=["X_train", "y_train", "params:model_params"],
                outputs="model",
                name="train_model",
            ),
            Node(
                func=evaluate_model,
                inputs=[
                    "model",
                    "X_train",
                    "y_train",
                    "X_test",
                    "y_test",
                    "params:data_mode",
                    "params:split",
                ],
                outputs="metrics",
                name="evaluate_model",
            ),
            Node(
                func=measure_baseline,
                inputs=["model", "X_test"],
                outputs="baseline_system_metrics",
                name="measure_baseline",
            ),
            Node(
                func=log_baseline_wandb,
                inputs=[
                    "metrics",
                    "baseline_system_metrics",
                    "params:model_params",
                    "params:wandb",
                ],
                outputs="wandb_baseline_run_id",
                name="log_baseline_wandb",
            ),
            Node(
                func=run_autogluon,
                inputs=[
                    "X_train",
                    "y_train",
                    "X_test",
                    "y_test",
                    "params:autogluon",
                    "params:data_mode",
                    "params:split",
                    "params:wandb",
                ],
                outputs="autogluon_report",
                name="autogluon_node",
            ),
        ]
    )
