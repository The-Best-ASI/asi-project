# Sprint 6 — Wdrożenie do Cloud Run, obserwowalność i release

> Treść generowana z `docs/sprints/SPRINT_6.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 07.01.2027 – 21.01.2027

## Cel

Macie już lokalny system z:

```text
Streamlit UI
    ↓
FastAPI
    ↓
PostgreSQL
```

W ostatnim sprincie wdrożycie API i UI do **Google Cloud Run**.

Na koniec kursu:

- API działa pod publicznym adresem;
- UI działa pod publicznym adresem;
- `API_KEY` jest pobierany z Secret Managera;
- aplikacja działa z jawnym trybem persistence;
- logi są widoczne w Cloud Logging;
- smoke test przechodzi na wdrożonych usługach;
- dokumentacja jest aktualna;
- projekt ma release `v1.0`;
- zespół potrafi zademonstrować cały system.

## Definition of Done

### release candidate — 14.01

- [ ] API jest wdrożone do Cloud Run.
- [ ] UI jest wdrożone do Cloud Run.
- [ ] Obrazy są zgodne z `linux/amd64`.
- [ ] API korzysta z `$PORT`.
- [ ] `API_KEY` znajduje się w Secret Managerze.
- [ ] API otrzymuje `API_KEY` przez integrację z Secret Managerem.
- [ ] UI otrzymuje `API_KEY` przez integrację z Secret Managerem.
- [ ] Persistence w chmurze jest ustawione jawnie.
- [ ] Przy braku zewnętrznej bazy działa `persistence = disabled`.
- [ ] SQLite w Cloud Run jest zablokowany.
- [ ] `/healthz` działa.
- [ ] Smoke test na publicznym URL API przechodzi.
- [ ] Manualny UI check przechodzi.
- [ ] Logi predykcji są widoczne w Cloud Logging.

### finał — 21.01

- [ ] Finalny smoke test przechodzi.
- [ ] Finalny manualny UI check przechodzi.
- [ ] README jest aktualne.
- [ ] Model Card jest aktualna.
- [ ] ADR-3 jest finalny.
- [ ] `deploy.sh` odpowiada rzeczywistemu deploymentowi.
- [ ] W repozytorium nie ma sekretów.
- [ ] Release notes są przygotowane.
- [ ] Release `v1.0` jest utworzony.
- [ ] Zespół jest gotowy do demo.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_6.md` w repozytorium.
