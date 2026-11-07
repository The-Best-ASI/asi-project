import pandas as pd

from asi_project.config import get_contract, load_project_config
from asi_project.data import (
    assert_valid,
    filter_training_rows,
    normalize_column_names,
    normalize_input,
)


def validate_raw_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """
    Walidacja kontraktu: ujednolica nazwy kolumn i przerywa pipeline przy naruszeniu kontraktu.
    Ujednolicenie nazw kolumn wykonywał w Sprincie 1 ``load_dataset``; teraz dane wczytuje
    Data Catalog, więc robimy to tutaj, przed sprawdzeniem wymaganych kolumn.
    """
    config = load_project_config()
    data = normalize_column_names(raw_data)
    assert_valid(data, get_contract(config), config)
    return data


def normalize_data(validated_data: pd.DataFrame) -> pd.DataFrame:
    """Input normalization — wspólna dla treningu i API."""
    return normalize_input(validated_data)


def filter_training_data(normalized_data: pd.DataFrame) -> pd.DataFrame:
    """Training-only filtering — rekordy bez targetu i duplikaty, tylko przy treningu."""
    contract = get_contract(load_project_config())
    return filter_training_rows(normalized_data, contract)
