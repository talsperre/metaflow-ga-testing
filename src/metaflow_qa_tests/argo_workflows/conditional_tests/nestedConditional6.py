from metaflow import step, FlowSpec, card


# A conditional branch in a foreach split with a diamond pattern.
# This gets around the issue of current Argo foreach-join input-paths
class NestedConditionalFlow6(FlowSpec):
    @card
    @step
    def start(self):
        print("Starting 👋")

        self.test_value = "start"
        # self.items = [1, 2]
        self.items = [1]

        self.next(self.split_work, foreach="items")

    @step
    def split_work(self):
        print("Now in split_work")
        self.test_value = "Went through split_work"
        if self.input % 2 == 0:
            self.condition = "true"
        else:
            self.condition = "false"

        self.next(
            {"true": self.branch_c, "false": self.branch_d}, condition="condition"
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
        for input in inputs:
            print(input.test_value)
        self.next(self.end)

    @step
    def end(self):
        print("Done! 🏁")


if __name__ == "__main__":
    NestedConditionalFlow6()
