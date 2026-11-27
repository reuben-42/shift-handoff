# Shift Handoff Copilot — Build Plan

*Nov 26, 2026 · Reuben Mathew*

> Markdown export of the original PDF build plan. Decisions taken after it was written are in [DECISIONS.md](DECISIONS.md), and the step-by-step branch order is in [BUILD_STEPS.md](BUILD_STEPS.md).

## Overview

Build a web app that turns one shift of a nursing-home resident's chart into a 30-second handoff for the next nurse. Every sentence links to the record it came from, and an evaluation proves with numbers how rarely it makes things up.

- **The problem:** at shift change, the outgoing nurse briefs the incoming nurse on every resident, often from memory and in a rush. Missed details (a fall, a refused dose, a blood pressure drop) are a patient-safety risk.
- **The product:** the app reads the notes, vitals and medication records (eMAR) that already exist in the chart. It writes one SBAR handoff per resident (Situation, Background, Assessment, Recommendation), with "what changed" first.
- **What it is not:** a notes app. Nurses never type anything into it, because asking them to chart twice is how healthcare tools die.
- **Users:** the incoming nurse reads the handoffs; the outgoing nurse reviews them and marks them read.

**Done means:**
- A live URL with a 20-resident synthetic unit and pre-generated handoffs
- Clicking any sentence shows its source record
- A README results table: unsupported-claim rate and change recall, before and after the verifier
- A 90-second demo video

**Why it fits PointClickCare:** it uses Azure, Azure AI Foundry and React, the exact stack in the Software Engineer posting. It also pulls from several data sources into AI-generated output, which is the core of the Systems Developer and AI Automation postings.

## Scope

Ship the MVP end to end before touching any stretch feature. A deployed, measured MVP impresses more than a half-built version with extras.

**MVP (must ship)**
- Synthetic unit: 20 residents × 3 days × 3 shifts
- Rules-based change detection (missed meds, falls, abnormal vitals, weight loss)
- SBAR handoff generation with a source ID on every claim
- A verifier that drops or flags unsupported claims
- Unit board, resident handoff view, source drawer, and an "I've read this" acknowledgement
- Evaluation harness with a four-variant comparison (ablation)
- Deployed on Azure, auto-deployed from GitHub on every push to main

**Stretch (only after the MVP is deployed)**
- Read from a real FHIR server (HAPI FHIR) instead of the SQLite import
- "Ask about this resident": a chat grounded on the same evidence, with the same citation rule
- Printable one-page handoff sheet for the whole unit
- Vitals trend sparklines on each resident card
- Spoken handoff readout (ElevenLabs)

**Non-goals**
- Real patient data, ever
- Diagnoses, or new medication or dose suggestions
- Real login and accounts (a demo nurse picker is enough)
- A mobile app, or replacing the chart itself

## Rule #1: Clean Architecture and SOLID

The backend and the frontend both use the same four layers, and dependencies only ever point inward. This is non-negotiable: CI fails the build if any code breaks it, so neither you nor the coding agent can quietly go around it.

**Every dependency points inward, toward the domain.** Arrows mean "depends on". Outer layers are swappable; the domain imports nothing.

| Layer | Backend | Frontend |
|---|---|---|
| **Frameworks and drivers** (outermost, swappable details) | FastAPI app, SQLite engine, Azure SDK, config, wiring | Vite, main.tsx (wiring), TanStack Query client |
| **Interface adapters** (translate in and out) | API routers, SQLite repositories, LLM writer and judge | HTTP gateways, API mappers, pages and components |
| **Application** (use cases + the ports they own) | GenerateHandoff, GetUnitBoard, AcknowledgeHandoff | loadBoard, loadHandoff, acknowledge + gateway ports |
| **Domain** (pure rules, imports nothing) | Resident, Handoff, Claim, ChangeRule, CitationVerifier | handoff types, priority sorting, flag rules |

Ports are interfaces owned by Application; adapters implement them. That is dependency inversion.

**The dependency rule, in plain words.** Think of an onion. The core (Domain) holds the rules of nursing handoffs, like "a missed dose is high severity". Those rules would still be true if you deleted FastAPI, React and Azure tomorrow. Each outer layer can use the layers inside it, but an inner layer never knows the outer ones exist.

- **Domain:** entities and pure business rules. Plain Python and TypeScript only.
- **Application:** use cases that run one user action start to finish. They declare what they need from the outside world as interfaces called ports, like "something that can write a handoff".
- **Interface adapters:** translate between the outside world and those ports: HTTP into use-case calls, SQL rows into entities, LLM JSON into claims.
- **Frameworks and drivers:** FastAPI, SQLite, the Azure SDK, React's root. Swappable details.

**How each SOLID principle shows up**

