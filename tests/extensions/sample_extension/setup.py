from setuptools import find_namespace_packages, setup

setup(
    name="metaflow-sample-extension",
    version="0.1.0",
    description="Minimal sample extension for testing the extension framework",
    packages=find_namespace_packages(include=["metaflow_extensions.*"]),
    zip_safe=False,
)
