"""Run real component tests in disposable copies and export auditable results."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCOPES = {"BoneWave-AI": "app", "Prototype": "src,scripts"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component", choices=SCOPES)
    parser.add_argument("--output", type=Path, default=ROOT / "test-results" / "latest")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    failed = False
    for name in ([args.component] if args.component else SCOPES):
        dest = output / name
        dest.mkdir(parents=True, exist_ok=True)
        # Clear previous reports so an interrupted run cannot expose stale results.
        for filename in ("junit.xml", "coverage.json", "coverage.txt", "summary.json", "environment.txt"):
            (dest / filename).unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix="bonewave-tests-") as temporary:
            work = Path(temporary) / name
            shutil.copytree(ROOT / name, work, ignore=shutil.ignore_patterns(
                ".venv", "__pycache__", ".pytest_cache", ".coverage*", "screenshots", "*.zip"))
            env = dict(os.environ, MPLCONFIGDIR=str(Path(temporary) / "matplotlib"),
                       COVERAGE_FILE=str(Path(temporary) / ".coverage"))

            def run(*command):
                return subprocess.run([sys.executable, *command], cwd=work, env=env,
                                      text=True, capture_output=True)

            result = run("-m", "coverage", "run", "--source=" + SCOPES[name],
                         "-m", "pytest", "-q", "--junitxml=" + str(dest / "junit.xml"))
            (dest / "pytest.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
            print(name + ":\n" + result.stdout + result.stderr, flush=True)
            report = run("-m", "coverage", "report", "--precision=2")
            (dest / "coverage.txt").write_text(report.stdout + report.stderr, encoding="utf-8")
            export = run("-m", "coverage", "json", "-o", str(dest / "coverage.json"))
            (dest / "environment.txt").write_text(run("-m", "pip", "freeze").stdout, encoding="utf-8")
            counts = dict(tests=0, failures=0, errors=0, skipped=0)
            if (dest / "junit.xml").exists():
                for suite in ET.parse(dest / "junit.xml").iter("testsuite"):
                    for key in counts:
                        counts[key] += int(suite.get(key, 0))
            totals = (json.loads((dest / "coverage.json").read_text())["totals"]
                      if (dest / "coverage.json").exists() else None)
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                      capture_output=True, text=True)
            status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                    capture_output=True, text=True)
            summary = dict(component=name, source_scope=SCOPES[name], python=platform.python_version(),
                           commit=revision.stdout.strip(), working_tree_dirty=bool(status.stdout.strip()),
                           pytest_exit_code=result.returncode, counts=counts, coverage=totals)
            (dest / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(report.stdout, flush=True)
            failed |= bool(result.returncode or report.returncode or export.returncode or not counts["tests"])
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
