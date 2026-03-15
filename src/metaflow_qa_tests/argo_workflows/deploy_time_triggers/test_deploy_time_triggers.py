import pytest
from metaflow import Deployer
from contextlib import redirect_stdout
import io
import os

ROOT = os.path.dirname(__file__)

# TODO: Test the actual triggered behaviour as well. Omitted for now, as the deployment should be enough of a verification for this functionality.


@pytest.fixture
def test_tags(test_id):
    return ["argo_workflows_tests", "deploy_time_triggers_tests", test_id]


@pytest.mark.argo_workflows
def test_successful_trigger_deployments(test_tags):
    # "filename, expected_trigger",
    filename_and_trigger = [
        ("ParamTest1.py", "deploytime_trigger_event"),
        ("ParamTest2.py", "deploytime_trigger_event"),
        ("ParamTest3.py", "deploytime_trigger_event"),
        ("ParamTest4.py", "deploytime_trigger_event"),
        ("ParamTest5.py", "deploytime_trigger_event"),
        ("ParamTest6.py", "deploytime_trigger_event"),
        ("ParamTest7.py", "deploytime_trigger_event"),
    ]
    deployers = []
    try:
        for filename, expected_trigger in filename_and_trigger:
            buff = io.StringIO()
            with redirect_stdout(buff):
                deployer = (
                    Deployer(flow_file=os.path.join(ROOT, filename))
                    .argo_workflows()
                    .create(tags=test_tags)
                )
                deployers.append(deployer)

            output = buff.getvalue()
            assert (
                f"This workflow triggers automatically when the upstream {expected_trigger} event is/are published."
                in output
            ), f"Trigger should be {expected_trigger}"
    finally:
        # Clean up deployed flows.
        for deployer in deployers:
            deployer.delete()


@pytest.mark.argo_workflows
def test_successful_trigger_on_finish_deployments(test_tags):
    # "filename, expected_trigger"
    filename_and_trigger = [
        ("ParamTestTriggerOnFinish1.py", "DeployTimeTriggerParams"),
        ("ParamTestTriggerOnFinish2.py", "DeployTimeTriggerParams"),
        ("ParamTestTriggerOnFinish3.py", "DeployTimeTriggerParams"),
        ("ParamTestTriggerOnFinish4.py", "DeployTimeTriggerParams"),
        (
            "ParamTestTriggerOnFinish5.py",
            "deploytime_project_two.user.saikonen.DeployTimeTriggerParams",
        ),
        (
            "ParamTestTriggerOnFinish6.py",
            "deploytime_project.test.custombranch.DeployTimeTriggerParams",
        ),
        # ("ParamTestTriggerOnFinish7.py", "another_project.test.custombranch.DeployTimeTriggerParams"),
    ]
    deployers = []
    try:
        for filename, expected_trigger in filename_and_trigger:
            buff = io.StringIO()
            with redirect_stdout(buff):
                deployer = (
                    Deployer(flow_file=os.path.join(ROOT, filename))
                    .argo_workflows()
                    .create(tags=test_tags)
                )
                deployers.append(deployer)

            output = buff.getvalue()
            assert (
                f"This workflow triggers automatically when the upstream {expected_trigger} flow succeed(s)"
                in output
            ), f"Trigger should be {expected_trigger}"
    finally:
        # Clean up deployed flows
        for deployer in deployers:
            deployer.delete()


@pytest.mark.argo_workflows
def test_expected_failing_trigger_deployments(test_tags):
    # "filename",
    filenames = [
        "ParamTestTriggerOnFinishFail1.py",
        "ParamTestTriggerOnFinishFail1.py",
        "ParamTestFail1.py",
        "ParamTestFail2.py",
    ]
    for filename in filenames:
        try:
            deployer = (
                Deployer(flow_file=os.path.join(ROOT, filename))
                .argo_workflows()
                .create(tags=test_tags)
            )
            failed = False
            # Clean up deployed flow that should not have gone through.
            deployer.delete()
        except Exception:
            failed = True  # expected to receive an exception!

        if not failed:
            raise Exception("deployment should have failed.")