| Principle | In this project |
|---|---|
| Single responsibility | One class per change rule. `PromptBuilder` only builds prompts; `AzureFoundryHandoffWriter` only calls the model. Routers only translate HTTP. |
| Open/closed | A new rule is a new `ChangeRule` class registered in the composition root; `ChangeDetector` is never edited. On the frontend, a new record kind is a new renderer in a registry; `SourceDrawer` is never edited. |
| Liskov substitution | Every `HandoffWriter` (Azure, Ollama, fake) passes the same contract test suite, so a use case can't tell them apart. |
| Interface segregation | Small ports: `ClinicalRecordReader`, `HandoffStore` and `AcknowledgementStore` instead of one giant repository. On the frontend, `BoardGateway`, `HandoffGateway`, `SourceGateway` and `AckGateway`. |
| Dependency inversion | Use cases depend on ports (Python `Protocol`, TypeScript `interface`). Concrete classes are built only in the composition root (`container.py`, `main.tsx`) and handed in through constructors or React context. |

**Hard rules**
- Domain imports only the standard library: no Pydantic, FastAPI, SQL or SDKs. Entities are frozen dataclasses.
- Application imports only Domain. Every port lives in Application.
- Framework and SDK types never cross into Application. Adapters map them at the boundary.
- Concrete classes are constructed only in the composition root.
- No business logic in routers, React components, SQL or prompts.

**Enforced in CI**
- Backend: `import-linter` with a layers contract (infrastructure → adapters → application → domain). A violation fails the build.
- Frontend: `dependency-cruiser` rules. Domain imports nothing; application imports domain only; presentation never imports infrastructure; only `main.tsx` may import infrastructure.
- Every PR answers one question: which layer does this change live in, and why?

## Architecture

An offline step builds the data, a five-stage pipeline turns each resident's shift into a handoff, FastAPI serves it to React, and an eval harness scores it.

**Rules find the changes, the LLM words them, a verifier checks each claim.**

```
Data built offline:     Synthea patients ──▶ Shift simulator ──▶ SQLite database
                        (fake FHIR records)   (notes, vitals,     (+ planted events)
                                               eMAR)                      │
                                                                          ▼
Per-resident pipeline:  Change detector ──▶ Evidence pack ──▶ LLM writer ──▶ Verifier
                        (rules, no AI)      (IDs on every     (SBAR JSON     (drops
                                             record)           + sources)    unsupported)
                                                                                 │
                                                                                 ▼
Serve and measure:      React app ◀── FastAPI backend ◀── Saved handoffs ──▶ Eval harness
                        (nurse view)  (serves the API)    (per resident,     (vs the
                                                            shift)            answer key)
```

Only the LLM writer uses AI at request time. Detection is rules and verification is checks plus a judge, so the AI's job is limited to wording.

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript (Vite) | The SWE posting asks for a modern UI framework |
| Backend | Python + FastAPI | Your strongest language; REST, like the Systems Developer posting |
| Data | SQLite (Postgres as a stretch goal) | Zero setup, ships inside the container |
| AI | Azure AI Foundry behind an LLM interface; Ollama locally | Named in the SWE posting; swappable providers |
| Hosting | Azure Static Web Apps + Azure Container Apps | Azure-backed production, like the postings |
| CI/CD | GitHub Actions | Ships on every push to main |
| Synthetic data | Synthea (FHIR R4) | FHIR is the healthcare data-exchange standard |

## Data

Synthea supplies realistic residents and their medical history. A shift simulator you write adds the nursing-home shift data and plants known events, which gives the evaluation an answer key.

Synthea doesn't produce nursing notes, shift vitals or eMAR events, so the simulator fills that gap. Because you planted every important event, you know exactly what a perfect handoff should mention.

1. **Generate residents with Synthea.** Run it seeded and age-filtered, for example `java -jar synthea-with-dependencies.jar -s 42 -p 60 -a 70-95`. It writes FHIR R4 bundles to `output/fhir/`. Keep them out of git.
2. **Import (`sim/import_synthea.py`).** Parse Patient, active Condition, active MedicationRequest, AllergyIntolerance and recent Observation resources. Pick 20 patients and give each a room number on one unit.
3. **Simulate shifts (`sim/simulate.py`, seeded).** For each resident, 3 days × 3 shifts (Day 07:00–15:00, Evening 15:00–23:00, Night 23:00–07:00):
   - Vitals once per shift around a per-resident baseline, with noise
   - eMAR: each active med scheduled (e.g. 08:00, 17:00, 21:00), with status given, refused, held or missed
   - 1–3 nursing notes per shift, written by an LLM from that shift's events at simulation time. Ask for realistic charting shorthand ("pt", "c/o", "PRN given") and some irrelevant chatter so the notes aren't suspiciously clean
   - A daily weight
