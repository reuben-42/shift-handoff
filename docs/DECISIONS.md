# Decisions

The plan's "Decide before starting" checklist (docs/PLAN.md, *Risks and decisions*), answered on 2026-11-27, plus the design choices that follow from those answers.

| Decision | Answer |
|---|---|
| Backend language | **Python 3.12+ / FastAPI** |
| Model provider | **Local, open-source model through Ollama** for the prototype and local dev. Azure AI Foundry stays a later adapter (step 18) behind the same `ChatClient` interface. CI always runs `LLM_PROVIDER=fake`. |
| Shift pattern | **Three 8-hour shifts by default** (Day 07:00–15:00, Evening 15:00–23:00, Night 23:00–07:00), **changeable inside the running prototype** (e.g. two 12-hour shifts). |

---

## 1. Configurable shift pattern

The plan assumes 3×8 everywhere. Making the pattern changeable at runtime means it becomes a domain concept instead of a constant. This is the one structural change from the PDF, and it is kept small.

### Domain (`domain/value_objects/shift_pattern.py`)
- `ShiftDefinition(kind: ShiftKind, start: time, hours: int)`, frozen.
- `ShiftPattern(name: str, shifts: tuple[ShiftDefinition, ...])`, frozen. It validates that the shifts are contiguous, don't overlap and add up to exactly 24 hours.
- Presets: `THREE_EIGHT` (`3x8`): day 07–15, evening 15–23, night 23–07. `TWO_TWELVE` (`2x12`): day 07–19, night 19–07.
- `ShiftCalendar.window_for(pattern, date, kind) -> ShiftWindow` and `ShiftCalendar.shifts_between(pattern, start_date, end_date)`. Night shifts cross midnight and belong to the date they *start* on.
- `ShiftKind` stays `day | evening | night`; 2×12 just doesn't use `evening`.

### Data
- Every record is timestamped, so **slicing by shift works under any pattern**. The PDF's `shifts` table is replaced by shifts *computed* from the active pattern and the date range of the data. (The simulator in step 11 still writes on a 24-hour clock.)
- `ground_truth` stores the event **time** (plus its evidence IDs). The eval maps each event to a shift under whatever pattern is being evaluated.
- `handoffs` gets a `pattern` column. The cache key is `(resident_id, shift_id, pattern)`, so switching patterns never serves a 3×8 handoff for a 12-hour shift. Custom patterns are named after their start times (e.g. `custom-3x@0600-1400-2200`), so the name alone is a safe cache key.
- A `settings` table holds the active pattern. The default comes from the env var `SHIFT_PATTERN=3x8`.

### Application / API / UI
- Ports: `SettingsStore` (get/set active pattern). Use cases: `GetShiftPattern`, `SetShiftPattern`, plus `ListShifts` (behind the existing `GET /api/shifts`).
- **Two endpoints beyond the plan's seven:** `GET /api/settings/shift-pattern` and `PUT /api/settings/shift-pattern` (body: a preset name, or custom definitions).
- UI: a small "Shift pattern" control in the board header (3×8 / 2×12 toggle, optional custom start time). Changing it refetches the shift picker and the board.

---

## 2. Local open-source model recommendations

What the job needs: the **writer** turns a ~2–4k-token evidence pack into strict JSON that matches a schema, cites record IDs and never makes anything up. That calls for good instruction-following and structured output, not medical knowledge, because the rules have already done the clinical judgement. The **judge** (step 13) must be *stronger than the writer and from a different model family* (PLAN.md: "the writer isn't grading itself"). The **simulator** (step 11) writes messy nursing notes and only runs offline.

All of these run through Ollama, which supports JSON-schema structured output (`format: <schema>`), so `DraftParser` gets valid JSON most of the time and only has to reject the rest.

| Role | Recommended | Licence | Approx. memory (Q4) | Why |
|---|---|---|---|---|
| **Writer (default)** | **`qwen3:8b`** | Apache-2.0 | ~6 GB | Best JSON/schema adherence at this size, long context, fast on a laptop. Run with thinking off (`think: false`) for latency. |
| Writer (low-spec laptop, ≤8 GB RAM) | `qwen3:4b` | Apache-2.0 | ~3 GB | Same family and prompt, so it's a one-line swap. Expect more `DraftParser` rejections. |
| Writer (stronger machine, ≥24 GB) | `qwen3:14b` | Apache-2.0 | ~10 GB | Better wording, still quick. |
| **Judge (step 13)** | **`gpt-oss:20b`** | Apache-2.0 | ~14 GB | Different family from Qwen, stronger reasoning, built for structured output. Runs only during eval, so its speed doesn't matter. |
| Judge alternative | `mistral-small3.2:24b` | Apache-2.0 | ~15 GB | Also a different family; good if gpt-oss is slow on your hardware. |
| Simulator notes (step 11) | `mistral-small3.2:24b`, or `qwen3:8b` at high temperature | Apache-2.0 | — | Offline only. A different family from the writer keeps the notes' phrasing from echoing the writer's style. |

**Recommendation:** start with `qwen3:8b` as the writer. Add `gpt-oss:20b` as the judge when step 13 arrives. For the deployed demo, move to Azure (step 18) or keep Ollama in the container if Azure isn't available.

Notes:
- Skip domain-tuned medical models (e.g. MedGemma). The LLM only words facts the rules already found, so medical tuning buys little, and their licences aren't OSI open source.
- Llama 3.x and Gemma 3 are fine models, but they ship under custom licences, not OSI open source. They're listed here only as fallbacks.
- Pin exact tags in `.env` (`OLLAMA_WRITER_MODEL=qwen3:8b`). If a newer Qwen generation is out when you start, the same reasoning applies: swap the tag, re-run `make eval SET=dev`, and compare.
- Settings (step 6): `temperature=0.2`, `num_ctx=8192`, cap output tokens (~800). These double as the plan's cost guardrail.
