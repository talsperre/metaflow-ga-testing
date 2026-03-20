import pytest
import uuid

# Add pytest helpers


def pytest_addoption(parser):
    parser.addoption(
        "--test-id",
        action="store",
        default=None,
        help="A unique ID for this test run. One will be generated if not provided",
    )
    parser.addoption(
        "--extension",
        action="append",
        default=[],
        help="Path to a Metaflow extension to load. Can be repeated for multiple extensions.",
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


def pytest_configure(config):
    """
    Handle --extension flags by:
    1. Prepending extension paths to sys.path (PYTHONPATH approach from Netflix's run_tests.py line 204)
    2. Setting METAFLOW_EXTENSIONS_SEARCH_DIRS for scoped discovery (from extension_support/__init__.py)
    3. Adding extension test directories to pytest discovery
    """
    import os
    import sys
    from pathlib import Path

    extensions = config.getoption("--extension", default=[])
    if not extensions:
        return

    search_dirs = []

    for ext_path in extensions:
        ext_path = Path(ext_path).resolve()
        if not ext_path.exists():
            raise ValueError(f"Extension path does not exist: {ext_path}")

        # PYTHONPATH approach — prepend to sys.path
        # Same pattern used in Netflix/metaflow/test/core/run_tests.py line 204
        sys.path.insert(0, str(ext_path))
        search_dirs.append(str(ext_path))

        # Add extension tests to discovery
        # Convention: metaflow_extensions/<org>/tests/
        ext_ns = ext_path / "metaflow_extensions"
        if ext_ns.exists():
            for org_dir in ext_ns.iterdir():
                if org_dir.is_dir() and not org_dir.name.startswith("_"):
                    tests_dir = org_dir / "tests"
                    if tests_dir.exists():
                        sys.path.insert(0, str(tests_dir))
                        config.args.append(str(tests_dir))

    # Scope Metaflow extension discovery to specified dirs only
    # Prevents extension A from affecting extension B's run
    os.environ["METAFLOW_EXTENSIONS_SEARCH_DIRS"] = os.pathsep.join(search_dirs)
