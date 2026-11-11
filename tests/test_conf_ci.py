"""Środowisko Kedro `ci`: pipeline'y czytają próbkę z gita i nie nadpisują wyników z base."""

from kedro.config import OmegaConfigLoader

from asi_project.settings import CONFIG_LOADER_ARGS


def _config(repo_root, env):
    return OmegaConfigLoader(
        str(repo_root / "conf"), **{**CONFIG_LOADER_ARGS, "default_run_env": env}
    )


def test_ci_reads_sample_and_writes_separate_outputs(repo_root):
    base = _config(repo_root, CONFIG_LOADER_ARGS["base_env"])
    ci = _config(repo_root, "ci")

    assert ci["catalog"]["raw_data"]["filepath"] == "data/01_raw/sample.csv"
    assert (repo_root / "data/01_raw/sample.csv").is_file()
    assert ci["parameters"]["data_mode"] == "sample"

    for name, dataset in base["catalog"].items():
        if name != "raw_data":
            assert ci["catalog"][name]["filepath"] != dataset["filepath"], name
