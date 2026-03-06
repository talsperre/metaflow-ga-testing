from metaflow import step, FlowSpec


# A conditional skip branch in a foreach split
class ConditionalSkipFlow4(FlowSpec):
    @step
    def start(self):
        print("Starting 👋")

        self.test_value = "start"
        self.items = [1, 2, 3]

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

        self.next(
            {"true": self.branch_c, "false": self.branch_d, "skip": self.common_c_d_e},
            condition="condition",
        )

    @step
    def branch_c(self):
        print("Now in Branch C")
        self.test_value = "Went through branch C"

        self.next(self.common_c_d)

    @step
    def branch_d(self):
        print("Now in Branch D")
        self.test_value = "Went through branch D"

        self.next(self.common_c_d)

    @step
    def common_c_d(self):
        print("Now in Common for C-D")
        self.test_value = "Went through branch D"

        self.next(self.common_c_d_e)

    @step
    def common_c_d_e(self):
        print("Now in Common for C-D-E")
        self.test_value = "Went through branch D"

        self.next(self.join_foreach)

    @step
    def join_foreach(self, inputs):
        for input in inputs:
            print(input.test_value)
        self.next(self.end)

    @step
    def end(self):
        print("Done! 🏁")


if __name__ == "__main__":
    ConditionalSkipFlow4()
