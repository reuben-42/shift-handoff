# Build Steps

This is the order everything gets built in. It expands the plan's build plan (docs/PLAN.md, *Build plan*) into one reviewable branch per step.

## How the branches work
- Each step is its own branch, `step-NN-<slug>`, **stacked on the previous step's branch**, so step 3 contains steps 1–2.
- **Nothing is ever pushed to `main`.** Reuben reviews a step branch, edits it if he wants, and merges it into `main` in order (00 → 01 → 02 …). If a step is changed after later steps were branched from it, the later branches get rebased or merged forward before review.
- Every step lists the layer(s) it touches, its files, classes and tests, and a **Done when** line. That's the plan the agent works to. The step isn't done until `make test` and `make lint-arch` pass.
- ✋ marks a step that needs something from Reuben (an account, hardware, a decision, or a merge before going on).

## Status

| # | Branch | Step | Status |
|---|---|---|---|
| 00 | `step-00-plan` | Plan docs, CLAUDE.md, decisions | ✅ pushed |
| 01 | `step-01-skeleton` | Repo skeleton, Makefile, CI, layer linters | ✅ pushed |
| 02 | `step-02-domain-model` | Domain entities, value objects, shift pattern | ⏳ next |
| 03 | `step-03-domain-rules` | ChangeRules, detector, evidence pack, verifiers ✋ | |
| 04 | `step-04-application` | Ports, DTOs, use cases, in-memory fakes | |
| 05 | `step-05-sqlite` | SQLite schema, fixtures, repositories | |
| 06 | `step-06-llm-adapters` | ChatClient, Ollama, PromptBuilder, DraftParser, writer ✋ | |
| 07 | `step-07-api` | FastAPI routers, schemas, composition root | |
| 08 | `step-08-frontend-core` | Frontend domain + application | |
| 09 | `step-09-frontend-ui` | Pages and components on fake gateways | |
| 10 | `step-10-frontend-http` | Generated API types, HTTP gateways → **prototype done** ✋ | |
| 11 | `step-11-synthetic-data` | Synthea import, shift simulator, planted events | |
| 12 | `step-12-remaining-rules` | NewOrder, VitalThreshold, PainIncrease, WeightLoss rules | |
| 13 | `step-13-llm-judge` | ClaimJudge, RecommendationPolicy, amber flags | |
| 14 | `step-14-ack-regenerate` | Acknowledge + Regenerate end to end | |
| 15 | `step-15-eval-harness` | handoff_eval, A→D ablation, metrics, reports | |
| 16 | `step-16-eval-page` | `/api/eval/latest` + `/eval` page | |
| 17 | `step-17-azure-deploy` | Docker, Azure chat client, deploy workflow ✋ | |
| 18 | `step-18-readme-demo` | README results, GIF, demo script ✋ | |
| — | `stretch-*` | Stretch features, only after deploy | |

---

## Phase 0: Plan

### 00 · `step-00-plan`
- **Files:** `CLAUDE.md`, `docs/PLAN.md` (the PDF as Markdown), `docs/BUILD_STEPS.md` (this file), `docs/DECISIONS.md`, `.gitignore`.
- **Done when:** the plan, decisions and build order are in the repo and Reuben agrees with the order.

---

## Phase 1: Prototype (thin slice through every layer)

Prototype scope (from the plan): 5 residents, 1 unit, hand-written fixtures, `MissedDoseRule` + `IncidentRule`, one real local LLM writer, deterministic verification only, board → handoff → source drawer working, `make dev` running, both layer linters passing.

### 01 · `step-01-skeleton`
- **Layers:** all (empty), plus tooling.
- **Backend:** `backend/pyproject.toml` (uv; FastAPI, Pydantic, httpx; dev: pytest, ruff, import-linter), `src/handoff/{domain,application,adapters,infrastructure}/`, `src/handoff_eval/`, `sim/`, `tests/{unit/domain,unit/application,integration,contract,api,fakes}/`, a trivial `/api/health` app so the stack runs.
- **Import-linter contracts:** exactly the three from the plan (layers; inner layers framework-free; the app never imports eval).
- **Frontend:** Vite + React + TS, `src/{domain,application,infrastructure,presentation}/`, `main.tsx`, Tailwind, Vitest, `.dependency-cruiser.cjs` with the plan's rules.
- **Root:** `Makefile` (`dev`, `test`, `lint-arch`, `data`, `eval`, `install`), `.github/workflows/ci.yml` (on every push and PR: ruff, pytest, import-linter, tsc, vitest, depcruise), `.env.example`.
- **Tests:** an arch-guard test that writes a bad import (domain → fastapi) into a temp copy and asserts import-linter fails; the same for dependency-cruiser.
- **Done when:** CI is green on the empty skeleton, and a deliberately bad import makes it fail.

