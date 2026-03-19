"""
Reference implementation: full deploy → trigger → wait → assert → cleanup.

This file is intentionally over-commented. It serves two purposes:
  1. A working test that verifies the event-trigger lifecycle end to end
  2. A guide for anyone adding support for a new orchestrator backend

The only backend-specific line in the test body is the Deployer call.
Everything else — the flow, the wait utilities, the assertions — is
backend-agnostic.

To port to a different orchestrator, change only get_deployer():
    Argo Workflows:      Deployer(...).argo_workflows()
    Step Functions:      Deployer(...).step_functions()
    (future) Maestro:    Deployer(...).maestro()

Answers to the three open design questions from issue #6:

Q: Should the backend be parameterized via fixture, CLI option, or env var?
A: Environment variable read inside a fixture. This keeps the test body
   clean (no backend logic), works with tox without extra config, and
   lets CI override the backend without changing any test code.

Q: How do you structure the test so adding Maestro only changes the Deployer call?
A: The get_deployer fixture encapsulates the backend choice entirely.
   The test calls get_deployer(flow_file) and gets back a deployer object.
   It never calls .argo_workflows() directly. Adding Maestro = one elif
   clause in the fixture, zero changes to any test.

Q: Should the trigger flow be a new file or reuse an existing one?
A: New file (trigger_flow.py). The existing flows in deploy_time_triggers/
   only verify deployment — they do not trigger, wait, and assert a
   completed run. A dedicated minimal flow makes the test self-contained
   and easy to understand in isolation.
"""
import os
import pytest
from metaflow import Deployer
from .utils import wait_for_run, wait_for_run_to_finish

FLOWS_ROOT = os.path.join(os.path.dirname(__file__), "..", "flows")

EVENT_NAME = "test_event"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_tags(test_id):
    return ["argo_workflows_tests", "trigger_tests", test_id]


@pytest.fixture
def get_deployer():
    """
    Returns a factory function that creates the right Deployer backend.

    Reads METAFLOW_TEST_BACKEND env var (default: argo_workflows).
    This is the only place the backend name appears — changing backends
    requires zero changes to test logic.

    Supported values:
        argo_workflows  →  .argo_workflows()
        step_functions  →  .step_functions()
    """
    backend = os.environ.get("METAFLOW_TEST_BACKEND", "argo_workflows")

    def _make(flow_file):
        d = Deployer(flow_file=flow_file)
        if backend == "argo_workflows":
            return d.argo_workflows()
        elif backend == "step_functions":
            return d.step_functions()
        else:
            raise ValueError(
                f"Unknown METAFLOW_TEST_BACKEND='{backend}'. "
                "Supported: 'argo_workflows', 'step_functions'."
            )

    return _make


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.argo_workflows
def test_simple_event_trigger(test_tags, test_id, get_deployer):
    """
    Full lifecycle test: deploy a flow, fire an event, verify the run succeeds.

    Lifecycle phases:
        1. DEPLOY  — register TriggerFlow with the orchestrator
        2. TRIGGER — fire a trigger with a parameter value
        3. WAIT    — poll until the triggered run appears and finishes
        4. ASSERT  — verify run succeeded and parameter arrived correctly
        5. CLEANUP — delete the deployment (always runs, even on failure)
    """
    # Phase 1 — DEPLOY
    # Compiles TriggerFlow and registers it with the orchestrator.
    # After this step the flow is live and listening for "test_event".
    deployed_flow = get_deployer(
        os.path.join(FLOWS_ROOT, "trigger_flow.py")
    ).create(tags=test_tags)

    try:
        # Phase 2 — TRIGGER
        # Fires a trigger with param_a and returns a TriggeredRun object.
        # The event name is registered on the flow via @trigger(event=EVENT_NAME).
        # Passing param_a here lets us assert the value arrived correctly.
        deployed_flow.trigger(param_a="hello from trigger")

        # Phase 3 — WAIT for a new run to appear
        # Polls Flow(flow_name).latest_run until a run newer than now
        # appears in the test_id namespace. Timeout: 120s.
        run = wait_for_run(deployed_flow.flow_name, ns=test_id, timeout=120)

        # Phase 4 — WAIT for the run to finish
        # Polls run.finished_at until complete. Re-raises any exception
        # stored in run.data.test_failure by @catch in TriggerFlow.start.
        run = wait_for_run_to_finish(run, timeout=240)

        # Phase 5 — ASSERT
        # run.successful is True only when all steps exit with code 0.
        assert run.successful, (
            f"TriggerFlow run did not succeed. "
            "Check the run logs for details."
        )
        # Verify the parameter value was passed through trigger() correctly.
        assert run.data.param_a == "hello from trigger", (
            f"Expected param_a='hello from trigger', "
            f"got '{run.data.param_a}'"
        )

    finally:
        # Phase 5 — CLEANUP
        # Deletes the deployed workflow template from the orchestrator.
        # Runs even if any phase above raises — prevents orphaned
        # deployments accumulating across test runs.
        deployed_flow.delete()