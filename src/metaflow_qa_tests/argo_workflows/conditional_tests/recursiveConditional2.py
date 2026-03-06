from metaflow import step, FlowSpec, Parameter


# looping from any other step than the split-switch onto itself is not allowed.
class RecursiveConditionalFlow2(FlowSpec):
    should_loop = Parameter("should_loop", default=True)
    max_recursion = Parameter("max_recursion", default=3)

    @step
    def start(self):
        print("Starting 👋")

        self.test_value = "start"
        self.continue_loop = "loop" if self.should_loop else "break"
        self.iterations = 0

        self.next(self.recursive_step)

    @step
    def recursive_step(self):
        print("Starting 👋")

        self.test_value = "start"

        if self.iterations < self.max_recursion:
            self.iterations += 1
            self.continue_loop = "loop"
        else:
            self.continue_loop = "break"

        self.next(
            {"break": self.branch_a, "loop": self.start},
            condition="continue_loop",
        )

    @step
    def branch_a(self):
        print("Now in Branch A")
        self.test_value = "Went through branch A"

        self.next(self.recursive_step2)

    @step
    def recursive_step2(self):
        print("Starting 👋")

        self.test_value = "start"

        if self.iterations < self.max_recursion:
            self.iterations += 1
            self.continue_loop = "loop"
        else:
            self.continue_loop = "break"

        self.next(
            {"break": self.end, "loop": self.branch_b_recursion},
            condition="continue_loop",
        )

    @step
    def branch_b_recursion(self):
        print("should not be able to loop from a longer recursive branch either.")
        self.next(self.recursive_step2)

    @step
    def end(self):
        print("Done! 🏁")

        print(self.test_value)


if __name__ == "__main__":
    RecursiveConditionalFlow2()
