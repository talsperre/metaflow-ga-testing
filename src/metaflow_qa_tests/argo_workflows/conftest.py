import pytest
from pathlib import Path

def pytest_collection_modifyitems(config, items):
    curr_dir = Path(__file__).parent
    for item in items:
        if curr_dir in item.path.parents and not item.get_closest_marker("argo_workflows"):
            item.add_marker(pytest.mark.argo_workflows)