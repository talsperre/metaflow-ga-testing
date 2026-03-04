"""
Uses a minimal flow (ci_helloflow.py) that can run on resource-constrained
GitHub Actions runners (2 CPU Minikube).
"""

import pytest
from metaflow import Deployer
from .utils import wait_for_run, wait_for_run_to_finish
import os

FLOWS_ROOT = os.path.join(os.path.dirname(__file__), "..", "flows")


@pytest.fixture
def test_tags(test_id):
    return ["ci_argo_tests", test_id]


@pytest.mark.argo_workflows
def test_ci_argo_helloflow(test_tags, test_id):
    """Deploy and trigger a minimal flow on Argo — no heavy resource requests."""
    deployer = Deployer(
        flow_file=os.path.join(FLOWS_ROOT, "ci_helloflow.py")
    ).argo_workflows()
    deployed_flow = deployer.create(tags=test_tags)

    try:
        deployed_flow.trigger()
        run = wait_for_run(deployed_flow.flow_name, ns=test_id)
        run = wait_for_run_to_finish(run)
        assert run.successful
    finally:
        deployed_flow.delete()
