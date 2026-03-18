# Marker Taxonomy for Feature-Level Test Selection

## Overview

Issue #2 added backend markers (`local`, `kubernetes`, `argo_workflows`) 
so you can run tests by where they execute. But some tests also exercise 
specific features like conda environments or Argo triggers. This document 
proposes a second dimension of markers for these features.

The key idea: **two independent dimensions**.

- **Backend marker** — answers "where does this test run?"
- **Feature marker** — answers "what does this test exercise?"

A test like `test_kubernetes_conda_flow` gets BOTH `kubernetes` AND `conda`.
They are orthogonal — neither implies the other. This lets you filter by
either dimension independently:
```bash
pytest -m kubernetes          # all kubernetes tests
pytest -m conda               # all conda tests across all backends
pytest -m "kubernetes and conda"  # only kubernetes conda tests
```

## Backend Markers

Backend markers are inferred automatically from directory structure via
`conftest.py pytestmark` — no manual annotation needed on individual tests.

| Marker | Description | How applied |
|--------|-------------|-------------|
| `local` | Runs against local backend via Runner API. No infrastructure needed. | `basic/conftest.py` pytestmark |
| `kubernetes` | Steps run as Kubernetes pods via Runner API with `decospecs=["kubernetes"]` | `kubernetes/conftest.py` pytestmark |
| `argo_workflows` | Flows deployed and triggered via Deployer API on Argo Workflows | `argo_workflows/conftest.py` pytestmark |

## Feature Markers

Feature markers describe WHAT a test exercises, independent of which
backend it runs on. Most are inferred automatically from test names.
The exception is `triggers` — `test_events` doesn't contain "trigger"
in its name so it needs explicit annotation.

| Marker | Description | How applied |
|--------|-------------|-------------|
| `conda` | Test uses `@conda_base` decorator. Requires conda or micromamba installed. | inferred from test name containing "conda" |
| `pypi` | Test uses `@pypi_base` decorator. Requires pypi environment support. | inferred from test name containing "pypi" |
| `conditionals` | Test exercises conditional branching flows. | inferred from test name containing "conditional" |
| `triggers` | Test deploys flows with `@trigger` or `@trigger_on_finish` and fires events. | explicit annotation (see note above) |
| `parameters` | Test exercises parameter passing and trigger-on-finish deployments. | inferred from test name containing "param" |
| `cron` | Test deploys flows with cron-based scheduling. | inferred from test name containing "cron" |
| `notifications` | Test verifies Argo Workflows notification configuration. | inferred from test name containing "notification" |

## Complete Test Marker Table

Every test mapped to its backend and feature markers:

| Test | Backend | Feature |
|------|---------|---------|
| `test_helloflow` | `local` | — |
| `test_conda_flow` | `local` | `conda` |
| `test_pypi_flow` | `local` | `pypi` |
| `test_kubernetes_helloflow` | `kubernetes` | — |
| `test_kubernetes_conda_flow` | `kubernetes` | `conda` |
| `test_kubernetes_pypi_flow` | `kubernetes` | `pypi` |
| `test_argo_helloflow` | `argo_workflows` | — |
| `test_argo_conda_flow` | `argo_workflows` | `conda` |
| `test_argo_pypi_flow` | `argo_workflows` | `pypi` |
| `test_argo_notifications` | `argo_workflows` | `notifications` |
| `test_conditional_flows` | `argo_workflows` | `conditionals` |
| `test_failing_conditional_flows` | `argo_workflows` | `conditionals` |
| `test_successful_trigger_deployments` | `argo_workflows` | `triggers` |
| `test_successful_trigger_on_finish_deployments` | `argo_workflows` | `triggers` |
| `test_expected_failing_trigger_deployments` | `argo_workflows` | `triggers` |
| `test_events` | `argo_workflows` | `triggers` |
| `test_cron` | `argo_workflows` | `cron` |
| `test_base_params` | `argo_workflows` | `parameters` |

## Skip Logic

A single `pytest_collection_modifyitems` hook in root `conftest.py`
handles all skip conditions automatically. When a test has multiple
markers (e.g. `kubernetes` AND `conda`), it skips if EITHER condition
is not met — no per-test skip decorators needed.

**Infrastructure checks (environment variables):**
- `kubernetes` → skip if `METAFLOW_KUBERNETES_NAMESPACE` not set
- `argo_workflows` → skip if `METAFLOW_ARGO_EVENTS_WEBHOOK_URL` not set

**Tool checks (shutil.which):**
- `conda` → skip if neither `conda` nor `micromamba` found
- `pypi` → skip if `pip` not found

This gives clean skip messages instead of confusing failures:
```
SKIPPED test_conda_flow — conda/micromamba not installed
SKIPPED test_kubernetes_conda_flow — Kubernetes unavailable
```

## Tox Integration

No new tox environments needed. Feature markers compose cleanly with
the existing three backend environments using `--` to pass pytest flags:
```bash
tox -e local                          # all local tests
tox -e local -- -m conda              # local conda tests only
tox -e kubernetes -- -m conda         # kubernetes conda tests only
tox -e argo -- -m triggers            # argo trigger tests only
tox -e argo -- -m conditionals        # argo conditional tests only
tox -e argo -- -m "not conditionals"  # argo tests excluding conditionals
```

Adding `tox -e local-conda` would mean 3 backends × 7 features = 21
potential environments. Marker flags achieve the same result with
zero extra maintenance.
## Trade-offs: orthogonal vs hierarchical markers

**Hierarchical** means feature markers imply backend markers —
`@pytest.mark.triggers` would automatically imply `@pytest.mark.argo_workflows`.
This reduces annotation: one marker instead of two.

The problem: the implication breaks the moment a second backend supports the
same feature. If Maestro trigger tests are added later, `triggers` can no longer
imply `argo_workflows` without excluding them. Every test using `triggers` would
need to be re-annotated.

**Orthogonal** means markers are independent — `triggers` says nothing about
which backend. It requires two markers per test but the taxonomy stays stable as
new backends are added. `pytest -m "triggers and argo_workflows"` and
`pytest -m "triggers and maestro"` both work without changing any existing tests.

Given the README explicitly mentions Maestro as a future orchestrator, orthogonal
is the right choice here. The small annotation overhead is worth the extensibility.
