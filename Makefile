# Shift Handoff Copilot. See CLAUDE.md for what each command is for.
.PHONY: help install dev dev-backend dev-frontend test test-backend test-frontend \
        lint lint-arch arch-guard data eval

BACKEND := backend
FRONTEND := frontend
VARIANT ?= D
SET ?= dev

help:
	@grep -E '^[a-z-]+:' Makefile | cut -d: -f1 | sort | tr '\n' ' '; echo

install:
	cd $(BACKEND) && uv sync
	cd $(FRONTEND) && npm ci

dev:  ## backend :8000 + frontend :5173
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd $(BACKEND) && uv run uvicorn handoff.infrastructure.main:create_app --factory --reload --port 8000

dev-frontend:
	cd $(FRONTEND) && npm run dev

test: test-backend test-frontend  ## pytest + vitest

test-backend:
	cd $(BACKEND) && uv run pytest

test-frontend:
	cd $(FRONTEND) && npm test

lint:
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check .
	cd $(FRONTEND) && npm run typecheck

lint-arch:  ## import-linter + dependency-cruiser
	cd $(BACKEND) && uv run lint-imports --no-cache
	cd $(FRONTEND) && npm run lint:arch

arch-guard:  ## prove the layer checks fail on planted violations
	cd $(BACKEND) && uv run pytest tests/arch
	cd $(FRONTEND) && npm run arch-guard

data:  ## rebuild SQLite (fixtures in step 05, Synthea + simulator in step 11)
	@echo "make data: not implemented yet (step 05)"; exit 1

eval:  ## make eval VARIANT=D SET=dev
	@echo "make eval: not implemented yet (step 15)"; exit 1
