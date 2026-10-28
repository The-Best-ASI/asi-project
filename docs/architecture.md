# Architektura systemu

Ten dokument opisuje architekturę systemu zespołu. W Sprincie 1 powstaje diagram v0, który
będzie aktualizowany w kolejnych sprintach.

## Architektura docelowa (scaffold)

Tak wygląda system po sześciu sprintach — na poziomie warstw. To mapa odpowiedzialności,
a nie diagram do skopiowania: diagram v0 (niżej) rysujecie sami.

Relacje między warstwami (opis tekstowy, nie diagram):

- training: dane → pipeline Kedro → artefakt modelu
- serving: UI → API → model (artefakt wczytany przez API)
- state: API → persistence
- deployment: API + UI → Cloud Run

| Warstwa | Odpowiedzialność | Sprint | Miejsce w repozytorium |
|---|---|---|---|
| Dane i kontrakt | źródło danych, kontrakt, input normalization, training-only filtering | S1 | `data/01_raw/`, `src/asi_project/datasets.yaml`, `src/asi_project/data.py` |
| Pipeline | odtwarzalne przetwarzanie i trening od surowych danych | S2 | `conf/`, `src/asi_project/pipelines/` |
| Eksperymenty i artefakt | porównanie runów, wybór modelu, pakiet modelu ładowalny poza treningiem | S3 | W&B, pakiet modelu, `docs/model_card.md` |
| API | kontrakt usługi, walidacja na granicy, model wczytywany raz | S4 | `src/asi_project/api/`, `docker/` |
| Persistence | zapis predykcji poza procesem aplikacji (tryby `sql` / `disabled`) | S4 → S5 → S6 | repository w API, Postgres w compose |
| UI | formularz jako klient API | S5 | `ui/`, `docker/`, `docker-compose.yml` |
| Chmura | wdrożenie, sekret, logi, release | S6 | `deploy/`, Cloud Run, Secret Manager, Cloud Logging |

## Diagram v0 (Sprint 1)

Narysujcie, jak — według waszej obecnej wiedzy — będzie wyglądał system na koniec projektu.
Diagram v0 nie musi być poprawny w szczegółach; ma pokazać wasze rozumienie przepływu.
Sama lista warstw z sekcji wyżej nie wystarcza — diagram pokazuje wasz system i wasze decyzje.

Na diagramie zaznaczcie co najmniej:

- skąd pochodzą dane i gdzie żyje kontrakt danych;
- gdzie działa każdy z trzech typów przetwarzania: input normalization, training-only
  filtering, model preprocessing;
- gdzie powstaje model i jak trafia tam, gdzie wykonuje się predykcja;
- kto lub co wysyła żądanie predykcji i co dostaje w odpowiedzi;
- gdzie przechowywany jest stan (np. zapis predykcji);
- które elementy już istnieją po Sprincie 1, a które są planowane.

Diagram umieśćcie w bloku `mermaid` w sekcji poniżej (GitHub renderuje Mermaid w Markdown)
albo jako obraz w `docs/` z linkiem w tej sekcji. Usuńcie znaczniki TODO, gdy diagram będzie
gotowy — sprawdza to `python scripts/check_dod.py`.

<!-- DIAGRAM-V0:START -->
```mermaid
flowchart LR
    %% SEKCJA: SPRINT 1
    subgraph S_SPRINT1 [Gotowe w Sprincie 1: Trening i Eksperyment]
        DD("Dane (Kaggle)") --> contract("Kontrakt Danych")
        contract --> EDA("EDA")

        subgraph S_BASELINE [BASELINE]
            NI("Normalizing Input") --> FTR("Filter_Training_Rows")
            FTR --> SPLIT("Split<br/>ALLOWED_FEATURES")

            subgraph Numeric [Numeric]
                IMP_MED("Imputer mediana") --> SS("Standard Scaler")
            end

            subgraph Categorical [Categorical]
                IMP_MF("Imputer most-frequent") --> OHE("One Hot Encoder")
            end

            SPLIT --> IMP_MED
            SPLIT --> IMP_MF
        end

        EDA --> NI

        subgraph S_MODEL [MODEL]
            LR("Logistic<br/>Regression")
        end

        SS --> LR
        OHE --> LR

        subgraph S_RESULT [RESULT]
            METRICS("Metrics & Artefakt Modelu")
        end

        LR --> METRICS
    end

    %%SEKCJA: PLANOWANE, PRZYSZŁE KROKI
    subgraph S_PLANNED [Planowane w S2-S6: Serwowanie i Stan]
        UI(("UI (Interfejs)"))
        API{"API (Usługa)"}
        DB[("Baza Danych (Stan)")]
    end


    METRICS -. "Wczytanie wytrenowanego modelu" .-> API
    UI -- "Żądanie predykcji" --> API
    API -- "Wynik predykcji" --> UI
    API -- "Zapis historii" --> DB

    %%STYLOWANIE
    style S_BASELINE fill:#fed7aa,stroke:#ea580c,stroke-width:3px,color:#000
    style S_MODEL fill:#ddd6fe,stroke:#7c3aed,stroke-width:3px,color:#000
    style S_RESULT fill:#bbf7d0,stroke:#16a34a,stroke-width:3px,color:#000

    style Numeric fill:none,stroke:#333,stroke-dasharray: 5 5,stroke-width:2px,color:#000
    style Categorical fill:none,stroke:#333,stroke-dasharray: 5 5,stroke-width:2px,color:#000


    style S_SPRINT1 fill:none,stroke:#16a34a,stroke-width:3px,stroke-dasharray: 5 5
    style S_PLANNED fill:none,stroke:#7c3aed,stroke-width:3px,stroke-dasharray: 5 5
```

Powyższy diagram v0 przedstawia docelowy system wspierający decyzje kredytowe. Obecnie gotowy jest potok treningowy, w
którym dane z Kaggle przechodzą weryfikację kontraktu, wczesną normalizację, filtrowanie i docelowy preprocessing wewnątrz modelu
W kolejnych sprintach planowane jest dodanie środowiska produkcyjnego, w którym zapisany artefakt modelu zostanie wczytany do API.
Interfejs będzie komunikować się z API, a predykcje będą zapisywane w bazie danych
<!-- DIAGRAM-V0:END -->

## Historia zmian architektury

| Sprint | Zmiana | Powiązany ADR |
|---|---|---|
| S1 | diagram v0 | — |
