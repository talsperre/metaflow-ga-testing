from metaflow import step, FlowSpec, Parameter


# a recursive conditional inside a foreach, with a diamond pattern before the join (supported)
class NestedRecursiveConditionalFlow1(FlowSpec):
    should_loop = Parameter("should_loop", default=True)
    max_recursion = Parameter("max_recursion", default=3)

    @step
    def start(self):
        print("Starting 👋")

        self.test_value = "start"
        self.case = "A"
        self.iterations = 0

        self.items = [1]

        self.next(self.split_work, foreach="items")

    @step
    def split_work(self):
        print("Now in split_work")
        self.test_value = "Went through split_work"

        if self.should_loop and self.iterations <= self.max_recursion:
            self.iterations += 1
            self.case = "B" if self.case == "A" else "A"
        else:
            self.case = "C" if self.input % 2 == 0 else "D"

        print(f"Case is '{self.case}'")

        self.next(
            {
                "C": self.branch_c,
                "D": self.branch_d,
                "A": self.split_work,
                "B": self.split_work,
            },
            condition="case",
        )

    @step
    def branch_c(self):
        print("Now in Branch C")
        self.test_value = "Went through branch C"

        self.next(self.common_e)

    @step
    def branch_d(self):
        print("Now in Branch D")
        self.test_value = "Went through branch D"

        self.next(self.common_e)

    @step
    def common_e(self):
        print("Now in Branch E")
        self.test_value = "Went through branch E"

        self.next(self.join_c_or_d)

    @step
    def join_c_or_d(self, inputs):
        self.merge_artifacts(inputs)
        for input in inputs:
            print(input.test_value)
        self.next(self.end)

    @step
    def end(self):
        print("Done! 🏁")

        print(self.test_value)


if __name__ == "__main__":
    NestedRecursiveConditionalFlow1()
