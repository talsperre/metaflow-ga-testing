"""
Sample extension tests — discovered automatically when running:
    tox -e local -- --extension tests/extensions/sample_extension

These tests demonstrate that:
1. The extension is loadable via sys.path (PYTHONPATH approach)
2. METAFLOW_EXTENSIONS_SEARCH_DIRS is scoped correctly
3. Extension tests are discovered alongside core tests
"""
import os
import pytest


@pytest.mark.local
def test_extension_loaded():
    """
    Verify that the sample extension directory is on sys.path.
    The --extension flag prepends the path via pytest_configure in conftest.py.
    """
    import sys
    # At least one path containing 'sample_extension' should be in sys.path
    ext_paths = [p for p in sys.path if "sample_extension" in p]
    assert len(ext_paths) > 0, (
        "sample_extension not found in sys.path. "
        "Did you pass --extension tests/extensions/sample_extension?"
    )


@pytest.mark.local
def test_extension_search_dirs():
    """
    Verify METAFLOW_EXTENSIONS_SEARCH_DIRS is set to scope
    Metaflow's extension discovery to our extension only.
    """
    search_dirs = os.environ.get("METAFLOW_EXTENSIONS_SEARCH_DIRS", "")
    assert "sample_extension" in search_dirs, (
        "METAFLOW_EXTENSIONS_SEARCH_DIRS not set correctly. "
        f"Got: '{search_dirs}'"
    )
