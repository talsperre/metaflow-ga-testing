from metaflow import step, FlowSpec


# A conditional skip foreach inside a conditional branch with skips.
class ConditionalSkipFlow5(FlowSpec):
    @step
    def start(self):
        print("Starting 👋")
        # self.condition = "foreach"
        self.condition = "foreach"

        self.next(
            {
                "true": self.branch_c,
                "false": self.branch_d,
                "foreach": self.deal_work,
                "skip": self.end,
            },
            condition="condition",
        )

    @step
    def deal_work(self):
        print("Dealing work")

        self.test_value = "deal_work"
        self.items = [1]

        self.next(self.split_work, foreach="items")

    @step
    def split_work(self):
        print("Now in Branch B")
        if self.input % 2 == 0:
            self.condition = "true"
        elif self.input % 3 == 0:
            self.condition = "skip"
        else:
            self.condition = "false"

        self.next(self.join_foreach)

    @step
    def branch_c(self):
        print("Now in Branch C")
        self.test_value = "Went through branch C"

        self.next(self.end)

    @step
    def branch_d(self):
        print("Now in Branch D")
        self.test_value = "Went through branch D"

        self.next(self.deal_work)

    @step
    def join_foreach(self, inputs):
        for input in inputs:
            print(input.test_value)
        self.next(self.end)

    @step
    def end(self):
        print("Done! 🏁")


if __name__ == "__main__":
    ConditionalSkipFlow5()
