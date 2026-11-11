from sklearn.pipeline import Pipeline

from asi_project.data import filter_training_rows, normalize_input
from asi_project.metrics import validate_metrics_record
from asi_project.pipelines.data_science.nodes import evaluate_model, split_data, train_model

SPLIT_PARAMS = {"test_size": 0.2, "random_state": 42}
MODEL_PARAMS = {
    "random_state": 42,
    "max_iter": 1000,
    "solver": "liblinear",
    "class_weight": "balanced",
}


def _clean_sample(project):
    return filter_training_rows(normalize_input(project.sample), project.contract)


def test_split_data_node(project):
    df = _clean_sample(project)
    X_train, X_test, y_train, y_test = split_data(df, SPLIT_PARAMS)

    assert len(X_train) + len(X_test) == len(df)
    assert list(X_train.columns) == list(project.config.model_features)
    assert set(y_train.unique()) == {0, 1}
    assert set(y_test.unique()) == {0, 1}


def test_train_model_node(project):
    df = _clean_sample(project)
    X_train, X_test, y_train, _ = split_data(df, SPLIT_PARAMS)

    model = train_model(X_train, y_train, MODEL_PARAMS)

    assert isinstance(model, Pipeline)
    assert len(model.predict(X_test)) == len(X_test)


def test_evaluate_model_node(project):
    df = _clean_sample(project)
    X_train, X_test, y_train, y_test = split_data(df, SPLIT_PARAMS)
    model = train_model(X_train, y_train, MODEL_PARAMS)

    record = evaluate_model(model, X_train, y_train, X_test, y_test, "sample")

    assert validate_metrics_record(record, project.contract) == []
