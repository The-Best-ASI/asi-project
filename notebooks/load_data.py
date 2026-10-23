from pathlib import Path

import kagglehub
import pandas as pd
from pandas import DataFrame

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "01_raw" / "bank_loan"
TRAIN_FILE = "credit_train.csv"
TEST_FILE = "credit_test.csv"


def load_data(spec_file=None) -> DataFrame | tuple[DataFrame, DataFrame]:
    kagglehub.dataset_download("zaurbegiev/my-dataset", output_dir=str(DATA_DIR))
    if spec_file is not None:
        return pd.read_csv(DATA_DIR / spec_file)
    return (load_data(TRAIN_FILE), load_data(TEST_FILE))
