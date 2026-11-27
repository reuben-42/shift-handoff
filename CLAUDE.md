# Shift Handoff Copilot

Turns one nursing-home shift of synthetic chart data into a cited SBAR handoff per resident.
Full plan: docs/PLAN.md. Read its "Rule #1" section before writing any code.
Build order and the current step: docs/BUILD_STEPS.md. Settled decisions: docs/DECISIONS.md.

## Rule #1: Clean Architecture + SOLID (non-negotiable)
- Layers, inside out: domain -> application -> adapters -> infrastructure. Dependencies point inward only.
- domain/ imports only the Python standard library. Frozen dataclasses, no Pydantic.
- application/ imports only domain/. Every port (typing.Protocol) lives in application/ports/.
- Concrete classes are constructed only in infrastructure/container.py (backend) and src/main.tsx (frontend).
- No business logic in routers, React components, SQL or prompts.
- One class per ChangeRule. Add rules or LLM providers by adding classes, never by editing ChangeDetector or LlmHandoffWriter.
- Frontend: components never fetch, presentation/ never imports infrastructure/, and domain/ has no React.
- If a task seems to need breaking a rule, stop and ask. Never work around it.

## Safety rules
- Synthetic data only. Never add real patient data or records copied from the web.
- Every claim carries sources (record IDs). No claim without a source reaches the UI.
- The model never suggests new medications, doses or diagnoses. Recommendations: monitor, reassess, notify, follow existing orders.
- Never read ground_truth outside handoff_eval/.
- Secrets come from environment variables. Never commit .env.

## Commands
- make dev        # backend :8000 + frontend :5173
- make test       # pytest + vitest
- make lint-arch  # import-linter + dependency-cruiser
- make data       # rebuild SQLite (fixtures now, Synthea + simulator later)
- make eval VARIANT=D SET=dev

## Git workflow
- One branch per build step: `step-NN-<slug>`, branched from the previous step's branch (stacked).
- Never push to main. Reuben reviews each step branch and merges into main himself, in order.
- Small commits, one concern each.

## Working style
- Each step's plan (layers it touches, files, classes and tests) is in docs/BUILD_STEPS.md; keep it current.
- Every change answers one question: which layer does this live in, and why?
- Tests come with the code: domain = pure unit tests, application = in-memory fakes, adapters = integration and contract tests.
- Run make test and make lint-arch before saying you're done.
- After any change to rules, prompts or verification, run make eval SET=dev and show the metric diff.
- Shift pattern is configurable (default three 8-hour shifts); never hard-code shift times outside the ShiftPattern presets.
