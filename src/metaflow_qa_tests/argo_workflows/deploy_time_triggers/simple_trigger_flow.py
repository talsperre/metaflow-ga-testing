"""
simple_trigger_flow.py, Minimal flow for the Deployer trigger lifecycle test.

This flow is triggered by an external event named test_simple_event.
It accepts one Parameter (param_a), stores it as an artifact, and uses the
@catch / re-raise pattern so that wait_for_run_to_finish in utils.py can
surface step-level errors without waiting for a timeout.

BACKEND-AGNOSTIC: This file is pure Metaflow; no Argo, Maestro, or Step
Functions imports.  It works with any orchestrator that supports @trigger.
"""

from metaflow import FlowSpec, step, Parameter, trigger, catch


@trigger(event="test_simple_event")
class SimpleTriggerFlow(FlowSpec):
    """Flow that fires on the test_simple_event event."""

    param_a = Parameter(
        name="param_a",
        default="default value A",
        type=str,
    )
 
    # @catch(var="test_failure") captures any exception raised in start
    # and stores it in self.test_failure instead of letting the step fail.
    # The end step then re-raises it.  This means the run always
    # reaches end (so wait_for_run_to_finish sees run.finished_at),
    # but the re-raise ensures run.successful is False and utils.py's
    # wait_for_run_to_finish can propagate the real error.
    @catch(var="test_failure")
    @step
    def start(self):
        # Store the parameter as an artifact so the test can assert on it.
        print(f"param_a = {self.param_a}")
        self.next(self.end)

    @step
    def end(self):
        # Re-raise any exception caught in start so the run is marked failed.
        test_failure = getattr(self, "test_failure", None)
        if test_failure is not None:
            raise test_failure
        print("Done!")


if __name__ == "__main__":
    SimpleTriggerFlow()
