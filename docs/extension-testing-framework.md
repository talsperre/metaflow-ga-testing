# Extension Testing Framework

## Problem

The QA test suite has no way to:
- Run with a custom extension installed to check for regressions
- Run extension-specific tests alongside core tests
- Test combinations of extensions together

## Design

### CLI Interface

```bash
# Test core with one extension
tox -e local -- --extension ./path/to/my-extension

# Test with multiple extensions
tox -e local -- --extension ./ext-a --extension ./ext-b

# Extension's own tests are discovered automatically
tox -e local -- --extension ./ext-a
```

### Dynamic Installation

Two modes based on Netflix's own patterns:

**Local/unpublished extensions — PYTHONPATH approach**

Based on `Netflix/metaflow/test/core/run_tests.py` line 204,
extensions are loaded by prepending the path to `sys.path`.
No pip install needed — works for local and unpublished extensions.

**Published extensions — tox deps**

```ini
[testenv:local-myext]
deps = my-published-extension
```

### How --extension Works

When `--extension ./my-ext` is passed, `pytest_configure` in
root `conftest.py`:

1. Prepends `./my-ext` to `sys.path` — Python finds the extension
2. Sets `METAFLOW_EXTENSIONS_SEARCH_DIRS=./my-ext` — scopes
   Metaflow's discovery to that directory only
3. Scans `./my-ext/metaflow_extensions/<org>/tests/` and adds
   to pytest's path for automatic test discovery

### Test Discovery Convention

Extensions place pytest tests at:

```
metaflow_extensions/<org>/tests/
```

This matches the namespace package structure from the
[extensions template](https://github.com/Netflix/metaflow-extensions-template).
`conftest.py` scans for this directory automatically.

### Backend x Extension Matrix

For known CI combinations — tox factors:

```ini
[tox]
envlist = local, kubernetes, argo, local-{ext_a,ext_b}

[testenv:local-{ext_a,ext_b}]
deps =
    ext_a: ./tests/extensions/ext_a
    ext_b: ./tests/extensions/ext_b
commands = pytest -m local --pyargs metaflow_qa_tests -v {posargs}
```

For ad-hoc local testing — use `--extension` flag without
creating new environments.

### Isolation Guarantees

**What's safe:**

- `METAFLOW_EXTENSIONS_SEARCH_DIRS` scopes discovery per invocation
- Tox creates fresh virtualenvs per factor — extension A can't
  affect extension B's tox factor run
- `METAFLOW_DEBUG_EXT=1` shows extension load order for debugging

**What can go wrong:**

- Extensions modify global state at import time
- If two extensions override the same decorator, last one wins
- Within a single pytest session, extensions accumulate — use
  separate tox invocations for true isolation

### Override Behavior Testing

```bash
METAFLOW_DEBUG_EXT=1 tox -e local -- --extension ./ext-a --extension ./ext-b
```

Debug output shows load order. Assert that later-loaded extension
behavior takes precedence.

## Prototype

`tests/extensions/sample_extension/` is a minimal working example.

Run it with:

```bash
tox -e local -- --extension tests/extensions/sample_extension
```

Expected output:

```
test_sample_extension.py::test_extension_loaded PASSED
test_sample_extension.py::test_extension_search_dirs PASSED
```

## Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| PYTHONPATH (chosen for local) | No pip install, fast | Requires namespace convention |
| pip install | Works with any package | Slower, needs published package |
| tox factors (chosen for CI) | Best isolation | New env per combination |
| --extension flag | Flexible, no new envs | Less isolation within session |