4. **Plant events (`sim/events.py`).** About one per three resident-shifts: fall, refused dose twice, BP or SpO2 out of range, new antibiotic order, weight down 5% or more in 30 days, new pain, family concern. Save each to `ground_truth` with its type, time and the record IDs that evidence it.

**Data model (SQLite)**

| Table | Key fields |
|---|---|
| residents | id, name, room, age, conditions, allergies, code_status |
| shifts | id, unit, date, kind (day / evening / night), start, end |
| notes | id (N…), resident_id, shift_id, time, author_role, text |
| vitals | id (V…), resident_id, time, bp_sys, bp_dia, hr, temp_c, rr, spo2, pain_0_10, weight_kg |
| med_admin | id (M…), resident_id, time, med, dose, status, reason |
| orders | id (O…), resident_id, time, type, text |
| incidents | id (I…), resident_id, time, type, text |
| ground_truth | id, resident_id, shift_id, event_type, evidence_ids |
| handoffs | id, resident_id, shift_id, json, model, created_at, acknowledged_by, acknowledged_at |

The letter prefixes (N, V, M, O, I) are the source IDs the model cites, so a citation tells you at a glance what kind of record it points to.

**Slicing by shift:** a handoff's evidence is every record with a time inside the shift window, plus context: the 7-day vitals median as the baseline, active conditions, active meds and allergies.

`ground_truth` is never shown to the handoff pipeline. Only the eval harness reads it.

## Handoff pipeline

Rules decide what changed, the LLM only turns it into readable sentences, and a verifier checks every claim before a nurse sees it. That split is the safety story: the risky judgement is deterministic and testable, not hidden in a prompt.

1. **Gather (`application: GenerateHandoff`).** Load the shift's records and the baseline context for one resident.
2. **Detect changes (`domain: ChangeDetector`, no AI).** Each rule returns a `Change` with a severity (high / medium / low) and the evidence IDs that triggered it. The thresholds below are demo defaults, not clinical guidance:
   - Any dose missed, refused or held
   - Any incident (fall, skin issue, behaviour)
   - Any new order
   - Systolic BP under 100 or over 160, or 20+ away from the resident's baseline
   - HR under 50 or over 110; SpO2 under 92%; temperature 38.0 °C or higher
   - Pain score 2+ points above baseline
   - Weight down 5% or more in 30 days (the same threshold the MDS assessment uses)
3. **Build the evidence pack (`domain: EvidencePackBuilder`).** One compact line per record, prefixed with its ID, e.g. `[V231] 14:35 BP 98/60 HR 88 SpO2 95%`, followed by the detected changes and their IDs.
4. **Generate (`HandoffWriter port, LlmHandoffWriter adapter`).** Call the LLM with structured output that must match the schema below. Prompt rules:
   - Use only the evidence pack
   - Every claim cites at least one ID
   - Put the detected changes first
   - If nothing notable happened, say "No changes this shift"
   - Recommendations are limited to monitor, reassess, notify the physician or family, or follow existing orders. Never new meds, doses or diagnoses
5. **Verify (`application: HandoffVerifier`).**
   - Deterministic checks: every cited ID exists in this resident's pack. Every high-severity change is covered by at least one claim; if not, append a templated claim built from the rule's output.
   - LLM judge per claim, shown only that claim's cited records: supported, partially supported or unsupported. Unsupported claims are dropped and logged; partly supported ones are flagged amber in the UI.
6. **Save and serve.** One handoff per resident per shift, cached in `handoffs`. A Regenerate button reruns the pipeline.

**Output schema** (also the Pydantic model in `adapters/api/schemas.py`)

```json
{
  "resident_id": "R07",
  "shift_id": "2026-12-03-day",
  "priority": "high",
  "changes": [
    {"text": "Unwitnessed fall at 14:20, no visible injury", "severity": "high", "sources": ["I12", "N88"]}
  ],
  "sbar": {
    "situation": [{"text": "Found on floor beside bed at 14:20", "sources": ["I12"]}],
    "background": [{"text": "Started amlodipine 5 mg two days ago", "sources": ["O31"]}],
    "assessment": [{"text": "BP 98/60, below her usual ~130/80", "sources": ["V231"], "flag": null}],
    "recommendation": [{"text": "Check BP before she stands; flag to physician in the morning", "sources": ["V231", "O31"]}]
  },
  "verification": {"claims_checked": 9, "dropped": 1, "flagged": 0}
}
```

## Backend design

Build the backend inside out: domain first with pure unit tests, then use cases against in-memory fakes, then adapters, then the composition root that wires them together. Every pipeline step above has exactly one home.

**Where each pipeline step lives**

