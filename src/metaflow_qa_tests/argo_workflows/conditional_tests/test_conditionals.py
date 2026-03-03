import pytest
from metaflow import Deployer
from ..utils import (
    wait_for_run_to_finish,
    wait_for_run,
)
import io
import os


ROOT = os.path.dirname(__file__)


@pytest.fixture
def test_tags(test_id):
    return ["argo_workflows_tests", "conditional_step_tests", test_id]


@pytest.mark.argo_workflows
@pytest.mark.parametrize(
    "filename",
    [
        "conditionalFlow.py",
        "nestedConditional1.py",
        "nestedConditional2.py",
        "nestedConditional4.py",
        "nestedConditional5.py",
        "nestedConditional6.py",
        "nestedConditional7.py",
        "nestedConditional9.py",
        "recursiveConditional1.py",
        "nestedRecursiveConditional1.py",
        "conditionalSkipFlow1.py",
        "conditionalSkipFlow2.py",
        "conditionalSkipFlow3.py",
        "conditionalSkipFlow4.py",
        "conditionalSkipFlow5.py",
    ],
)
def test_conditional_flows(filename, test_tags, test_id):
    deployed_flow = None
    try:
        deployed_flow = (
            Deployer(flow_file=os.path.join(ROOT, filename))
            .argo_workflows()
            .create(tags=test_tags)
        )

        deployed_flow.trigger()

        run = wait_for_run(deployed_flow.flow_name, ns=test_id)

        finished_run = wait_for_run_to_finish(run, timeout=120)

        assert finished_run.successful

    finally:
        if deployed_flow is not None:
            # Clean up deployed flows.
            deployed_flow.delete()


@pytest.mark.argo_workflows
@pytest.mark.parametrize(
    "filename",
    [
        "nestedConditional3.py",
        "nestedConditional8.py",
        "failingConditionalFlow.py",
        "recursiveConditional2.py",
        "nestedRecursiveConditional2.py",
        "nestedRecursiveConditional3.py",
    ],
)
def test_failing_conditional_flows(filename, test_tags, test_id):
    deployed_flow = None
    try:
        deploy_failed = False
        deployed_flow = (
            Deployer(flow_file=os.path.join(ROOT, filename))
            .argo_workflows()
            .create(tags=test_tags)
        )
    except Exception:
        deploy_failed = True
    finally:
        if deployed_flow is not None:
            # Clean up deployed flows.
            deployed_flow.delete()

    assert deploy_failed, "The deployment was expected to fail"
