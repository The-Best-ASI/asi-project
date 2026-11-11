# conf/ci

Uruchomienie: `kedro run --env ci` (konfiguracja `base` + `ci`).

- `catalog.yml`: `raw_data` czyta `data/01_raw/sample.csv`, wyniki idą do plików z
  sufiksem `_ci`, więc nie nadpisują wyników z pełnych danych.
- `parameters.yml`: `data_mode: "sample"`.

Nadpisania dla środowiska `ci`: te same pipeline'y uruchamiane na próbce
`data/01_raw/sample.csv`. Od Sprintu 3 także wyłączenie zewnętrznych usług w CI
(`WANDB_MODE=disabled`, AutoGluon wyłączony parametrem albo z kilkusekundowym limitem).
