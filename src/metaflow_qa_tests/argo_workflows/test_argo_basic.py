import pytest
from metaflow import Deployer
from .utils import wait_for_run, wait_for_run_to_finish
import os

FLOWS_ROOT = os.path.join(os.path.dirname(__file__), "..", "flows")


@pytest.fixture
def test_tags(test_id):
    return ["argo_workflows_tests", test_id]


@pytest.mark.argo_workflows
def test_argo_helloflow(test_tags, test_id):
    deployer = Deployer(
        flow_file=os.path.join(FLOWS_ROOT, "helloflow.py")
    ).argo_workflows()
    deployed_flow = deployer.create(tags=test_tags)

    try:
        deployed_flow.trigger()
        run = wait_for_run(deployed_flow.flow_name, ns=test_id)
        run = wait_for_run_to_finish(run)
        assert run.successful
    finally:
        # clean up.
        deployed_flow.delete()


@pytest.mark.argo_workflows
def test_argo_conda_flow(test_tags, test_id):
    deployer = Deployer(
        flow_file=os.path.join(FLOWS_ROOT, "condatest.py"), environment="conda"
    ).argo_workflows()
    deployed_flow = deployer.create(tags=test_tags)

    try:
        deployed_flow.trigger()
        run = wait_for_run(deployed_flow.flow_name, ns=test_id)
        run = wait_for_run_to_finish(run)
        assert run.successful
    finally:
        # clean up.
        deployed_flow.delete()


@pytest.mark.argo_workflows
def test_argo_pypi_flow(test_tags, test_id):
    deployer = Deployer(
        flow_file=os.path.join(FLOWS_ROOT, "pypitest.py"), environment="pypi"
    ).argo_workflows()
    deployed_flow = deployer.create(tags=test_tags)

    try:
        deployed_flow.trigger()
        run = wait_for_run(deployed_flow.flow_name, ns=test_id)
        run = wait_for_run_to_finish(run)
        assert run.successful
    finally:
        # clean up.
        deployed_flow.delete()


@pytest.mark.argo_workflows
def test_argo_notifications(test_tags):
    deployer = Deployer(
        flow_file=os.path.join(FLOWS_ROOT, "helloflow.py")
    ).argo_workflows(name="argo-notifications-flow")

    deployed_flow = None
    try:
        did_not_raise = False
        deployed_flow = deployer.create(
            notify_on_error=True, notify_on_success=True, tags=test_tags
        )
        did_not_raise = True
    except:
        if did_not_raise:
            raise Exception("did not fail with missing config. this is unexpected")

    try:
        did_not_raise = False
        # slack and pagerduty test
        deployed_flow = deployer.create(
            notify_on_success=True,
            notify_on_error=True,
            notify_incident_io_api_key="123",
        )
        did_not_raise = True
    except:
        if did_not_raise:
            raise Exception("was supposed to fail with incident.io misconfiguration.")

    try:
        # test successful config
        # Slack/pagerduty config
        deployed_flow = deployer.create(
            notify_on_success=True,
            notify_on_error=True,
            notify_slack_webhook_url="http://test.example",
            notify_pager_duty_integration_key="123",
        )
        # incident.io config. separated in order to cover a regression
        deployed_flow = deployer.create(
            notify_on_success=True,
            notify_on_error=True,
            notify_incident_io_api_key="123",
            incident_io_alert_source_config_id="1",
            tags=test_tags,
        )

    finally:
        if deployed_flow:
            deployed_flow.delete()
