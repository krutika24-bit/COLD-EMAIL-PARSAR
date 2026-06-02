# The Closer — Cold Email Writer + Send Bot

Sprint 3 project: generate personalized job outreach emails, preview them, and send via SMTP (Gmail) with a full audit log.

## Project layout

```text
COLD-EMAIL-PARSAR/
├── docs/                 # problem statement, architecture, implementation plan
├── phases/               # phase-by-phase code & run scripts (Phase 0–9)
│   ├── phase_00_foundation/
│   ├── phase_01_load_targets/
│   └── ...
├── src/                  # integrated application (Phase 6+)
├── data/contacts.json
├── run.py                # full MVP entry point
├── requirements.txt
└── .env.example
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
# Edit .env — keep DRY_RUN=true until ready to send
```

## Run by phase (teaching)

```bash
python phases/phase_00_foundation/run_phase.py
python phases/phase_01_load_targets/run_phase.py
python phases/phase_02_email_generator/run_phase.py
python phases/phase_03_preview_confirm/run_phase.py
python phases/phase_04_email_sender/run_phase.py
python phases/phase_05_logging/run_phase.py
python phases/phase_06_orchestrator/run_phase.py
```

## Run full MVP

```bash
python run.py
```

## Safety

- Every email is **previewed**; you must confirm before send.
- Default **`DRY_RUN=true`** — no SMTP traffic until you change it.
- **`MAX_SENDS_PER_RUN`** caps volume (default 5).
- Use your **own name and email**; no invented experience.

## Stretch: Groq

Set `USE_LLM=true` and `GROQ_API_KEY` in `.env`, then:

```bash
pip install groq
python phases/phase_09_stretch_groq/run_phase.py
```

## Docs

- [Implementation plan](docs/implementation-plan.md)
- [Architecture](docs/architecture.md)
- [Edge cases](docs/edge-case.md)
- [Phase evaluation](docs/eval.md)

## Sending method

MVP uses **SMTP** (Gmail + App Password). Optional stretch: **Groq** for tone rewrite, Gmail API for drafts.
