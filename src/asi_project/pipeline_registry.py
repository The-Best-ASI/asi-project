from kedro.pipeline import Pipeline, pipeline


def register_pipelines() -> dict[str, Pipeline]:
    return {
        "__default__": pipeline([]),
    }
