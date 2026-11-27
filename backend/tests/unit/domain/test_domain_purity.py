"""Done-when for step 02: the domain has zero non-standard-library imports."""

import ast
import sys
from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[3] / "src" / "handoff" / "domain"


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
    return names


def test_domain_imports_only_stdlib_and_itself() -> None:
    offenders = [
        f"{path.relative_to(DOMAIN)}: {module}"
        for path in DOMAIN.rglob("*.py")
        for module in _imported_modules(path)
        if not module.startswith("handoff.domain")
        and module.split(".")[0] not in sys.stdlib_module_names
    ]
    assert offenders == []
