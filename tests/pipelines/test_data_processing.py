import pandas as pd
import pytest

from asi_project.data import DataContractError
from asi_project.pipelines.data_processing.nodes import (
    filter_training_data,
    normalize_data,
    validate_raw_data,
)
from asi_project.pipelines.data_processing.pipeline import create_pipeline


def _raw_sample(project):
    return pd.read_csv(project.config.ci_sample_path)


def test_create_pipeline_structure():
    pipeline = create_pipeline()

    assert pipeline.inputs() == {"raw_data"}
    assert pipeline.outputs() == {"intermediate_data"}


def test_validate_raw_data_unifies_column_names(project):
    raw = _raw_sample(project).rename(columns={"Credit Score": "Credit  Score "})

    validated = validate_raw_data(raw)

    assert "Credit Score" in validated.columns
    assert len(validated) == len(raw)


def test_validate_raw_data_rejects_missing_target(project):
    raw = _raw_sample(project).drop(columns=[project.contract.target])

    with pytest.raises(DataContractError):
        validate_raw_data(raw)


def test_normalize_data_applies_dataset_rules(project):
    validated = validate_raw_data(_raw_sample(project)).head(3).copy()
    validated.loc[0, "Credit Score"] = 7310.0
    validated.loc[1, "Home Ownership"] = "HaveMortgage"
    validated.loc[2, "Purpose"] = " other "

    normalized = normalize_data(validated)

    assert normalized.loc[0, "Credit Score"] == 731.0
    assert normalized.loc[1, "Home Ownership"] == "Home Mortgage"
    assert normalized.loc[2, "Purpose"] == "Other"


def test_filter_training_data_drops_missing_target_and_duplicates(project):
    normalized = normalize_data(validate_raw_data(_raw_sample(project)))
    expected = filter_training_data(normalized)
    no_target = normalized.head(1).assign(**{project.contract.target: None})
    duplicate = expected.head(1).assign(**{"Credit Score": 999.0})

    filtered = filter_training_data(
        pd.concat([normalized, no_target, duplicate], ignore_index=True)
    )

    assert len(filtered) == len(expected)
