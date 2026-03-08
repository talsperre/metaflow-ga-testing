#!/usr/bin/env python3
"""
Merge test results from multiple pytest runs into a single HTML report.

Each tox environment (local, kubernetes, argo) writes JUnit XML via:
    pytest --junitxml=test-results/local.xml ...

Run after tox:
    tox -e local && tox -e kubernetes && tox -e argo && python merge_results.py

Or with partial results:
    tox -e local && python merge_results.py

Output: test-results/report.html
"""

import argparse
import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junitxml(path: Path) -> dict[str, dict]:
    """
    Parse a JUnit XML file and return a dict of test_id -> result.
    test_id format: classname::name (for parametrized: classname::name[param])
    """
    results = {}
    try:
        tree = ET.parse(path)
    except (ET.ParseError, FileNotFoundError):
        return results

    root = tree.getroot()
    for testcase in root.iter("testcase"):
        classname = testcase.get("classname", "")
        name = testcase.get("name", "")
        time_val = float(testcase.get("time", 0))
        # Normalize test id (pytest uses :: for nodeid, [ for params)
        test_id = f"{classname}::{name}" if classname else name

        status = "passed"
        message = ""
        traceback = ""

        failure = testcase.find("failure")
        error = testcase.find("error")
        skipped = testcase.find("skipped")

        if failure is not None:
            status = "failed"
            message = failure.get("message", "")
            traceback = (failure.text or "").strip()
        elif error is not None:
            status = "error"
            message = error.get("message", "")
            traceback = (error.text or "").strip()
        elif skipped is not None:
            status = "skipped"
            message = skipped.get("message", "")

        results[test_id] = {
            "status": status,
            "time": time_val,
            "message": message,
            "traceback": traceback,
        }
    return results


def collect_results(results_dir: Path) -> dict[str, dict[str, dict]]:
    """
    Collect results from all backend XML files.
    Returns: {backend: {test_id: result}}
    """
    backend_files = {
        "local": "local.xml",
        "kubernetes": "kubernetes.xml",
        "argo": "argo.xml",
    }
    all_results = {}
    for backend, filename in backend_files.items():
        path = results_dir / filename
        all_results[backend] = parse_junitxml(path)
    return all_results


def build_matrix(all_results: dict[str, dict[str, dict]]) -> tuple[set[str], list[str]]:
    """Build the set of all test IDs and ordered backend list."""
    all_tests = set()
    for backend_results in all_results.values():
        all_tests.update(backend_results.keys())
    backends = ["local", "kubernetes", "argo"]
    return all_tests, backends


def generate_html(
    all_results: dict[str, dict[str, dict]],
    output_path: Path,
) -> None:
    """Generate HTML report with test x backend matrix."""
    all_tests, backends = build_matrix(all_results)
    sorted_tests = sorted(all_tests)

    tracebacks: list[str] = []
    rows = []
    for test_id in sorted_tests:
        cells = []
        for backend in backends:
            result = all_results.get(backend, {}).get(test_id)
            if result is None:
                cell = '<td class="not-run" title="Not run on this backend">—</td>'
            else:
                status = result["status"]
                time_val = result["time"]
                if status == "passed":
                    cell = f'<td class="passed">✓ <span class="duration">({time_val:.2f}s)</span></td>'
                elif status == "failed" or status == "error":
                    idx = len(tracebacks)
                    tracebacks.append(result["traceback"] or result["message"] or "")
                    short_msg = html.escape((result["message"] or "Failed")[:80])
                    cell = f'<td class="failed" title="{short_msg}"><a href="#" onclick="showTraceback({idx}); return false;">✗</a> <span class="duration">({time_val:.2f}s)</span></td>'
                else:
                    cell = f'<td class="skipped">↷ <span class="duration">({time_val:.2f}s)</span></td>'
            cells.append(cell)
        rows.append(f"<tr><td class=\"test-name\">{html.escape(test_id)}</td>{''.join(cells)}</tr>")

    table_body = "\n".join(rows)
    header_cells = "".join(f"<th>{b}</th>" for b in backends)
    tb_json = json.dumps(tracebacks)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metaflow Test Results — Cross-Backend Report</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; margin: 2rem; background: #1e1e1e; color: #d4d4d4; }}
        h1 {{ color: #fff; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 900px; }}
        th, td {{ border: 1px solid #444; padding: 0.5rem 1rem; text-align: left; }}
        th {{ background: #2d2d2d; color: #fff; }}
        .test-name {{ font-family: monospace; font-size: 0.9em; }}
        .passed {{ color: #4ec9b0; }}
        .failed {{ color: #f48771; }}
        .skipped {{ color: #dcdcaa; }}
        .not-run {{ color: #6e7681; }}
        .duration {{ font-size: 0.8em; color: #6e7681; }}
        #traceback-modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; }}
        #traceback-content {{ background: #252526; padding: 1.5rem; max-width: 80%; max-height: 80%; overflow: auto; white-space: pre-wrap; font-family: monospace; font-size: 0.85em; border: 1px solid #444; }}
        .close-btn {{ margin-top: 1rem; padding: 0.5rem 1rem; cursor: pointer; background: #0e639c; color: #fff; border: none; }}
    </style>
</head>
<body>
    <h1>Metaflow Test Results — Cross-Backend Report</h1>
    <p>✓ = passed, ✗ = failed, ↷ = skipped, — = not run</p>
    <table>
        <thead>
            <tr><th>Test</th>{header_cells}</tr>
        </thead>
        <tbody>
            {table_body}
        </tbody>
    </table>
    <div id="traceback-modal">
        <div>
            <pre id="traceback-content"></pre>
            <button class="close-btn" onclick="document.getElementById('traceback-modal').style.display='none'">Close</button>
        </div>
    </div>
    <script>
        const TRACEBACKS = {tb_json};
        function showTraceback(idx) {{
            document.getElementById('traceback-content').textContent = TRACEBACKS[idx] || '';
            document.getElementById('traceback-modal').style.display = 'flex';
        }}
    </script>
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge pytest JUnit XML results into HTML report")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("test-results"),
        help="Directory containing local.xml, kubernetes.xml, argo.xml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output HTML path (default: results-dir/report.html)",
    )
    args = parser.parse_args()
    output = args.output or args.results_dir / "report.html"
    args.results_dir.mkdir(parents=True, exist_ok=True)

    all_results = collect_results(args.results_dir)
    generate_html(all_results, output)
    print(f"Report written to {output}")


if __name__ == "__main__":
    main()
