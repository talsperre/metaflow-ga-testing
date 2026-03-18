import pytest
import uuid
import os
import shutil


# Add pytest helpers
def pytest_addoption(parser):
    parser.addoption(
        "--test-id",
        action="store",
        default=None,
        help="A unique ID for this test run. One will be generated if not provided",
    )


@pytest.fixture(scope="session")
def test_id(request):
    test_id = request.config.getoption("--test-id")
    if test_id is not None:
        return test_id
    # check for pytest-xdist availability
    if hasattr(request.config, "workerinput"):
        testrunid = request.config.workerinput["testrunuid"]
        return testrunid[:8]
    return uuid.uuid4().hex[:8]


def pytest_collection_modifyitems(items):
    """
    Automatically infer feature markers from test names and
    apply skip logic based on available infrastructure and tools.
    
    Backend markers (local, kubernetes, argo_workflows) are already
    inferred from directory structure via conftest.py pytestmark.
    
    Feature markers are inferred from test names:
    - "conda" in name → @pytest.mark.conda
    - "pypi" in name → @pytest.mark.pypi
    - "notification" in name → @pytest.mark.notifications
    - "conditional" in name → @pytest.mark.conditionals
    - "cron" in name → @pytest.mark.cron
    - "param" or "base_params" in name → @pytest.mark.parameters
    
    Triggers marker must be explicit (test_events doesn't contain "trigger").
    """
    for item in items:
        # ── Feature marker inference from test name ──────────────────
        name = item.name.lower()

        if "conda" in name:
            item.add_marker(pytest.mark.conda)
        if "pypi" in name:
            item.add_marker(pytest.mark.pypi)
        if "notification" in name:
            item.add_marker(pytest.mark.notifications)
        if "conditional" in name:
            item.add_marker(pytest.mark.conditionals)
        if "cron" in name:
            item.add_marker(pytest.mark.cron)
        if "param" in name or "base_params" in name:
            item.add_marker(pytest.mark.parameters)

        # ── Skip logic ───────────────────────────────────────────────

        # Infrastructure checks
        if "kubernetes" in item.keywords:
            if not os.environ.get("METAFLOW_KUBERNETES_NAMESPACE"):
                item.add_marker(pytest.mark.skip(
                    reason="Kubernetes unavailable: METAFLOW_KUBERNETES_NAMESPACE not set"
                ))

        if "argo_workflows" in item.keywords:
            if not os.environ.get("METAFLOW_ARGO_EVENTS_WEBHOOK_URL"):
                item.add_marker(pytest.mark.skip(
                    reason="Argo unavailable: METAFLOW_ARGO_EVENTS_WEBHOOK_URL not set"
                ))

        # Tool checks
        if "conda" in item.keywords:
            if not shutil.which("conda") and not shutil.which("micromamba"):
                item.add_marker(pytest.mark.skip(
                    reason="conda/micromamba not installed"
                ))

        if "pypi" in item.keywords:
            if not shutil.which("pip"):
                item.add_marker(pytest.mark.skip(
                    reason="pip not available"
                ))