| Step | Layer | Class |
|---|---|---|
| Gather | Application | `GenerateHandoff` reads through the `ClinicalRecordReader` port |
| Detect changes | Domain | `ChangeDetector`, holding one `ChangeRule` class per rule |
| Evidence pack | Domain | `EvidencePackBuilder` → `EvidencePack` (IDs + facts). Turning it into prompt text is an adapter job (`PromptBuilder`) |
| Generate | Port in Application, implementation in Adapters | `HandoffWriter` → `LlmHandoffWriter` |
| Verify (deterministic) | Domain | `CitationVerifier`, `CoverageGuard`, `RecommendationPolicy` |
| Verify (judge) | Port in Application, implementation in Adapters | `ClaimJudge` → `LlmClaimJudge` |
| Save and serve | Application + Adapters | `HandoffStore` → `SqliteHandoffStore`; FastAPI router + presenter |

**Domain (`domain/`): no imports outside the standard library**
- Entities (frozen dataclasses): `Resident`, `Shift`, `ShiftWindow`, `Baseline`, the source records (`Note`, `VitalSign`, `MedAdministration`, `Order`, `Incident`), `Change`, `Claim`, `Handoff`
- Value objects: `SourceId` (validates the N/V/M/O/I prefix), `Severity`, `Priority`, `ShiftKind`
- Rules: a `ChangeRule` protocol with `evaluate(window, baseline) -> list[Change]`, implemented by `MissedDoseRule`, `IncidentRule`, `NewOrderRule`, `VitalThresholdRule`, `PainIncreaseRule` and `WeightLossRule`. Thresholds are constructor arguments, so tests and config can set them
- Services: `ChangeDetector`, `EvidencePackBuilder`, `CitationVerifier`, `CoverageGuard`, `RecommendationPolicy`, `PriorityCalculator`

**Application (`application/`): use cases, ports, DTOs**
- Ports, kept small: `ResidentReader`, `ShiftReader`, `ClinicalRecordReader`, `HandoffStore`, `AcknowledgementStore`, `HandoffWriter`, `ClaimJudge`, `Clock`
- Use cases, one action each: `GenerateHandoff` (with a `force` flag for Regenerate), `GetUnitBoard`, `GetHandoff`, `GetSourceRecord`, `AcknowledgeHandoff`
- `HandoffVerifier`: an application service that combines the domain checks with the `ClaimJudge` port. It lives here because it needs a port
- Plain dataclass DTOs in and out, plus app errors (`ResidentNotFound`, `HandoffNotFound`) that adapters translate into HTTP codes

The central use case, to show the shape:

```python
# application/ports/llm.py
class HandoffWriter(Protocol):
    def write(self, pack: EvidencePack) -> HandoffDraft: ...

# application/use_cases/generate_handoff.py
class GenerateHandoff:
    def __init__(self, records: ClinicalRecordReader, detector: ChangeDetector,
                 packer: EvidencePackBuilder, writer: HandoffWriter,
                 verifier: HandoffVerifier, store: HandoffStore) -> None:
        ...

    def execute(self, cmd: GenerateHandoffCommand) -> HandoffDTO:
        if not cmd.force and (cached := self._store.get(cmd.resident_id, cmd.shift_id)):
            return HandoffDTO.from_entity(cached)
        window, baseline = self._records.shift_window(cmd.resident_id, cmd.shift_id)
        changes = self._detector.detect(window, baseline)
        pack = self._packer.build(window, baseline, changes)
        draft = self._writer.write(pack)
        handoff = self._verifier.verify(draft, pack, changes)
        self._store.save(handoff)
        return HandoffDTO.from_entity(handoff)
```

Nothing in that file knows about FastAPI, SQLite or Azure, so you can test it in milliseconds with fakes.

**Interface adapters (`adapters/`)**
- `api/`: one router per resource (board, handoffs, sources, eval), Pydantic request and response schemas, presenters that map DTOs to schemas, and an error handler that maps app errors to 404 / 409
- `persistence/sqlite/`: one class per port (`SqliteClinicalRecordReader`, `SqliteHandoffStore` and so on), each with a row → entity mapper
- `llm/`: `PromptBuilder` (EvidencePack → messages), `DraftParser` (model JSON → `HandoffDraft`, rejecting bad output), and `LlmHandoffWriter` / `LlmClaimJudge`. Both depend on a small adapter-level `ChatClient` interface implemented by `AzureFoundryChatClient` and `OllamaChatClient`, so adding a provider never touches the writer

**Frameworks and drivers (`infrastructure/`)**
- `config.py`: settings from env vars (`LLM_PROVIDER=ollama|azure|fake`, model names, DB path)
- `db.py`: the SQLite connection factory
- `container.py`: **the composition root**, the only file that constructs concrete classes. It reads config, builds adapters, and injects them into use cases
- `main.py`: the FastAPI app factory. Routers get use cases from the container through `Depends`

