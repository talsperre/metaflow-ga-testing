"""
Minimal flow for the event-trigger reference test (issue #6).

Kept intentionally simple: start → end, one parameter, @catch for
error surfacing. The only purpose is to verify the full trigger lifecycle:
deploy → event fires → run starts → parameter arrives → run completes.

BACKEND-AGNOSTIC: no Argo, Maestro, or Step Functions imports.
Works with any orchestrator that supports @trigger.
"""
from metaflow import FlowSpec, step, current, trigger, catch, Parameter

EVENT_NAME = "test_event"


@trigger(event=EVENT_NAME)
class TriggerFlow(FlowSpec):

    param_a = Parameter(
        name="param_a",
        default="default value A",
        type=str,
    )

    @catch(var="test_failure")
    @step
    def start(self):
        print(f"TriggerFlow started — run id: {current.run_id}")
        print(f"param_a = {self.param_a}")
        self.next(self.end)

    @step
    def end(self):
        test_failure = getattr(self, "test_failure", None)
        if test_failure is not None:
            raise test_failure
        print("TriggerFlow complete.")


if __name__ == "__main__":
    TriggerFlow()