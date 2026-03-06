from metaflow import step, FlowSpec, Parameter


class RecursiveConditionalFlow1(FlowSpec):
    should_loop = Parameter("should_loop", default=True)
    max_recursion = Parameter("max_recursion", default=3)

    @step
    def start(self):
        print("Starting 👋")

        self.test_value = "start"
        self.case = "A" if self.should_loop else "break"
        self.iterations = 0

        self.next(self.recursive_step)

    @step
    def recursive_step(self):
        print("Starting 👋")

        self.test_value = "start"

        if self.iterations <= self.max_recursion:
            self.iterations += 1
            self.case = "B" if self.case == "A" else "A"
        else:
            self.case = "break"

        print(f"Case is '{self.case}'")
        self.next(
            {
                "break": self.branch_a,
                "A": self.recursive_step,
                "B": self.recursive_step,
            },
            condition="case",
        )

    @step
    def branch_a(self):
        print("Now in Branch A")
        self.test_value = "Went through branch A"

        self.next(self.end)

    @step
    def end(self):
        print("Done! 🏁")

        print(self.test_value)


if __name__ == "__main__":
    RecursiveConditionalFlow1()
