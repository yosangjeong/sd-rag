"""The ECS tasks start these modules with `python -m <module>` (infra/stacks/app.py).

Without the `__main__` guard such a module only imports and exits 0 with no output:
the worker lost its guard in a refactor (11/16) and every worker task stopped at once,
which the unit tests could not see (they call the functions directly). Found in the
11/26 rehearsal deploy.
"""

import ast
import importlib.util
from pathlib import Path

import pytest

ECS_MODULES = ["sdrag.worker.main", "sdrag.ingest.from_s3"]


@pytest.mark.parametrize("module", ECS_MODULES)
def test_module_runs_main_when_started_with_python_m(module):
    path = importlib.util.find_spec(module).origin
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and ast.unparse(node.test) in ('__name__ == "__main__"', "__name__ == '__main__'")
    ]
    assert guards, f"{module} has no `if __name__ == '__main__':` block"
    calls = [
        n.func.id
        for g in guards
        for n in ast.walk(g)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    assert "main" in calls, f"{module}'s __main__ block does not call main()"
