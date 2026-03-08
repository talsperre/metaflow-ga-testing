# Metaflow Integration Testing

Starter repo for [GSoC 2026: Metaflow CI/CD — Kubernetes Integration Testing with GitHub Actions](https://docs.metaflow.org/internals/gsoc-2026).

## What's here

The test suite from [metaflow-qa-tests](https://github.com/saikonen/metaflow-qa-tests),
copied as-is. Tests are organized by backend:

- `basic/` — local execution via Runner API (no infrastructure needed)
- `kubernetes/` — steps run as K8s pods via Runner with `decospecs=["kubernetes"]`
- `argo_workflows/` — flows deployed and triggered via Deployer API (conditionals, triggers, parameters, cron)

Currently you can run everything with:

```bash
pip install .
pytest --pyargs metaflow_qa_tests -n auto
```

There is no tox, no markers, no CI, and no way to test extensions.

### Cross-backend HTML report

After running tests with tox (see Starter Tasks 1b), you can merge results into a single HTML report:

```bash
tox -e local && tox -e kubernetes && tox -e argo && python merge_results.py
```

This produces `test-results/report.html` — a matrix of tests × backends (local, kubernetes, argo) with pass/fail/skipped/not-run status and tracebacks for failures. Partial runs work: if you only ran `tox -e local`, the other columns show "—".

## Context

This test framework needs to work in two contexts:

- **OSS** — GitHub Actions for CI orchestration, [Metaflow dev stack](https://docs.metaflow.org/getting-started/devstack)
  (Minikube + Argo + MinIO) for Kubernetes infrastructure
- **Internal (Netflix)** — Maestro for CI orchestration, internal Kubernetes infrastructure

The test logic (pytest + flows) must be independent of the orchestration layer.
`tox` is the unified entry point: the same `tox -e <env>` command should work on a
developer's Mac, in GitHub Actions, and in Maestro. The only thing that changes between
these contexts is how the environment is set up before tox runs.

## Starter Tasks

Tasks are grouped into three tiers. **Tier 1** tasks are concrete and scoped — complete
them to demonstrate you can work with the codebase. **Tier 2** tasks require you to make
design decisions and handle edge cases. **Tier 3** tasks are open-ended architectural
challenges.

---

### Tier 1: Get the basics working

These tasks have clear deliverables. They build on each other in order.

#### 1a. Add pytest markers and register them in `pyproject.toml`

**The problem:** There are zero pytest markers in the repo. The only way to run
local-only tests is `pytest --pyargs metaflow_qa_tests.basic` — hardcoded paths. You
can't say `pytest -m local`.

**What to do:**
- Add a `[tool.pytest.ini_options]` section to `pyproject.toml` with marker
  registration (`local`, `kubernetes`, `argo_workflows`)
- Add `@pytest.mark.local` to the 3 tests in `basic/test_basic.py`
- Add `@pytest.mark.kubernetes` to the 3 tests in `kubernetes/test_kubernetes.py`
- Add `@pytest.mark.argo_workflows` to all tests across `argo_workflows/`
- Add `conftest.py` files in each subdirectory with `pytestmark` module-level markers
  as a fallback pattern
- Verify `pytest -m local --pyargs metaflow_qa_tests` works

**Demonstrates:** Understanding of pytest marker mechanics and why backend selection
matters for CI.

#### 1b. Add a `tox.ini` with backend-specific environments

**The problem:** There is no `tox.ini`. The main Metaflow repo's `tox.ini` is a
pass-through to a bash script. The QA tests need proper tox environments so `tox -e local`
Just Works.

**What to do:**
- Create a `tox.ini` with environments: `local`, `kubernetes`, `argo`, `all`
- `[testenv:local]` runs `pytest -m local --pyargs metaflow_qa_tests -v`
- `[testenv:kubernetes]` runs `pytest -m kubernetes --pyargs metaflow_qa_tests -v`
- `[testenv:argo]` runs `pytest -m argo_workflows --pyargs metaflow_qa_tests -v`
- Each environment installs the package + deps from `pyproject.toml`
- Add `passenv` for `METAFLOW_HOME`, `METAFLOW_PROFILE`, `METAFLOW_SERVICE_URL`,
  `METAFLOW_DEFAULT_DATASTORE`, `METAFLOW_DATASTORE_SYSROOT_S3`,
  `METAFLOW_KUBERNETES_NAMESPACE`, `METAFLOW_KUBERNETES_SECRETS`,
  `METAFLOW_SERVICE_INTERNAL_URL`, `AWS_*`, `HOME`, `USER` — these are needed when
  running inside `metaflow-dev shell`

**Depends on:** Task 1a.

**Demonstrates:** Understanding of tox environment management and the "one command
locally, same command in CI" story.

#### 1c. Create a GitHub Actions workflow for local tests

**The problem:** There is zero CI. Start with the simplest possible workflow.

**What to do:**
- Create `.github/workflows/test-local.yml`
- Trigger on push/PR to `main`
- Matrix across Python 3.10–3.13
- Steps: checkout, install Python, `pip install . tox`, `tox -e local`
- No Minikube, no dev stack — just pure local execution

**Depends on:** Tasks 1a + 1b.

**Demonstrates:** Basic GitHub Actions competency, and understanding that the
project is incremental (local first, then K8s).

---

### Tier 2: Handle the hard parts

These tasks require design decisions. There isn't one obvious right answer — your
approach and reasoning matter as much as the code.

#### 2a. Create a GitHub Actions workflow for Kubernetes + Argo tests

**The problem:** The local CI workflow is easy because it needs no infrastructure.
Running against Kubernetes and Argo in CI means spinning up the
[Metaflow dev stack](https://docs.metaflow.org/getting-started/devstack) inside
GitHub Actions.

**What to do:**
- Create `.github/workflows/test-kubernetes.yml`
- Checkout both `Netflix/metaflow` (for `metaflow-dev`) and this repo
- Install: `pip install ./metaflow kubernetes && pip install .`
- Start the dev stack: `MINIKUBE_CPUS=2 metaflow-dev all-up &` +
  `WAIT_TIMEOUT=600 metaflow-dev wait-until-ready`
- Run tests through the dev stack shell:
  `cat <<EOF | metaflow-dev shell` ... `tox -e kubernetes` ... `EOF`
- Teardown: `metaflow-dev down`

Study the existing reference at
[`Netflix/metaflow/.github/workflows/full-stack-test.yml`](https://github.com/Netflix/metaflow/blob/master/.github/workflows/full-stack-test.yml)
— it runs a single helloworld. You're extending this to the full test suite.

**The hard parts:**
- `metaflow-dev shell` sets environment variables (`METAFLOW_HOME`,
  `METAFLOW_PROFILE=local`, etc.). How do you bridge those into tox, which creates
  its own sub-environments? Does `passenv` cover it, or do you need a wrapper?
- The dev stack takes ~5 minutes to start. GitHub Actions runners have 2 CPUs and
  7GB RAM. Can the K8s and Argo tox environments run in parallel, or does that
  overwhelm the runner?
- K8s pods occasionally fail to schedule. Should retry logic live at the workflow
  level, the tox level, or the pytest level?

**Depends on:** Tasks 1a–1c.

#### 2b. Add a well-documented Deployer-based trigger test

**The problem:** The `argo_workflows/deploy_time_triggers/` and `parameter_tests/`
directories contain complex tests that deploy flows with `@trigger` and
`@trigger_on_finish`, but they're not well-documented and there's no simple example
showing the full lifecycle. Internally, similar tests run against Maestro — the
pattern needs to generalize across orchestrators.

**What to do:**
- Study the existing tests in `deploy_time_triggers/test_deploy_time_triggers.py`
  and `parameter_tests/test_parameters.py`
- Write a minimal, self-contained test (e.g., `test_simple_trigger.py`) that:
  1. Deploys a flow with `@trigger(event="test_event")` via
     `Deployer(...).argo_workflows().create()`
  2. Fires the event via `deployed_flow.trigger()`
  3. Uses `wait_for_run` / `wait_for_run_to_finish` from `utils.py`
  4. Asserts the triggered run succeeded and artifacts are correct
  5. Cleans up with `deployed_flow.delete()` in a `finally` block
- Comment the test clearly enough that someone adapting it for a different
  orchestrator (e.g., Maestro, Step Functions) can follow the pattern

**Think about:**
- The existing tests use `Deployer(...).argo_workflows()` — the `.argo_workflows()`
  call is backend-specific. How would you structure the test so the flow logic and
  assertions are reusable, but the deployment backend is swappable?
- The `utils.py` polling functions (`wait_for_run`, `wait_for_run_to_finish`) are
  Argo-agnostic — they use the Metaflow Client API. Are there parts of the test
  lifecycle that *are* backend-specific and need abstraction?

**Depends on:** Task 1a (for markers). Requires dev stack with Argo running.

#### 2c. Build cross-backend test result aggregation with HTML reporting

**The problem:** When you run `tox -e local` and then `tox -e kubernetes`, you get
two separate pytest outputs. There's no unified view of which tests passed on which
backend, no way to compare results, and no artifact to attach to a PR.

**What to build:**

A mechanism that collects results from multiple tox/pytest runs and produces a single
HTML report showing:
- Per-backend pass/fail matrix (test x backend)
- Failure details with tracebacks
- Test durations (K8s tests are much slower than local — this matters)
- Summary statistics

**Design questions to answer:**
- Results come from separate tox invocations (separate processes, separate Python
  environments). How do you persist intermediate results between runs? Options:
  pytest's `--junitxml`, a custom pytest plugin writing JSON, or `pytest-html` with
  post-processing.
- Should aggregation happen as a pytest plugin, a standalone script that runs after
  all tox envs finish, or a tox post-command?
- How does this integrate with GitHub Actions? The HTML should be uploadable as a
  workflow artifact and ideally summarized in the PR check run via the Checks API.
- What does the report look like when some backends weren't tested (e.g., a
  contributor only ran `tox -e local` because they don't have the dev stack)?

**Reference:** Look at [pytest-html](https://github.com/pytest-dev/pytest-html),
[allure-pytest](https://github.com/allure-framework/allure-python), and Metaflow's
own core test harness (`Netflix/metaflow/test/core/run_tests.py`) which has its own
result collection across CLI vs API executors and multiple graph types.

---

### Tier 3: Architectural challenges

These are open-ended design problems. A proposal that demonstrates thoughtful
engagement with these — even without code — would strengthen a GSoC application.

#### 3a. Design an extension testing framework

**The problem:** Metaflow has a
[namespace-package extension system](https://github.com/Netflix/metaflow-extensions-template)
where users install packages under `metaflow_extensions/<org>/` that add decorators,
environments, datastores, CLI commands, etc. Currently there's no way to run the QA
test suite against a custom extension — or against a combination of extensions.

**Real-world scenarios:**
- A team builds a `@custom_gpu` decorator as an extension. They want to verify it
  doesn't break core Metaflow behavior (run the basic tests with the extension
  installed) AND run extension-specific tests.
- Two extensions exist (`metaflow-ext-a`, `metaflow-ext-b`). They work individually
  but nobody has tested them together. Run the suite with both installed.
- An internal Netflix extension works with Maestro triggers. Run the same trigger
  tests against both Argo and Maestro, swapping only the orchestration backend.

**Design questions:**
- How do you install extensions into a tox environment dynamically? Options: tox
  `deps` substitution, a conftest that shells out to pip, a wrapper script, or
  tox factors (`tox -e 'local-{ext_a,ext_b}'`).
- How does test discovery work for extension-provided tests? Entry points, a known
  directory convention, or a config file?
- How do you handle the matrix explosion? 3 backends x 3 extensions x combinations
  is a lot of tox environments.
- Metaflow auto-discovers extensions on import. How do you prevent extension A from
  polluting a run testing extension B? Is tox environment isolation sufficient?

**Reference:** Study `metaflow/extension_support/__init__.py` (discovery/loading),
`Netflix/metaflow/test/extensions/` (existing extension test harness), and the
[extensions template](https://github.com/Netflix/metaflow-extensions-template).

#### 3b. Design the marker taxonomy for feature-level test selection

**The problem:** Task 1a adds backend markers (`local`, `kubernetes`, `argo_workflows`).
But the test suite also has feature dimensions: `conda`, `pypi`, `triggers`,
`conditionals`, `parameters`, `cron`, `notifications`. A test like
`test_kubernetes_conda_flow` lives at the intersection of two dimensions.

**Design questions:**
- Should a test have multiple markers (`@pytest.mark.kubernetes` AND
  `@pytest.mark.conda`)? How does `pytest -m "kubernetes and conda"` interact
  with tox environments?
- Some features require infrastructure (conda needs a package cache, triggers need
  Argo Events). Should feature markers imply backend requirements, or are they
  orthogonal?
- Auto-skip gets more complex: `test_kubernetes_conda_flow` should skip if
  Kubernetes is unavailable, but `test_conda_flow` (local + conda) should skip if
  conda isn't installed. Different skip reasons for different markers.
- How do you keep the marker taxonomy maintainable as the test suite grows? Is
  there a conftest pattern that infers markers from directory structure + test name,
  or is explicit annotation better?

This task is primarily a design document, not code. Propose a marker scheme, show
how it handles the existing tests, and explain the trade-offs.

## Key References

- [Metaflow Dev Stack](https://docs.metaflow.org/getting-started/devstack) — Minikube + Argo + MinIO local environment
- [Runner API](https://docs.metaflow.org/metaflow/managing-flows/runner) — programmatic flow execution
- [Deployer API](https://docs.metaflow.org/metaflow/managing-flows/deployer) — deploy flows to Argo/Step Functions
- [Metaflow Extensions Template](https://github.com/Netflix/metaflow-extensions-template) — how extensions are structured
- [Extension loading code](https://github.com/Netflix/metaflow/blob/master/metaflow/extension_support/__init__.py) — how Metaflow discovers extensions
- [Existing full-stack CI](https://github.com/Netflix/metaflow/blob/master/.github/workflows/full-stack-test.yml) — Minikube in GitHub Actions
- [Metaflow core test harness](https://github.com/Netflix/metaflow/tree/master/test/core) — custom integration test framework (for reference, not pytest-based)
