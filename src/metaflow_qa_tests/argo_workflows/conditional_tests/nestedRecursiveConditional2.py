from metaflow import step, FlowSpec, Parameter


# a foreach join step that is a recursive conditional.
# NOTE: This is not supported.
class NestedRecursiveConditionalFlow2(FlowSpec):
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

    @step
    def join(self, inputs):
        self.merge_artifacts(inputs)
        for input in inputs:
            print(input.test_value)

        if self.iterations <= self.max_recursion:
            self.iterations += 1
            self.case = "B" if self.case == "A" else "A"
        else:
            self.case = "break"

        print(f"Case is '{self.case}'")
        self.next(
            {
                "break": self.post_joining,
                "A": self.recursive_step,
                "B": self.recursive_step,
            },
            condition="case",
        )

    @step
    def post_joining(self):
        print("Now in a post-join state")
        self.test_value = "Went through post-joining"

        self.next(self.end)

    @step
    def end(self):
        print("Done! 🏁")

        print(self.test_value)


if __name__ == "__main__":
    NestedRecursiveConditionalFlow2()
