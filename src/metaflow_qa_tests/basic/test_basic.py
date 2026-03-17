import pytest
from metaflow.runner.metaflow_runner import Runner
import os

FLOWS_ROOT = os.path.join(os.path.dirname(__file__), "..", "flows")


@pytest.fixture
def test_tags(test_id):
    return ["basic_tests", test_id]


@pytest.mark.local
def test_helloflow(test_tags):
    result = Runner(flow_file=os.path.join(FLOWS_ROOT, "helloflow.py")).run(
        tags=test_tags
    )

    assert result.run.finished


@pytest.mark.local
def test_conda_flow(test_tags):
    result = Runner(
        flow_file=os.path.join(FLOWS_ROOT, "condatest.py"), environment="conda"
    ).run(tags=test_tags)

    assert result.run.finished


@pytest.mark.local
def test_pypi_flow(test_tags):
    # Should default to fast-env
    result = Runner(
        flow_file=os.path.join(FLOWS_ROOT, "pypitest.py"), environment="pypi"
    ).run(tags=test_tags)

    assert result.run.finished
