import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psutil

BYTES_IN_MB = 1024 * 1024


def path_size_mb(path: Path | str) -> float:
    path = Path(path)
    if path.is_file():
        total = path.stat().st_size
    else:
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / BYTES_IN_MB, 2)


def _rss_after_load_mb(kind: str, path: str) -> float:
    if kind == "autogluon":
        from autogluon.tabular import TabularPredictor

        model = TabularPredictor.load(path)
        model.persist()
    else:
        import joblib

        model = joblib.load(path)
    rss = psutil.Process().memory_info().rss
    del model
    return round(rss / BYTES_IN_MB, 2)


_LOAD_SCRIPT = (
    "import sys; from asi_project.system_metrics import _rss_after_load_mb; "
    "print(_rss_after_load_mb(sys.argv[1], sys.argv[2]))"
)


def load_memory_mb(path: Path | str, kind: str) -> float:
    result = subprocess.run(
        [sys.executable, "-c", _LOAD_SCRIPT, kind, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip().splitlines()[-1])


def timed(func: Callable[[], Any]) -> tuple[Any, float]:
    start = time.perf_counter()
    result = func()
    return result, round(time.perf_counter() - start, 4)


def system_metrics(
    prediction_time: float, artifact_path: Path | str, kind: str
) -> dict[str, float]:
    return {
        "prediction_time_seconds": prediction_time,
        "artifact_size_mb": path_size_mb(artifact_path),
        "load_memory_mb": load_memory_mb(artifact_path, kind),
    }
