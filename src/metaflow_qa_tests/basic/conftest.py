import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = Path(str(item.fspath))
        if "basic" in path.parts:
            item.add_marker(pytest.mark.local)