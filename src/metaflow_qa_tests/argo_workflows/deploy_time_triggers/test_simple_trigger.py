"""
test_simple_trigger.py, Minimal, self-contained Deployer trigger lifecycle test.

This single test demonstrates the full deploy -> trigger -> wait -> assert -> cleanup
lifecycle using the Metaflow Deployer API.  It is intentionally simple and
heavily commented so that someone adapting it to a different orchestrator
(Maestro, Step Functions) can follow the pattern.


 BACKEND SWAPPABILITY GUIDE                                                  
                                                                             
  Backend-SPECIFIC (change when switching orchestrators):                    
    • .argo_workflows()  ->  .step_functions() / .maestro() / …             
                                                                             
  Backend-AGNOSTIC (unchanged across all orchestrators):                     
    • The flow file     —> pure Metaflow, no backend imports                  
    • .trigger()        —> Deployer API, works identically everywhere         
    • wait_for_result() —> polls via the Metaflow Client API                  
    • All assertions    —> use the Metaflow Client API (run.data, etc.)       

"""

import os
import pytest
from metaflow import Deployer

# Reuse the existing wait helper, it chains wait_for_run + wait_for_run_to_finish
# and surfaces any test_failure artifacts captured by @catch. 
from ..utils import wait_for_result


ROOT = os.path.dirname(__file__)


# Fixtures 
# test_id is provided by the top-level conftest.py and gives each test run a
# unique identifier so deployed flows don't collide.

@pytest.fixture
def test_tags(test_id):
    """Tags applied to the deployed flow for identification and cleanup."""
    return ["argo_workflows_tests", "simple_trigger_tests", test_id]


# The Test 

@pytest.mark.argo_workflows
def test_simple_trigger_lifecycle(test_tags):
    """
    End-to-end Deployer trigger lifecycle:
      1. Deploy a flow with @trigger
      2. Fire the trigger event with a parameter
      3. Wait for the triggered run to complete
      4. Assert the run succeeded and the parameter arrived correctly
      5. Clean up the deployment

    Each section below is annotated with what is backend-specific vs agnostic.
    """

    deployed_flow = None  # ensure cleanup runs even if deploy fails mid-way

    try:
        # Step 1: Deploy 
        # Create a deployment of SimpleTriggerFlow on the orchestrator.
        #
        # BACKEND-SPECIFIC: .argo_workflows() selects Argo as the backend.
        #   To target a different orchestrator, swap this single method call:
        #     .step_functions()   —> AWS Step Functions
        #     .maestro()          —> Netflix Maestro
        #   The rest of the test remains unchanged.
        deployed_flow = (
            Deployer(flow_file=os.path.join(ROOT, "simple_trigger_flow.py"))
            .argo_workflows()
            .create(tags=test_tags)
        )

        # Step 2: Trigger 
        # Fire the event that the @trigger decorator is listening for,
        # passing param_a as a keyword argument.
        #
        # BACKEND-AGNOSTIC: .trigger() is part of the Deployer API and works
        #   identically regardless of the orchestrator backend.
        triggered_run = deployed_flow.trigger(param_a="hello from trigger")

        # Step 3: Wait 
        # Poll until the triggered run finishes (or timeout).
        #
        # BACKEND-AGNOSTIC: wait_for_result uses the Metaflow Client API
        #   (run.finished_at, run.data), no backend-specific calls.
        #   It also re-raises any test_failure artifact captured by @catch
        #   in the flow, giving us a fast-fail with a real traceback instead
        #   of a generic timeout.
        run = wait_for_result(triggered_run, timeout=240)

        # Step 4: Assert 
        # Verify the run succeeded and that the parameter value was passed
        # through the trigger correctly and stored as an artifact.
        #
        # BACKEND-AGNOSTIC: run.successful and run.data are part of the
        #   Metaflow Client API; they work the same on every backend.
        assert run.successful, (
            f"Triggered run {run.pathspec} did not succeed. "
            f"Check the run logs for details."
        )

        # Verify the parameter arrived with the value we sent in .trigger().
        assert run.data.param_a == "hello from trigger", (
            f"Expected param_a='hello from trigger', "
            f"got param_a='{run.data.param_a}'"
        )

    finally:
        # Step 5: Cleanup 
        # remove the deployed flow to avoid leaving resources behind.
        #
        # BACKEND-SPECIFIC: .delete() is part of the Deployer API, but the
        # resources it cleans up are backend-specific (Argo WorkflowTemplate,
        # Step Functions state machine, etc.).
        if deployed_flow is not None:
            deployed_flow.delete()
