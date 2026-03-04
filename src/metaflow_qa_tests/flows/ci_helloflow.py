"""
Unlike helloflow.py (which uses @resources(cpu=2) and foreach with 5 splits),
this flow is designed to run on resource-constrained CI runners (2 CPU / 7GB RAM)
where Minikube is allocated only 2 CPUs.
"""

from metaflow import FlowSpec, step, current


class CIHelloFlow(FlowSpec):
    @step
    def start(self):
        print("CI hello flow - start")
        print(vars(current))
        self.message = "hello from CI"
        self.next(self.end)

    @step
    def end(self):
        print(f"CI hello flow - end: {self.message}")
        assert self.message == "hello from CI"


if __name__ == "__main__":
    CIHelloFlow()
