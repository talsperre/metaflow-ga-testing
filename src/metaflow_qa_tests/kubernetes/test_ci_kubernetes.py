"""
These tests use a minimal flow (ci_helloflow.py) that doesn't request
@resources(cpu=2) or use foreach splits, so it can run on GitHub Actions
runners where Minikube only has 2 CPUs.
"""

import pytest
from metaflow.runner.metaflow_runner import Runner
import os

FLOWS_ROOT = os.path.join(os.path.dirname(__file__), "..", "flows")


@pytest.fixture
def test_tags(test_id):
    return ["ci_kubernetes_tests", test_id]


@pytest.mark.kubernetes
def test_ci_kubernetes_helloflow(test_tags):
    """Verify a minimal flow completes on K8s — no heavy resource requests."""
    result = Runner(
        flow_file=os.path.join(FLOWS_ROOT, "ci_helloflow.py"),
        decospecs=["kubernetes"],
    ).run(tags=test_tags)

    assert result.run.finished
