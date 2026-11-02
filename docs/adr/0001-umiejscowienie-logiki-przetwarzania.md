# ADR-1: Podział i umiejscowienie logiki przetwarzania danych

- **Status:** proponowany
- **Sprint:** S2
- **Autor:** Frank Schweizer
- **Recenzent:** imię i nazwisko (zostawiam puste dla osoby co robi review)

## Kontekst

W Sprincie 2 przenosimy proces trenowania baseline'u przewidującego `Loan Status` z Jupyter Notebooka do  pipeline'u w
frameworku Kedro. Musimy ustalić, w których węzłach powinny znajdować się poszczególne przekształcenia danych, aby
uniknąć wycieku danych (data leakage) ze zbioru testowego do treningowego oraz zachować parametry podziału bez
duplikowania logiki.
## Rozważone opcje

1. **Globalny węzeł Kedro** — umieszczenie wszystkich transformacji (czyszczenie, imputacja braków, skalowanie) w jednym,
wielkim nodzie uruchamianym na całych danych zaraz przed podziałem na train/test.
2. **Warstwowy podział** — rozbicie logiki na 3 warstwy opierające się o bezstanowość funkcji dla nowych predykcji oraz
moment dopasowania (`fit()`).

## Decyzja

Wybieramy **Warstwowy podział**. Opiera się on na perspektywie predykcji pojedynczego, nowego rekordu w środowisku produkcyjnym.

1. **Input normalization** znajduje się w funkcji `normalize_input()` w module `src/asi_project/data.py` i działa jako
pierwszy węzeł pipeline'u `data_processing`. Funkcja wykonuje transformacje nieoparte o statystyki grupy (np. rzutowanie
wartości 99999999 na brak danych w `Current Loan Amount`, standaryzacja napisu z "other" na "Other" w `Purpose` czy
dzielenie wyników czterocyfrowych `Credit Score` przez 10).

2. **Training-only filtering:** funkcja `filter_training_rows()` w pipeline `data_processing`. Żyje tutaj, by odfiltrować
śmieci przed treningiem (usuwa rekordy bez targetu i duplikaty `Loan ID`), nie mając wpływu na późniejsze predykcje.

3. **Model preprocessing** (np. `SimpleImputer` uzupełniający braki medianą, `StandardScaler`, `OneHotEncoder`) został
zapięty jako składowa sklearnowego `ColumnTransformer`, który wraz z ostatecznym klasyfikatorem znajduje się w obiekcie
`sklearn.pipeline.Pipeline` zdefiniowanym w `src/asi_project/model.py`.

| Wielkość | Wartość | Skąd pochodzi |
|---|---|---|
| Rozmiar zbioru po Training-only filtering | 81 999 rekordów (odrzucono 18 515) | EDA: różnica liczebności `df_raw` i wyniku odrzucania braków targetu oraz duplikatów `Loan ID`. |
| Bazowe F1-score dla Logistic Regression | 0.465 | Artefakt `metrics.json` wygenerowany z ewaluacji modelu na zbiorze |

## Odrzucone alternatywy


Odrzuciliśmy **Globalny czyszczący węzeł Kedro**

**Powód odrzucenia:** Poddanie surowych danych statystycznej imputacji i skalowaniu przed użyciem `train_test_split`
skutkuje wyciekiem informacji ze zbioru testowego do treningowego, co zakłamuje metrykę oceny modelu.
## Konsekwencje

- **Co ułatwia:** Wdrożenie produkcyjne. Wyjściowy model to samowystarczalny artefakt scikit-learn. Metoda `predict()` poradzi sobie z brakami i nowymi kategoriami w oparciu o stany zapamiętane podczas `fit()`.
- **Co utrudnia:** Wymaga zachowania dyscypliny. Należy pilnować, aby do `normalize_input()` nikt nie przemycił reguł korzystających z metody `.mean()` (złamie to bezstanowość predykcji).
- **Co w kolejnych sprintach:** Podczas stawiania serwera API (S4) konieczny będzie bezpośredni import modułu `src/asi_project/data.py`, by wszystkie zapytania klientów przepuszczać przez to samo normalizowanie przed wysłaniem ich do `sklearn.Pipeline`.

## Historia

| Data       | Zmiana |
|------------|---|
| 01.11.2026 | utworzenie |
