from kedro.pipeline import Node, Pipeline

from .nodes import evaluate_model, split_data, train_model


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
        ]
    )