### 02 · `step-02-domain-model`
- **Layer:** domain only.
- **Files:** `domain/entities/` (`Resident`, `Note`, `VitalSign`, `MedAdministration`, `Order`, `Incident`, `Baseline`, `ShiftWindow`, `Change`, `Claim`, `Handoff`, `SbarSection`), `domain/value_objects/` (`SourceId`, `Severity`, `Priority`, `ShiftKind`, `ClaimFlag`, `ShiftDefinition`, `ShiftPattern` + `THREE_EIGHT` / `TWO_TWELVE` presets), `domain/services/shift_calendar.py`.
- **Tests:** `SourceId` accepts N/V/M/O/I and rejects everything else; pattern validation (gaps, overlaps, ≠24 h); night shift crossing midnight; 2×12 windows; `ShiftCalendar` listing.
- **Done when:** every class has unit tests and the domain has zero non-stdlib imports.

### 03 · `step-03-domain-rules` ✋
- **Layer:** domain only.
- **Files:** `domain/rules/` (`ChangeRule` protocol, `MissedDoseRule`, `IncidentRule`), `domain/services/` (`ChangeDetector`, `PriorityCalculator`, `EvidencePackBuilder` → `EvidencePack`, `CitationVerifier`, `CoverageGuard`).
- **Tests:** each rule below, at and above its threshold; the detector runs all rules and sorts by severity; the pack has one line per record (`[V231] 14:35 BP 98/60 HR 88 SpO2 95%`); the citation verifier drops claims citing unknown IDs; the coverage guard appends a templated claim for any uncovered high-severity change.
- ✋ **The plan says to write the ChangeRule classes and verifiers yourself, because interviewers will ask you to explain them line by line.** Choose one: (a) I write them and you study them, or (b) I write the protocol, tests and stubs, and you fill in the bodies until the tests pass.
- **Done when:** every class has unit tests and the domain has zero non-stdlib imports.

### 04 · `step-04-application`
- **Layer:** application (+ `tests/fakes/`).
- **Files:** `application/ports/` (`ResidentReader`, `ClinicalRecordReader`, `HandoffStore`, `HandoffWriter`, `SettingsStore`, `Clock`), `application/dto.py`, `application/errors.py` (`ResidentNotFound`, `HandoffNotFound`, `SourceNotFound`, `InvalidShift`), `application/services/handoff_verifier.py` (deterministic part only), `application/use_cases/` (`GenerateHandoff` with `force`, `GetUnitBoard`, `GetHandoff`, `GetSourceRecord`, `ListShifts`, `GetShiftPattern`, `SetShiftPattern`).
- **Fakes:** `InMemoryResidentReader`, `InMemoryClinicalRecordReader`, `InMemoryHandoffStore`, `InMemorySettingsStore`, `FakeHandoffWriter`, `FixedClock`.
- **Tests:** cache hit vs `force`; the verifier is applied before saving; the board is sorted by priority; switching the pattern changes the windows and cache keys; app errors are raised.
- **Done when:** use-case tests pass with no database and no network.

### 05 · `step-05-sqlite`
- **Layer:** adapters (`persistence/sqlite/`) + `infrastructure/db.py`.
- **Files:** `schema.sql` (residents, notes, vitals, med_admin, orders, incidents, ground_truth, handoffs (+ `pattern`), settings), one class per port (`SqliteResidentReader`, `SqliteClinicalRecordReader`, `SqliteHandoffStore`, `SqliteSettingsStore`), row ↔ entity mappers, `sim/fixtures/unit_2b.json` (5 residents, 24 h of records + 7 days of vitals for baselines, a planted missed dose and a fall), `sim/load_fixtures.py`, `make data`.
- **Tests:** integration tests against a temp SQLite file: window slicing under 3×8 and 2×12, baseline median, handoff save/get by `(resident, shift, pattern)`, settings round-trip.
- **Done when:** integration tests pass against a temp database.