**Simulator and eval sit outside the app**
- `sim/` is a driver that writes the database. It may reuse domain entities, but the app never imports it.
- `handoff_eval/` is a separate package with its own `RunEvaluation` use case and a `GroundTruthReader` port. import-linter forbids the app from importing it, so ground truth can never leak into handoff generation.

**Tests per layer**

| Layer | Tests | Rule |
|---|---|---|
| Domain | Plain unit tests, no mocks | Every rule tested below, at and above its threshold |
| Application | Use-case tests with in-memory fakes from `tests/fakes/` | No database, no network |
| Adapters | Temp-SQLite integration tests; one contract suite every `HandoffWriter` must pass; FastAPI `TestClient` tests | LLM tests replay recorded responses, so CI never calls a real model |
| Whole app | One smoke test: board → handoff → source with `LLM_PROVIDER=fake` | Runs on every push |

## Evaluation harness

The simulator's planted events are the answer key, so most scoring is automatic. A 50-claim sample that you label by hand checks that the LLM judge can be trusted.

**Metrics**

| Metric | How it's measured | Goal |
|---|---|---|
| Citation validity | Cited IDs that exist in the resident's pack ÷ all cited IDs (deterministic) | 100% |
| Unsupported-claim rate | Claims the judge labels unsupported ÷ all claims | Under 2% after the verifier |
| Change recall | Planted events mentioned with a correct source ÷ planted events | 95%+ for high severity |
| False alarms | High-severity changes with no planted or rule-detected event behind them | Report the count |
| Judge agreement | Your labels vs the judge's on 50 claims | Report the % |
| Latency | Seconds per handoff, p50 and p95 | Report |
| Cost | Tokens × price per handoff | Report |

**Ablation: four variants on the same test set**

| Variant | What it adds |
|---|---|
| A | Plain "summarize this shift" prompt, no IDs |
| B | Evidence IDs and required citations |
| C | B + the rules-based change list |
| D | C + the verifier (the shipped version) |

Variant A has no citations, so its judge checks each claim against the whole evidence pack. The A → D table is the headline result for your README and interviews.

**Rules**
- Two seeded datasets: `dev` (seed 7) to iterate on, `test` (seed 42, 60 resident-shifts) touched only to report. Tuning prompts on the test set makes the numbers meaningless.
- Use a different, stronger model for the judge than for the writer, so the writer isn't grading itself.
- `python -m handoff_eval.run --variant D --set test` writes `eval/reports/<date>-<variant>.json` plus a markdown table ready to paste into the README.

## Frontend

Four screens, designed for a tired nurse on a medication-cart tablet: the most urgent resident first, what changed at the top, and any fact traceable to its source in one tap.

1. **Unit board.** A shift picker (date + Day / Evening / Night) and resident cards sorted by priority. Each card shows room, name, age, a priority badge, the single most important change, and a tick once acknowledged. Toggle: "only residents with changes".
2. **Resident handoff.** "What changed" on top as red or amber rows, then the S, B, A and R sections. Every sentence ends in source chips like `[N88]` `[V231]`. Flagged claims are amber, with a tooltip saying "only partly supported by its sources".
3. **Source drawer.** Tapping a chip slides in the record from the right: the full note with the record highlighted, or the shift's vitals with the cited reading bolded. (Highlighting the exact sentence inside a note is a stretch goal.)
4. **Eval page (`/eval`).** Renders the latest A → D report table. Recruiters who click around will find the proof without opening GitHub.

Acknowledge bar at the bottom of each handoff: an "I've read this handoff" button that stores the demo nurse's name and the time.

**UX rules**
- 16 px minimum body text; designed for 1024 px tablets first
- No jargon the nurse wouldn't use; times in 24-hour format
- Keyboard `j` / `k` to move between residents (a small touch people notice)
- A permanent banner: "Synthetic data. Demo only. Not for clinical use."

**Stack:** React + TypeScript (Vite), React Router, TanStack Query for fetching, Tailwind for styling.

## Frontend design

The React app uses the same four layers. Components render, hooks connect, use cases decide, gateways fetch, and only `main.tsx` knows which gateways are real. Because the UI depends on gateway interfaces, you can build the whole frontend against fake gateways before the backend exists.

