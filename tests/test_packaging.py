"""Testy jednostkowe pakowania modelu (Sprint 3): zapis, walidacja, odczyt i predykcja w CI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from asi_project.config import load_project_config
from asi_project.data import make_xy, normalize_input
from asi_project.metrics import compute_metrics
from asi_project.model import build_baseline_pipeline
from asi_project.model_package import (
    METADATA_FILENAME,
    MODEL_FILENAME,
    _discover_project_packages,
    build_metadata,
    get_library_versions,
    load_model_package,
    log_model_package_artifact,
    save_model_package,
    validate_metadata,
    validate_package_dir,
)


def _make_sample_metadata(toy_contract, repo_root):
    config = load_project_config(repo_root)
    metrics = compute_metrics([0, 0, 1, 1], [0, 1, 1, 1])
    return build_metadata(
        contract=toy_contract,
        config=config,
        metrics=metrics,
        model_type="sklearn",
        model_version="1.0.0",
        features=["num", "cat"],
        git_sha="deadbeef1234567",
        data_fingerprint="a" * 64,
    )


def _make_fitted_toy_pipeline(toy_frame, toy_contract):
    df = normalize_input(toy_frame)
    X, y = make_xy(df, toy_contract, ("num", "cat"))
    pipeline = build_baseline_pipeline(["num"], ["cat"])
    pipeline.fit(X, y)
    return pipeline, X


def test_build_and_validate_metadata_passes(toy_contract, repo_root):
    metadata = _make_sample_metadata(toy_contract, repo_root)
    assert validate_metadata(metadata, contract=toy_contract) == []
    assert metadata["target"] == "label"
    assert metadata["positive_class"] == "yes"
    assert metadata["features"] == ["num", "cat"]
    assert "python" in metadata["library_versions"]


def test_validate_metadata_reports_missing_and_invalid_fields(toy_contract, repo_root):
    metadata = _make_sample_metadata(toy_contract, repo_root)
    metadata["features"] = ["num", "leak"]
    problems = validate_metadata(metadata, contract=toy_contract)
    assert any("ALLOWED FEATURES" in p for p in problems)

    broken = _make_sample_metadata(toy_contract, repo_root)
    del broken["git_sha"]
    problems = validate_metadata(broken, contract=toy_contract)
    assert any("git_sha" in p for p in problems)

    wrong_target = _make_sample_metadata(toy_contract, repo_root)
    wrong_target["target"] = "wrong_col"
    problems = validate_metadata(wrong_target, contract=toy_contract)
    assert any("metadata.target" in p for p in problems)


def test_save_and_load_sklearn_package_roundtrip(toy_frame, toy_contract, repo_root, tmp_path):
    pipeline, X = _make_fitted_toy_pipeline(toy_frame, toy_contract)
    metadata = _make_sample_metadata(toy_contract, repo_root)
    package_dir = tmp_path / "sklearn_pkg"

    saved_path = save_model_package(pipeline, metadata, package_dir, contract=toy_contract)
    assert saved_path == package_dir
    assert (package_dir / MODEL_FILENAME).is_file()
    assert (package_dir / METADATA_FILENAME).is_file()

    loaded_model, loaded_metadata = load_model_package(package_dir, contract=toy_contract)
    assert loaded_metadata["git_sha"] == "deadbeef1234567"
    assert loaded_metadata["features"] == ["num", "cat"]

    batch = X.head(5)
    np.testing.assert_array_equal(pipeline.predict(batch), loaded_model.predict(batch))
    np.testing.assert_allclose(pipeline.predict_proba(batch), loaded_model.predict_proba(batch))


def test_save_autogluon_package_handles_same_and_external_directory(
    toy_contract, repo_root, tmp_path
):
    metadata = _make_sample_metadata(toy_contract, repo_root)
    metadata["model_type"] = "autogluon"

    # Przypadek 1: predyktor zapisany w zewnętrznym katalogu -> kopiowany do package_dir / "model"
    ext_predictor_dir = tmp_path / "ag_raw"
    ext_predictor_dir.mkdir()
    (ext_predictor_dir / "predictor.pkl").write_bytes(b"dummy-ag-data")

    class DummyAGModel:
        def __init__(self, path: Path):
            self.path = str(path)

    pkg_dir = tmp_path / "ag_package"
    save_model_package(DummyAGModel(ext_predictor_dir), metadata, pkg_dir, contract=toy_contract)
    assert (pkg_dir / MODEL_FILENAME).is_dir()
    assert (pkg_dir / MODEL_FILENAME / "predictor.pkl").read_bytes() == b"dummy-ag-data"

    # Przypadek 2: predyktor wytrenowany bezpośrednio w docelowym katalogu package_dir / "model"
    # save_model_package NIE może go usunąć przez rmtree
    in_place_model = DummyAGModel(pkg_dir / MODEL_FILENAME)
    save_model_package(in_place_model, metadata, pkg_dir, contract=toy_contract)
    assert (pkg_dir / MODEL_FILENAME / "predictor.pkl").read_bytes() == b"dummy-ag-data"


def test_validate_package_dir_checks_files_without_loading_model(
    toy_frame, toy_contract, repo_root, tmp_path
):
    pipeline, _ = _make_fitted_toy_pipeline(toy_frame, toy_contract)
    metadata = _make_sample_metadata(toy_contract, repo_root)
    pkg_dir = tmp_path / "pkg"
    save_model_package(pipeline, metadata, pkg_dir, contract=toy_contract)

    with patch("asi_project.model_package.joblib.load") as mock_load:
        validated = validate_package_dir(pkg_dir, contract=toy_contract)
        mock_load.assert_not_called()
        assert validated["dataset"] == "toy"

    with pytest.raises(FileNotFoundError):
        validate_package_dir(tmp_path / "non_existent")


def test_discover_project_packages_parses_requirements(tmp_path):
    (tmp_path / "constraints.txt").write_text(
        "# Komentarz\nnumpy==2.2.6\npandas>=2.0.0\n",
        encoding="utf-8",
    )
    req_dir = tmp_path / "requirements"
    req_dir.mkdir()
    (req_dir / "preflight-s3.txt").write_text(
        "-c ../constraints.txt\nwandb\nautogluon.tabular[lightgbm,catboost]==1.6.3 # inline\n",
        encoding="utf-8",
    )
    packages = _discover_project_packages(tmp_path)
    assert packages == ["numpy", "pandas", "wandb", "autogluon.tabular"]

    versions = get_library_versions(packages=["pytest"], repo_root=tmp_path)
    assert "python" in versions
    assert "pytest" in versions


def test_log_model_package_artifact_does_not_set_production_alias_by_default(
    toy_frame, toy_contract, repo_root, tmp_path
):
    pipeline, _ = _make_fitted_toy_pipeline(toy_frame, toy_contract)
    metadata = _make_sample_metadata(toy_contract, repo_root)
    pkg_dir = tmp_path / "pkg_wandb"
    save_model_package(pipeline, metadata, pkg_dir, contract=toy_contract)

    mock_run = MagicMock()
    mock_wandb = MagicMock()
    with patch.dict("sys.modules", {"wandb": mock_wandb}):
        log_model_package_artifact(pkg_dir, artifact_name="exp-model", run=mock_run)
        mock_run.log_artifact.assert_called_once()
        _, kwargs = mock_run.log_artifact.call_args
        assert "aliases" not in kwargs

        mock_run.reset_mock()
        log_model_package_artifact(
            pkg_dir,
            artifact_name="prod-model",
            aliases=("production",),
            run=mock_run,
        )
        _, kwargs = mock_run.log_artifact.call_args
        assert kwargs.get("aliases") == ["production"]
