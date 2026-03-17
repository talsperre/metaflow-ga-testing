import pytest
from metaflow.runner.metaflow_runner import Runner
import os

FLOWS_ROOT = os.path.join(os.path.dirname(__file__), "..", "flows")


@pytest.fixture
def test_tags(test_id):
    return ["kubernetes_tests", test_id]


@pytest.mark.kubernetes
def test_kubernetes_helloflow(test_tags):
    result = Runner(
        flow_file=os.path.join(FLOWS_ROOT, "helloflow.py"), decospecs=["kubernetes"]
    ).run(tags=test_tags)

    assert result.run.finished


@pytest.mark.kubernetes
def test_kubernetes_conda_flow(test_tags):
    result = Runner(
        flow_file=os.path.join(FLOWS_ROOT, "condatest.py"),
        environment="conda",
        decospecs=["kubernetes"],
    ).run(tags=test_tags)

    assert result.run.finished


@pytest.mark.kubernetes
def test_kubernetes_pypi_flow(test_tags):
    result = Runner(
        flow_file=os.path.join(FLOWS_ROOT, "pypitest.py"),
        environment="pypi",
        decospecs=["kubernetes"],
    ).run(tags=test_tags)

    assert result.run.finished