```
frontend/src/
├── domain/                    # pure TypeScript: no React, no fetch
│   ├── handoff.ts             # Handoff, Claim, Change, SourceId types
│   ├── priority.ts            # sortByPriority, topChange
│   └── flags.ts               # isFlagged, needsAttention
├── application/
│   ├── ports/                 # BoardGateway, HandoffGateway, SourceGateway, AckGateway
│   └── useCases/              # loadBoard, loadHandoff, openSource, acknowledgeHandoff
├── infrastructure/
│   ├── http/                  # apiClient, generated OpenAPI types, mappers, Http*Gateway
│   └── fakes/                 # Fake*Gateway + fixture data, for tests and offline dev
├── presentation/
│   ├── pages/                 # BoardPage, HandoffPage, EvalPage
│   ├── components/            # ResidentCard, SbarSection, ClaimLine, SourceChip, SourceDrawer
│   ├── sourceRenderers/       # NoteView, VitalsView, MedView, OrderView, IncidentView + registry.ts
│   ├── hooks/                 # useBoard, useHandoff, useSource, useAcknowledge
│   └── GatewayProvider.tsx    # React context that carries the gateways
└── main.tsx                   # composition root: picks Http or Fake gateways
```

**What each layer does**
- **Domain:** types and pure functions, tested with Vitest and no DOM.
- **Application:** gateway interfaces (ports) and use cases written as plain async functions that take a gateway, e.g. `loadBoard(gateway, shiftId)` returns a sorted, view-ready board.
- **Infrastructure:** HTTP gateways call the API and map the generated OpenAPI types into domain types at the boundary. An API rename breaks one mapper file, not twenty components.
- **Presentation:** hooks wrap use cases in TanStack Query (caching, loading and error states). Components are presentational: props in, JSX out, no fetching and no business rules.

```ts
// application/ports/HandoffGateway.ts
export interface HandoffGateway {
  getHandoff(residentId: string, shiftId: string): Promise<Handoff>;
  regenerate(residentId: string, shiftId: string): Promise<Handoff>;
}

// presentation/hooks/useHandoff.ts
export function useHandoff(residentId: string, shiftId: string) {
  const { handoffs } = useGateways(); // injected through context
  return useQuery({
    queryKey: ["handoff", residentId, shiftId],
    queryFn: () => loadHandoff(handoffs, residentId, shiftId),
  });
}

// main.tsx: the only file that imports infrastructure
const gateways = import.meta.env.VITE_USE_FAKES === "true"
  ? createFakeGateways()
  : createHttpGateways(import.meta.env.VITE_API_URL);
root.render(<GatewayProvider value={gateways}><App /></GatewayProvider>);
```

**Open/closed in the UI:** `SourceDrawer` looks up a renderer by record kind in `sourceRenderers/registry.ts`. A new record kind is a new component plus one registry line; the drawer is never edited.

**Tests:** Vitest for domain and use cases; React Testing Library for components, always rendered with fake gateways.

## API contract

Seven endpoints cover everything. Lock them down in the skeleton step so the frontend and backend can be built in parallel against the same shapes.

| Method | Path | Returns |
|---|---|---|
| GET | `/api/shifts?unit=2B` | Shifts available for the picker |
| GET | `/api/shifts/{shift_id}/board` | Resident cards: id, room, name, age, priority, top_change, acknowledged |
| GET | `/api/handoffs/{resident_id}?shift_id=…` | The cached handoff JSON (schema above) |
| POST | `/api/handoffs/{resident_id}/regenerate` | Body `{shift_id}`; reruns the pipeline and returns the new handoff (rate-limited in public mode) |
| GET | `/api/sources/{source_id}` | One record: `{id, kind, time, fields, text}` for the source drawer |
| POST | `/api/handoffs/{handoff_id}/ack` | Body `{nurse}`; returns `{acknowledged_by, acknowledged_at}` |
| GET | `/api/eval/latest` | The latest eval report JSON for `/eval` |

FastAPI generates OpenAPI docs at `/docs` automatically. Generate the frontend's TypeScript types from it (`openapi-typescript`) so the two sides can't drift apart.

## Repo layout and coding-agent workflow

Give the agent this plan, the CLAUDE.md below, and one build-plan step at a time. Write the ChangeRule classes and the verifiers yourself: those are the parts interviewers will ask you to explain line by line.

**Folder structure**

```
shift-handoff-copilot/
├── CLAUDE.md
├── README.md
├── Makefile
├── docs/PLAN.md                  # this doc, exported as Markdown
├── data/                         # gitignored; rebuilt by `make data`
├── backend/
│   ├── pyproject.toml            # includes the import-linter contracts
│   ├── src/handoff/
│   │   ├── domain/               # entities/, value_objects/, rules/, services/
│   │   ├── application/          # ports/, use_cases/, services/, dto.py, errors.py
│   │   ├── adapters/             # api/, persistence/sqlite/, llm/
│   │   └── infrastructure/       # config.py, db.py, container.py, main.py
│   ├── src/handoff_eval/         # RunEvaluation, GroundTruthReader, judge, reports
│   ├── sim/                      # fixtures, Synthea import, shift simulator
│   └── tests/                    # unit/domain, unit/application, integration, contract, api, fakes/
├── frontend/
│   ├── .dependency-cruiser.cjs   # frontend layer rules
│   └── src/                      # domain/, application/, infrastructure/, presentation/, main.tsx
└── .github/workflows/            # ci.yml (tests + layer checks), deploy.yml
```

