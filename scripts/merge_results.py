#!/usr/bin/env python3
"""
Merge pytest-json-report results from multiple tox backends
into a single HTML report showing a per-backend matrix.

Usage:
    tox -e local && tox -e kubernetes && python scripts/merge_results.py
    
Output: test-results/report.html
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

BACKENDS = ["local", "kubernetes", "argo"]
RESULTS_DIR = Path("test-results")
OUTPUT_FILE = RESULTS_DIR / "report.html"

OUTCOME_SYMBOL = {
    "passed": "✓",
    "failed": "✗",
    "skipped": "~",
    "not_run": "—",
}

OUTCOME_CLASS = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
    "not_run": "not-run",
}


def load_results():
    """Load JSON results for each backend that has been run."""
    results = {}
    for backend in BACKENDS:
        path = RESULTS_DIR / f"{backend}.json"
        if path.exists():
            with open(path) as f:
                results[backend] = json.load(f)
            print(f"Loaded {backend}: {path}")
        else:
            print(f"Skipping {backend}: {path} not found")
    return results


def build_matrix(results):
    """
    Build a matrix of {test_id: {backend: {outcome, duration, traceback}}}.
    Tests not run on a backend are marked as 'not_run'.
    """
    all_tests = {}

    for backend, data in results.items():
        for test in data.get("tests", []):
            node_id = test["nodeid"]
            # Use short name for display
            short_name = node_id.split("::")[-1] if "::" in node_id else node_id

            if node_id not in all_tests:
                all_tests[node_id] = {
                    "short_name": short_name,
                    "backends": {}
                }

            # Extract traceback if failed
            traceback = ""
            if test.get("outcome") == "failed":
                call = test.get("call", {})
                traceback = call.get("longrepr", "")

            all_tests[node_id]["backends"][backend] = {
                "outcome": test.get("outcome", "unknown"),
                "duration": round(test.get("call", {}).get("duration", 0), 2),
                "traceback": traceback,
            }

    return all_tests


def generate_html(matrix, results):
    """Generate HTML report from the matrix."""
    run_backends = list(results.keys())
    not_run_backends = [b for b in BACKENDS if b not in results]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count summary stats
    total = len(matrix)
    passed = sum(
        1 for t in matrix.values()
        for b, r in t["backends"].items()
        if r["outcome"] == "passed"
    )
    failed = sum(
        1 for t in matrix.values()
        for b, r in t["backends"].items()
        if r["outcome"] == "failed"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metaflow QA Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat {{ background: white; padding: 15px 25px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
        th {{ background: #333; color: white; padding: 12px 16px; text-align: left; }}
        td {{ padding: 10px 16px; border-bottom: 1px solid #eee; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover {{ background: #f9f9f9; }}
        .test-name {{ font-family: monospace; font-size: 0.9em; }}
        .passed {{ color: #22863a; font-weight: bold; }}
        .failed {{ color: #cb2431; font-weight: bold; cursor: pointer; }}
        .skipped {{ color: #b08800; }}
        .not-run {{ color: #999; }}
        .duration {{ color: #666; font-size: 0.85em; }}
        .traceback {{ display: none; background: #ffeef0; border: 1px solid #fdb8c0; border-radius: 4px; padding: 10px; margin-top: 8px; font-family: monospace; font-size: 0.8em; white-space: pre-wrap; word-break: break-all; }}
        .not-run-notice {{ background: #fff3cd; padding: 10px 16px; border-radius: 4px; margin-bottom: 20px; color: #856404; }}
    </style>
</head>
<body>
    <h1>Metaflow QA Test Report</h1>
    <div class="meta">Generated at {generated_at} — ✓ = passed, ✗ = failed, ~ = skipped, — = not run</div>
    
    <div class="summary">
        <div class="stat">
            <div class="stat-number">{total}</div>
            <div class="stat-label">Total Tests</div>
        </div>
        <div class="stat">
            <div class="stat-number passed">{passed}</div>
            <div class="stat-label">Passed</div>
        </div>
        <div class="stat">
            <div class="stat-number failed">{failed}</div>
            <div class="stat-label">Failed</div>
        </div>
    </div>
"""

    if not_run_backends:
        html += f"""
    <div class="not-run-notice">
        Backends not run: {", ".join(not_run_backends)} — showing "—" for missing results.
        Run <code>tox -e {not_run_backends[0]}</code> to include them.
    </div>
"""

    html += """
    <table>
        <thead>
            <tr>
                <th>Test</th>
"""
    for backend in BACKENDS:
        html += f"                <th>{backend}</th>\n"

    html += """            </tr>
        </thead>
        <tbody>
"""

    for test_id, test_data in sorted(matrix.items()):
        html += f"""            <tr>
                <td class="test-name">{test_data['short_name']}</td>
"""
        for backend in BACKENDS:
            if backend in test_data["backends"]:
                result = test_data["backends"][backend]
                outcome = result["outcome"]
                symbol = OUTCOME_SYMBOL.get(outcome, "?")
                css_class = OUTCOME_CLASS.get(outcome, "")
                duration = result["duration"]
                traceback = result["traceback"]

                if outcome == "failed" and traceback:
                    tb_id = f"tb-{test_id.replace('/', '-').replace('::', '-')}-{backend}"
                    html += f"""                <td>
                    <span class="{css_class}" onclick="toggleTraceback('{tb_id}')">{symbol}</span>
                    <span class="duration">({duration}s)</span>
                    <div id="{tb_id}" class="traceback">{traceback}</div>
                </td>
"""
                else:
                    html += f"""                <td>
                    <span class="{css_class}">{symbol}</span>
                    <span class="duration">({duration}s)</span>
                </td>
"""
            else:
                html += f"""                <td><span class="not-run">{OUTCOME_SYMBOL['not_run']}</span></td>
"""

        html += "            </tr>\n"

    html += """        </tbody>
    </table>

    <script>
        function toggleTraceback(id) {
            const el = document.getElementById(id);
            el.style.display = el.style.display === 'block' ? 'none' : 'block';
        }
    </script>
</body>
</html>"""

    return html


def main():
    if not RESULTS_DIR.exists():
        print(f"Error: {RESULTS_DIR} directory not found.")
        print("Run tox -e local first to generate results.")
        sys.exit(1)

    results = load_results()

    if not results:
        print("No result files found in test-results/")
        print("Run: tox -e local && python scripts/merge_results.py")
        sys.exit(1)

    matrix = build_matrix(results)
    html = generate_html(matrix, results)

    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    print(f"\nReport generated: {OUTPUT_FILE}")
    print(f"Open in browser: file://{OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()

