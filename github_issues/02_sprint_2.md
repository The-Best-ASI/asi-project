# Sprint 2 — Reprodukowalny pipeline

> Treść generowana z `docs/sprints/SPRINT_2.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 29.10.2026 – 12.11.2026

## Cel

W Sprincie 1 przygotowaliście poprawny baseline głównie w notebooku.

Teraz przeniesiecie ten proces do **Kedro**, tak aby cały trening dało się odtworzyć jedną
komendą, bez ręcznego wykonywania komórek notebooka.

Na koniec sprintu:

```bash
kedro run
```

ma przejść przez cały proces:

```text
surowe dane
→ walidacja
→ input normalization
→ training-only filtering
→ split train/test
→ model preprocessing
→ trening modelu
→ ewaluacja
→ zapis modelu i metryk
```

Notebook przestaje być głównym miejscem, w którym „dzieje się” trening. Źródłem prawdy staje
się pipeline w kodzie.

## Definition of Done

- [ ] Kedro działa w przypiętej wersji z `requirements/preflight-s2.txt`.
- [ ] Pipeline `data_processing` wykonuje walidację, input normalization i training-only filtering.
- [ ] Pipeline `data_science` wykonuje split, trening i ewaluację.
- [ ] Pipeline korzysta z logiki przygotowanej w Sprincie 1 zamiast ją duplikować.
- [ ] Model preprocessing nadal znajduje się wewnątrz sklearn `Pipeline`.
- [ ] Parametry są przeniesione do konfiguracji.
- [ ] Data Catalog opisuje wejścia i wyjścia pipeline'u.
- [ ] `conf/ci/` pozwala uruchomić pipeline na próbce CI.
- [ ] Testy nodów przechodzą.
- [ ] `kedro run` na pełnych danych tworzy model i metryki.
- [ ] `kedro run --env ci` działa w CI.
- [ ] Notebook nie jest już wymagany do trenowania baseline'u.
- [ ] ADR-1 jest napisany i zmergowany.
- [ ] README zawiera sekcję „Kedro quickstart”.
- [ ] CI na `main` jest zielone.
- [ ] Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_2.md` w repozytorium.
