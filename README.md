# Shift Handoff Copilot

Turns one shift of a (synthetic) nursing-home resident's chart into a 30-second, cited SBAR handoff for the next nurse. Rules find the changes, a local LLM words them, and a verifier checks every claim against its source record.

> **Synthetic data. Demo only. Not for clinical use.**

🚧 Under construction. Build order: [docs/BUILD_STEPS.md](docs/BUILD_STEPS.md). Full plan: [docs/PLAN.md](docs/PLAN.md).

## Run locally

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and Node 22+.

```bash
make install
make dev          # backend http://localhost:8000/docs, frontend http://localhost:5173
make test         # pytest + vitest
make lint-arch    # Clean Architecture layer checks (import-linter + dependency-cruiser)
```
