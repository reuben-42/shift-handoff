"""Rule #1 guard: prove import-linter actually fails on a layer violation.

Each test copies src/ to a temp dir, plants one bad import, and runs
lint-imports against the copy. The real tree must pass; every planted
violation must fail.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]


def _lint_imports(src_dir: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(src_dir)}
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from importlinter.cli import lint_imports_command; "
            "sys.exit(lint_imports_command())",
            "--config",
            str(BACKEND / "pyproject.toml"),
            "--no-cache",
        ],
        cwd=src_dir,
        env=env,
        capture_output=True,
        text=True,
    )


def test_real_tree_passes() -> None:
    result = _lint_imports(BACKEND / "src")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("module_path", "bad_import", "broken_contract"),
    [
        ("handoff/domain/_bad.py", "import fastapi", "Inner layers stay framework-free"),
        ("handoff/application/_bad.py", "import pydantic", "Inner layers stay framework-free"),
        (
            "handoff/domain/_bad.py",
            "from handoff.infrastructure import config",
            "Clean Architecture layers",
        ),
        (
            "handoff/application/_bad.py",
            "from handoff.adapters import api",
            "Clean Architecture layers",
        ),
        ("handoff/adapters/_bad.py", "import handoff_eval", "The app never imports eval"),
    ],
)
def test_planted_violation_fails(
    tmp_path: Path, module_path: str, bad_import: str, broken_contract: str
) -> None:
    src_copy = tmp_path / "src"
    shutil.copytree(BACKEND / "src", src_copy)
    (src_copy / module_path).write_text(bad_import + "\n")

    result = _lint_imports(src_copy)

    assert result.returncode != 0, "import-linter should have failed"
    assert broken_contract in result.stdout
    assert "BROKEN" in result.stdout