**Layer contracts (in `backend/pyproject.toml`)**

```toml
[tool.importlinter]
root_packages = ["handoff", "handoff_eval"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Clean Architecture layers"
type = "layers"
layers = [
  "handoff.infrastructure",
  "handoff.adapters",
  "handoff.application",
  "handoff.domain",
]

[[tool.importlinter.contracts]]
name = "Inner layers stay framework-free"
type = "forbidden"
source_modules = ["handoff.domain", "handoff.application"]
forbidden_modules = ["fastapi", "pydantic", "openai", "httpx"]

[[tool.importlinter.contracts]]
name = "The app never imports eval"
type = "forbidden"
source_modules = ["handoff"]
forbidden_modules = ["handoff_eval"]
```

**CLAUDE.md (paste into the repo root):** see [/CLAUDE.md](../CLAUDE.md).

**How to run each milestone with the agent**
1. Paste one build-plan step, its "done when" line, and the Rule #1 section. Ask for a plan only: the layers it touches, files, classes and tests. No code yet.
2. Read the plan. Reject anything that puts logic in the wrong layer or constructs a concrete class outside the composition root.
3. Approve it, and have the agent write tests and code together, running `make test` and `make lint-arch` after each file.
4. Check the "done when" line yourself, and read three handoffs with your own eyes.
5. Commit, then ask the agent to explain any part you couldn't explain to an interviewer.

## Build plan

Get a working prototype first, built as a thin slice through every layer rather than a shortcut around them, then harden it one step at a time. The prototype cuts scope (fewer residents, fewer rules), never structure. Everything added later is a new class or adapter, not a rewrite.

**The prototype is done when:**
- 5 residents and 1 shift load from a hand-written fixture file (no Synthea yet)
- Two rules work end to end: `MissedDoseRule` and `IncidentRule`
- One real LLM provider writes handoffs behind `HandoffWriter` (Ollama locally, or Azure if you have access)
- Verification is deterministic only: `CitationVerifier` + `CoverageGuard`, no LLM judge yet
- The board, the handoff view with source chips, and the source drawer all work
- `make dev` runs it locally, and the import-linter and dependency-cruiser checks already pass

**Prototype build order: inside out, one agent session per step**
1. **Skeleton.** Repo, all four layer folders in both apps, Makefile, CI running pytest, Vitest, import-linter and dependency-cruiser.
   - Done when: CI is green on the empty skeleton, and a deliberately bad import (domain importing FastAPI) makes it fail.
2. **Backend domain.** Entities, value objects, `SourceId`, the two rules, `ChangeDetector`, `EvidencePackBuilder`, `CitationVerifier`, `CoverageGuard`.
   - Done when: every class has unit tests and the domain has zero non-standard-library imports.
3. **Backend application.** Ports, DTOs, `GenerateHandoff`, `GetUnitBoard`, `GetHandoff`, `GetSourceRecord`, `HandoffVerifier` (deterministic part), and in-memory fakes, including `FakeHandoffWriter`.
   - Done when: use-case tests pass with no database and no network.
4. **Backend persistence adapters.** SQLite schema, a fixture loader, and one SQLite class per read/store port.
   - Done when: integration tests pass against a temp database.
5. **Backend LLM adapters.** `PromptBuilder`, `DraftParser`, `LlmHandoffWriter`, and a `ChatClient` for your provider.
   - Done when: the same contract suite passes for the fake writer and the real one (on recorded responses).
6. **Backend API and composition root.** Routers, schemas, presenters, `container.py`, `main.py`.
   - Done when: `TestClient` tests pass, `/docs` shows the API contract, and you can curl a real handoff.
7. **Frontend domain and application.** Types, priority sorting, flag rules, gateway ports, use cases.
   - Done when: Vitest is green.
8. **Frontend presentation on fakes.** `GatewayProvider`, `BoardPage`, `HandoffPage`, `SourceDrawer` with the renderer registry, all running on fake gateways.
   - Done when: you can click through board → handoff → source with no backend running.
9. **Frontend HTTP gateways.** Generated API types, mappers, HTTP gateways; switch `main.tsx` from fakes to HTTP.
   - Done when: the same click-through works against the real backend. **Prototype done.**

Steps 7 and 8 depend only on the API contract, so they can run alongside steps 2–6 if you want two agent sessions going at once.

