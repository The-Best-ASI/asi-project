from kedro.pipeline import Node, Pipeline

from .nodes import filter_training_data, normalize_data, validate_raw_data


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=validate_raw_data,
                inputs="raw_data",
                outputs="validated_data",
                name="validate_raw_data",
            ),
            Node(
                func=normalize_data,
                inputs="validated_data",
                outputs="normalized_data",
                name="normalize_data",
            ),
            Node(
                func=filter_training_data,
                inputs="normalized_data",
                outputs="intermediate_data",
                name="filter_training_data",
            ),
        ]
    )
