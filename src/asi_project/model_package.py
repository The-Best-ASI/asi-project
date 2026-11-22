import json
import os
import platform
import re
import shutil
import subprocess
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib

from asi_project.config import DatasetContract, ProjectConfig, find_repo_root
from asi_project.download import sha256_hex

MODEL_FILENAME = "model"
METADATA_FILENAME = "metadata.json"

_PKG_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)(?:\[[^\]]*\])?\s*(?:[=<>!~]|$|#)")

REQUIRED_METADATA_KEYS = (
    "features",
    "target",
    "positive_class",
    "metrics",
    "git_sha",
    "data_fingerprint",
    "library_versions",
)


def get_git_sha(repo_root: Path | None = None) -> str:
    """Zwraca aktualny skrót Git SHA"""

    env_sha = os.environ.get("GIT_SHA")

    if env_sha:
        return env_sha.strip()
    if shutil.which("git") is None:
        return "unknown"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def get_data_fingerprint(
    config: ProjectConfig,
    contract: DatasetContract,
    data_path: Path | None = None,
) -> str:
    """Zwraca SHA-256 danych treningowych"""

    if data_path is not None and data_path.is_file():
        return sha256_hex(data_path.read_bytes())

    raw_dir = config.root / "data" / "01_raw" / contract.dataset_id
    fingerprint_file = raw_dir / "fingerprint.json"
    if fingerprint_file.is_file():
        try:
            payload = json.loads(fingerprint_file.read_text(encoding="utf-8"))
            sha = payload.get("sha256")
            if isinstance(sha, str) and sha.strip():
                return sha.strip()
        except (json.JSONDecodeError, OSError):
            pass

    raw_csv = raw_dir / contract.download_member

    if raw_csv.is_file():
        return sha256_hex(raw_csv.read_bytes())

    if config.ci_sample_path.is_file():
        return sha256_hex(config.ci_sample_path.read_bytes())

    return "unknown"


def _discover_project_packages(repo_root: Path | None = None) -> list[str]:
    """Odczytuje nazwy pakietów bezpośrednio z constraints.txt oraz requirements"""

    root = repo_root or find_repo_root()
    req_dir = root / "requirements"
    req_files = sorted(req_dir.glob("*.txt")) if req_dir.is_dir() else []
    files = [root / "constraints.txt", *req_files]

    names: list[str] = []
    for path in files:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if match := _PKG_RE.match(line):
                pkg = match.group(1).lower()
                if pkg not in names:
                    names.append(pkg)
    return names


def get_library_versions(
    packages: Sequence[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Zbiera wersję Pythona oraz bibliotek"""

    target_packages = (
        list(packages) if packages is not None else _discover_project_packages(repo_root)
    )
    versions: dict[str, str] = {"python": platform.python_version()}
    for pkg in target_packages:
        try:
            versions[pkg] = version(pkg)
        except PackageNotFoundError:
            continue
    return versions


def build_metadata(
    *,
    contract: DatasetContract,
    config: ProjectConfig,
    metrics: dict[str, Any],
    model_type: str = "sklearn",
    model_version: str = "1.0.0",
    features: Sequence[str] | None = None,
    git_sha: str | None = None,
    data_fingerprint: str | None = None,
    library_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Buduje metadata.json"""

    selected_features = (
        [str(f) for f in features] if features is not None else list(config.model_features)
    )
    resolved_sha = git_sha or get_git_sha(config.root)
    resolved_fingerprint = data_fingerprint or get_data_fingerprint(config, contract)
    resolved_versions = library_versions or get_library_versions(repo_root=config.root)

    return {
        "dataset": contract.dataset_id,
        "model_type": model_type,
        "model_version": model_version,
        "features": selected_features,
        "numeric_features": list(config.numeric_features),
        "categorical_features": list(config.categorical_features),
        "target": contract.target,
        "positive_class": contract.positive_class,
        "metrics": metrics,
        "git_sha": resolved_sha,
        "data_fingerprint": resolved_fingerprint,
        "library_versions": resolved_versions,
    }


def validate_metadata(
    metadata: dict[str, Any],
    contract: DatasetContract | None = None,
) -> list[str]:
    """Sprawdza metadata.json"""

    problems: list[str] = []
    if not isinstance(metadata, dict):
        return ["metadata: oczekiwano słownika JSON."]

    for key in REQUIRED_METADATA_KEYS:
        if key not in metadata:
            problems.append(f"metadata.{key}: brak wymaganego klucza.")

    features = metadata.get("features")
    if (
        not isinstance(features, list)
        or not features
        or not all(isinstance(f, str) and f.strip() for f in features)
    ):
        problems.append("metadata.features: oczekiwana niepusta lista nazw cech (str).")
        features = []

    for str_key in ("target", "positive_class", "git_sha", "data_fingerprint"):
        val = metadata.get(str_key)
        if not isinstance(val, str) or not val.strip():
            problems.append(f"metadata.{str_key}: oczekiwany niepusty napis (str).")

    metrics = metadata.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        problems.append("metadata.metrics: oczekiwany niepusty słownik z metrykami modelu.")

    lib_versions = metadata.get("library_versions")
    if not isinstance(lib_versions, dict) or not lib_versions:
        problems.append("metadata.library_versions: oczekiwany niepusty słownik wersji bibliotek.")

    if contract is not None:
        if metadata.get("target") != contract.target:
            problems.append(
                f"metadata.target: oczekiwano {contract.target!r}, jest {metadata.get('target')!r}."
            )
        if metadata.get("positive_class") != contract.positive_class:
            problems.append(
                f"metadata.positive_class: oczekiwano {contract.positive_class!r}, "
                f"jest {metadata.get('positive_class')!r}."
            )
        disallowed = [name for name in features if name not in contract.allowed_features]
        if disallowed:
            problems.append(f"metadata.features: kolumny spoza ALLOWED FEATURES: {disallowed}.")

    return problems


def _is_autogluon_model(model: Any, metadata: dict[str, Any]) -> bool:
    if metadata.get("model_type") == "autogluon":
        return True
    cls_module = getattr(model.__class__, "__module__", "")
    return cls_module.startswith("autogluon")


def _remove_path(target: Path) -> None:
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


def validate_package_dir(
    package_dir: Path | str,
    contract: DatasetContract | None = None,
) -> dict[str, Any]:
    """Sprawdza strukturę katalogu"""

    package_path = Path(package_dir)
    metadata_path = package_path / METADATA_FILENAME
    model_path = package_path / MODEL_FILENAME

    if not metadata_path.is_file():
        raise FileNotFoundError(f"Brak pliku {METADATA_FILENAME} w pakiecie: {package_path}")
    if not model_path.exists():
        raise FileNotFoundError(
            f"Brak zapisanego modelu '{MODEL_FILENAME}' w pakiecie: {package_path}"
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    problems = validate_metadata(metadata, contract=contract)
    if problems:
        raise ValueError("Wczytane metadane nie spełniają kontraktu:\n" + "\n".join(problems))
    return metadata


def save_model_package(
    model: Any,
    metadata: dict[str, Any],
    package_dir: Path | str,
    contract: DatasetContract | None = None,
) -> Path:
    """Zapisuje pakiet modelu"""

    problems = validate_metadata(metadata, contract=contract)
    if problems:
        raise ValueError("Metadane pakietu modelu nie spełniają kontraktu:\n" + "\n".join(problems))

    package_path = Path(package_dir)
    package_path.mkdir(parents=True, exist_ok=True)
    model_target = package_path / MODEL_FILENAME

    if _is_autogluon_model(model, metadata):
        predictor_path = getattr(model, "path", None)
        if not isinstance(predictor_path, str | os.PathLike):
            raise ValueError("Model AutoGluon nie posiada atrybutu 'path' z zapisanym predyktorem.")
        source_dir = Path(predictor_path).resolve()
        if source_dir != model_target.resolve():
            _remove_path(model_target)
            shutil.copytree(source_dir, model_target)
    else:
        _remove_path(model_target)
        joblib.dump(model, model_target)

    metadata_path = package_path / METADATA_FILENAME
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return package_path


def load_model_package(
    package_dir: Path | str,
    contract: DatasetContract | None = None,
) -> tuple[Any, dict[str, Any]]:
    """waliduje pakiet modelu z katalogu"""

    package_path = Path(package_dir)
    metadata = validate_package_dir(package_path, contract=contract)
    model_path = package_path / MODEL_FILENAME

    if model_path.is_dir() or metadata.get("model_type") == "autogluon":
        from autogluon.tabular import TabularPredictor

        model = TabularPredictor.load(str(model_path))
    else:
        model = joblib.load(model_path)

    return model, metadata


def log_model_package_artifact(
    package_dir: Path | str,
    artifact_name: str = "model-package",
    aliases: Sequence[str] = (),
    run: Any | None = None,
) -> Any:
    """Zapisuje katalog modelu jako W&B"""

    import wandb

    package_path = Path(package_dir)
    metadata = validate_package_dir(package_path)

    active_run = run or wandb.run
    if active_run is None:
        raise RuntimeError(
            "Brak aktywnego runu W&B. Uruchom wandb.init() lub przekaż obiekt 'run'."
        )

    artifact = wandb.Artifact(
        name=artifact_name,
        type="model",
        metadata=metadata,
    )
    artifact.add_dir(str(package_path))
    if aliases:
        active_run.log_artifact(artifact, aliases=list(aliases))
    else:
        active_run.log_artifact(artifact)
    return artifact


def download_model_package_artifact(
    artifact_ref: str,
    target_dir: Path | str | None = None,
) -> Path:
    """Pobiera W&B Artifact z pakietem modelu"""

    import wandb

    if wandb.run is not None:
        artifact = wandb.run.use_artifact(artifact_ref, type="model")
    else:
        api = wandb.Api()
        artifact = api.artifact(artifact_ref, type="model")

    root = str(target_dir) if target_dir is not None else None
    downloaded_dir = artifact.download(root=root)
    return Path(downloaded_dir)