### 06 · `step-06-llm-adapters` ✋
- **Layer:** adapters (`llm/`).
- **Files:** `ChatClient` (adapter-level interface), `OllamaChatClient` (httpx, JSON-schema `format`), `FakeChatClient`, `RecordedChatClient` (replays fixtures), `PromptBuilder` (EvidencePack → messages; the prompt rules from the plan), `DraftParser` (JSON → `HandoffDraft`, rejects bad output), `LlmHandoffWriter`.
- **Tests:** a `HandoffWriter` contract suite run against `FakeHandoffWriter` and `LlmHandoffWriter` + recorded responses; parser rejection cases.
- ✋ You need Ollama installed with `qwen3:8b` pulled (docs/DECISIONS.md). I'll ship a `make record` script that captures real responses into `tests/contract/recordings/`. Run it once on your machine and commit the recordings, because CI never calls a real model.
- **Done when:** the same contract suite passes for the fake writer and the real one (on recorded responses).

### 07 · `step-07-api`
- **Layers:** adapters (`api/`) + infrastructure.
- **Files:** `adapters/api/` (routers: shifts, board, handoffs, sources, settings; `schemas.py` with the plan's output schema as Pydantic; presenters; error handlers mapping app errors → 404/409/422), `infrastructure/config.py` (`LLM_PROVIDER=ollama|fake`, model names, `DB_PATH`, `SHIFT_PATTERN`), `container.py` (the only place concrete classes are constructed), `main.py` (app factory, CORS).
- **Endpoints:** the plan's seven (ack and eval return 501 until steps 14 and 16) plus `GET/PUT /api/settings/shift-pattern`.
- **Tests:** a `TestClient` test for every endpoint; the smoke test board → handoff → source with `LLM_PROVIDER=fake`.
- **Done when:** TestClient tests pass, `/docs` shows the API contract, and you can curl a real handoff.

### 08 · `step-08-frontend-core`
- **Layers:** frontend domain + application.
- **Files:** `domain/handoff.ts` (types), `priority.ts` (`sortByPriority`, `topChange`), `flags.ts` (`isFlagged`, `needsAttention`), `shiftPattern.ts` (labels, formatting in 24-hour time); `application/ports/` (`BoardGateway`, `HandoffGateway`, `SourceGateway`, `AckGateway`, `SettingsGateway`), `application/useCases/` (`loadBoard`, `loadHandoff`, `openSource`, `acknowledgeHandoff`, `loadShifts`, `changeShiftPattern`).
- **Tests:** Vitest, no DOM.
- **Done when:** Vitest is green. (This step depends only on the API contract, so it could have run alongside 02–07.)

### 09 · `step-09-frontend-ui`
- **Layers:** frontend presentation + `infrastructure/fakes/`.
- **Files:** `GatewayProvider`, hooks (`useBoard`, `useHandoff`, `useSource`, `useShifts`, `useShiftPattern`), pages (`BoardPage`, `HandoffPage`), components (`ShiftPicker`, `ShiftPatternControl`, `ResidentCard`, `ChangeList`, `SbarSection`, `ClaimLine`, `SourceChip`, `SourceDrawer`, `DemoBanner`), `sourceRenderers/` (`NoteView`, `VitalsView`, `MedView`, `OrderView`, `IncidentView` + `registry.ts`), `Fake*Gateway` with fixture data.
- **UX rules:** 16 px minimum, 1024 px tablet first, 24-hour times, `j`/`k` between residents, the permanent "Synthetic data. Demo only. Not for clinical use." banner, and an "only residents with changes" toggle.
- **Tests:** React Testing Library with fake gateways: board renders sorted, a chip opens the drawer, switching the pattern refetches.
- **Done when:** you can click through board → handoff → source with no backend running.

### 10 · `step-10-frontend-http` ✋
- **Layer:** frontend infrastructure.
- **Files:** `openapi-typescript` generated types (`make api-types`), `apiClient`, mappers, `Http*Gateway`, the `main.tsx` switch on `VITE_USE_FAKES`; `make dev` runs both apps.
- **Done when:** the same click-through works against the real backend. **Prototype done.**
- ✋ A good point to merge 00–10 into `main`, and to read three handoffs yourself (the plan's milestone check).

---

## Phase 2: After the prototype (the plan's order)

### 11 · `step-11-synthetic-data`
- **Where it lives:** `sim/` (a driver; the app never imports it).
- **Files:** `sim/import_synthea.py` (Patient, active Condition, MedicationRequest, AllergyIntolerance, recent Observation → 20 residents with rooms on unit 2B), `sim/simulate.py` (seeded; 3 days on a 24-hour clock, so any shift pattern can slice it; vitals 3×/day around a per-resident baseline; eMAR at scheduled times with given/refused/held/missed; a daily weight; 1–3 LLM-written notes per 8 h with charting shorthand, typos and chatter), `sim/events.py` (about one planted event per three resident-shifts → `ground_truth` with time + evidence IDs), the `dev` (seed 7) and `test` (seed 42) datasets.
- **Needs:** Java + the Synthea jar (`make synthea` downloads it; output stays out of git). Note generation uses the local model.
- **Done when:** `make data` builds a 20-resident × 3-day DB and the app runs on it unchanged.

### 12 · `step-12-remaining-rules`
- **Layer:** domain + one line each in `container.py`.
- **Files:** `NewOrderRule`, `VitalThresholdRule` (SBP <100 / >160 / ±20 from baseline; HR <50 / >110; SpO2 <92; temp ≥38.0), `PainIncreaseRule` (≥2 above baseline), `WeightLossRule` (≥5 % in 30 days). Thresholds are constructor arguments.
- **Done when:** each rule is tested below, at and above its threshold, and `ChangeDetector` is untouched.

### 13 · `step-13-llm-judge`
- **Layers:** domain (`RecommendationPolicy`), application (`ClaimJudge` port, full `HandoffVerifier`), adapters (`LlmClaimJudge`), UI (amber flag + tooltip).
- **Behaviour:** the judge sees only each claim's cited records; unsupported claims are dropped and logged, partially supported ones are flagged; `RecommendationPolicy` drops recommendations outside the whitelist (monitor / reassess / notify / follow existing orders).
- **Model:** the judge uses a different, stronger model (`gpt-oss:20b`, see DECISIONS.md).
- **Done when:** the judge contract tests pass on recordings and flagged claims render amber.

### 14 · `step-14-ack-regenerate`
- **Files:** the `AcknowledgeHandoff` use case, the `AcknowledgementStore` port + SQLite adapter, `POST /api/handoffs/{id}/ack`, a demo nurse picker (no real login), an acknowledge bar, a ✓ on board cards, a Regenerate button (`force=True`), and a rate limit on regenerate in public mode (5/hour/IP).
- **Done when:** ack persists and shows on the board, and regenerate reruns the pipeline.

### 15 · `step-15-eval-harness`
- **Package:** `src/handoff_eval/` (the only reader of `ground_truth`; import-linter forbids the app from importing it).
- **Files:** the `RunEvaluation` use case, the `GroundTruthReader` port + adapter, variants A–D (A: plain summary; B: + IDs and citations; C: + the rule change list; D: + the verifier), metrics (citation validity, unsupported-claim rate, change recall, false alarms, latency p50/p95, token cost), a CLI `python -m handoff_eval.run --variant D --set test` → `eval/reports/<date>-<variant>.json` + a Markdown table, and a 50-claim hand-labelling CLI for judge agreement.
- **Rule:** tune on `dev` only; `test` is touched only to report.
- **Done when:** the A→D table is generated on `test`.

### 16 · `step-16-eval-page`
- **Files:** `GET /api/eval/latest`, `EvalGateway`, and an `EvalPage` that renders the A→D table.
- **Done when:** `/eval` shows the latest report.

### 17 · `step-17-azure-deploy` ✋
- **Files:** `backend/Dockerfile` (seeded SQLite baked in, handoffs pre-generated at build time), `AzureFoundryChatClient` (one new adapter + one line in the container), `.github/workflows/deploy.yml` (OIDC login; Container Apps for the backend, Static Web Apps for the frontend; deploys on push to `main` only).
- ✋ Needs your Azure for Students account, a budget alert, a Foundry deployment and the OIDC federated credential. If Azure isn't available, the fallback is Ollama inside the container.
- **Cost guardrails:** pre-generated cache, regenerate rate limit, max-token cap.
- **Done when:** a live URL serves the 20-resident unit.

### 18 · `step-18-readme-demo` ✋
- **Files:** the README in the plan's order (pitch, GIF, live link, problem, architecture, eval table, safety design, run locally, what's next), the demo script, and the resume bullet with real numbers.
- ✋ You record the 90-second video.

---

## Phase 3: Stretch (only after step 17 is live)
Each one is its own `stretch-<slug>` branch: HAPI FHIR reader adapter · "Ask about this resident" grounded chat · printable unit handoff sheet · vitals sparklines · spoken readout.