**After the prototype, in this order**
1. **Real data:** Synthea import, shift simulator and planted events. It's a new driver writing the same schema, so the app doesn't change.
2. **Remaining rules:** `NewOrderRule`, `VitalThresholdRule`, `PainIncreaseRule`, `WeightLossRule`. New classes plus one line each in the composition root.
3. **LLM judge:** the `ClaimJudge` port already exists; add `LlmClaimJudge` and wire it in.
4. **Acknowledge and regenerate:** the `AcknowledgeHandoff` use case, `AcknowledgementStore`, and the UI bar.
5. **Evaluation:** the `handoff_eval` package and the `/eval` page.
6. **Deploy to Azure:** a Dockerfile, the Azure chat client config, and GitHub Actions.
7. **README, demo video and resume bullet.**

## Deployment to Azure

Host everything on Azure, with GitHub Actions deploying on every push to main. That mirrors the Software Engineer posting, which describes regularly releasing work to an Azure-backed production environment.

| Part | Azure service | Notes |
|---|---|---|
| Frontend | Azure Static Web Apps (Free plan) | Built from `frontend/` by GitHub Actions |
| Backend | Azure Container Apps (consumption, scales to zero) | FastAPI Docker image with the seeded SQLite file baked in. Acknowledgements reset on redeploy, which is fine for a demo |
| Models | Azure AI Foundry deployments | A small, cheap model writes handoffs; a stronger one judges, and only during eval runs |
| Secrets | Container Apps secrets | Model keys never touch the repo |
| CI/CD | GitHub Actions | Tests on every PR; deploy on main, using OIDC login to Azure instead of stored passwords |

**Cost guardrails**
- Sign up with Azure for Students for free credit, and set a budget alert on day one
- Pre-generate every demo handoff at build time, so public visitors read the cache and never trigger a model call
- Rate-limit Regenerate in public mode (e.g. 5 per hour per IP), or disable it
- Cap max output tokens per call
- Do local development on Ollama, which costs $0

## Demo, README and interview story

Lead every version of the story with the verifier and the numbers. That's what separates this from "a ChatGPT wrapper".

**90-second demo video**
1. 0–10 s, the problem: "At shift change, a nurse has minutes to brief the next shift on every resident."
2. 10–40 s: the board, open the top-priority resident, read what changed, tap a source chip to show the original record.
3. 40–60 s: an amber flagged claim, then the `/eval` page with the A → D table.
4. 60–80 s, the architecture in one sentence: rules find the changes, the LLM words them, a verifier checks every claim.
5. 80–90 s: "Synthetic data, deployed on Azure," plus the link.

**README order:** a one-line pitch, a GIF, the live link, the problem in three sentences, the architecture diagram, the eval results table, the safety design (rules, recommendation limits, acknowledgement), how to run it locally, and what you'd build next.

**Four interview talking points**
- "I deliberately didn't make nurses enter data twice. The app reads what's already in the chart."
- "Safety-critical judgement lives in deterministic rules with unit tests. The LLM only turns it into readable sentences."
- "I measured hallucination. The verifier took unsupported claims from X% to Y%, and I checked the LLM judge against my own labels."
- "It follows Clean Architecture, enforced in CI. Moving from Ollama to Azure was one new adapter and one line in the composition root; no use case changed."

**Resume bullet template (fill in your real numbers)**

> Built Shift Handoff Copilot, an AI shift-change tool for long-term care (React, FastAPI, Azure AI Foundry) that turns a resident's notes, vitals and eMAR into a cited SBAR handoff; a claim verifier cut unsupported claims from X% to Y% across N handoffs.

If you've already applied, send the campus recruiter a two-line email with the live link and video once it's deployed.

## Risks and decisions

Settle three decisions before the skeleton step. The biggest risk isn't technical: it's a demo that looks like "just a summarizer".

**Decide before starting** (answered in [DECISIONS.md](DECISIONS.md))
- [x] Model provider: Ollama for local dev and the prototype, Azure AI Foundry for the deployed app (matches the postings). Recommended.
- [x] Backend language: Python, your fastest language. Recommended over C#.
- [x] Shift pattern: three 8-hour shifts (default) or two 12-hour shifts. → *3×8 default, switchable in the app.*

**Risks**

| Risk | Mitigation |
|---|---|
| The architecture erodes under pressure | import-linter and dependency-cruiser fail CI; every agent plan must name its layer |
| Over-engineering slows the prototype | Cut scope, never layers: 5 residents and 2 rules, but all four layers from day one |
| Reads as "just a summarizer" | Open the demo with source chips, the verifier and the eval table |
| Clinical overreach | Recommendation whitelist, demo-only banner, nurse acknowledgement |
| The LLM grades itself | A different, stronger judge model, checked against 50 hand labels |
| Synthetic notes too clean to be convincing | The simulator adds charting shorthand, typos and irrelevant chatter |
| Cost surprise | Cached handoffs, a token cap, a budget alert |
| Agent-written code you can't explain | You write the ChangeRule classes and the verifiers, and review every diff |
| Scope creep | No stretch feature until the app is deployed |
