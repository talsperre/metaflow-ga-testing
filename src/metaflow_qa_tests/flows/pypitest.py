from metaflow import FlowSpec, step, pypi_base


@pypi_base(packages={"pandas": "1.5.2", "numpy": "1.26.4"}, python="3.11")
class PyPIFlow(FlowSpec):
    @step
    def start(self):
        print("In start")
        import pandas as pd

        self.next(self.a)

    @step
    def a(self):
        import pandas as pd

        print("Testing pandas")
        dates = pd.date_range("20130101", periods=6)
        print(dates)
        self.next(self.end)

    @step
    def end(self):
        print("In end")


if __name__ == "__main__":
    PyPIFlow()
