from metaflow import FlowSpec, step, current, resources


def verify_otel_init():
    # verifies that OTEL dependencies can be imported successfully
    from metaflow.metaflow_config import OTEL_ENDPOINT

    if OTEL_ENDPOINT:
        print(f"METAFLOW_OTEL_ENDPOINT is set to {OTEL_ENDPOINT}")
    else:
        print("METAFLOW_OTEL_ENDPOINT is not set. OTEL import was not attempted.")


class HelloFlow(FlowSpec):
    @step
    def start(self):
        verify_otel_init()

        print("In A")
        print(vars(current))
        self.var_1 = ["d", "u", "m", "m", "y"]

        self.next(self.b, foreach="var_1")

    @resources(cpu=2, memory=1280)
    @step
    def b(self):
        print("In B")
        self.next(self.join)

    @resources(memory=4096)
    @step
    def join(self, inputs):
        print("YO")
        self.next(self.end)

    @step
    def end(self):
        print("In end")


if __name__ == "__main__":
    HelloFlow()
