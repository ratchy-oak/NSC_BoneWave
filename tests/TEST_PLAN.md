# BoneWave test plan and requirement traceability

Scope: software behavior of the research prototype. These acceptance requirements are derived from the current README and implementation; they are not medical or regulatory requirements.

| ID | Requirement / risk | Test case and expected result | Level |
|---|---|---|---|
| R01 | A disconnected dashboard must prevent scans | E01: Scan disabled before connection and after disconnection | Chromium E2E |
| R02 | A normal sample scan ends after 3 completed sweeps | E01: click MOCK connect and ordinary Scan, observe 3 WebSocket results, rendered final class matching backend, 3 saved S2P files, Scan re-enabled | Chromium E2E |
| R03 | Reference setup dialog is usable | E01: open setup, see 0 of 3, close dialog | Chromium E2E |
| R04 | Drivers return correct complex channels and frequency axis | D01: shell response parsing; D02: V2 fragmented FIFO payload and normalized S11/S21 values | Driver unit |
| R05 | Transport failures are visible and connection failures release resources | D03: unopened acquisition rejected, busy port, malformed response, wrong V2 variant, short read timeout; check DeviceError and cleanup | Driver unit |
| R06 | Device discovery selects the correct adapter | D04: known USB IDs select V2, other/unknown ports select shell, enumeration failure returns empty ports | Driver unit |
| R07 | Touchstone input supports RI/MA/DB and rejects malformed data | Existing parser tests, finite 404-point interpolated trace | Unit |
| R08 | Interrupted acquisition stops and releases connection | Existing `test_release_after_errors`, WebSocket stop/cancellation tests | Integration with mock |
| R09 | Repeated measurements of one synthetic sample cannot cross train/test split | Existing `test_group_split_and_all_models_train`: sample ID sets are disjoint | Prototype integration |
| R10 | Pipeline produces required nonempty artifacts | Existing `test_complete_pipeline_creates_required_outputs` | Prototype integration |

Test sources: [E01](e2e/test_dashboard.py), [D01–D04](../BoneWave-AI/tests/test_device.py), [parser](../BoneWave-AI/tests/test_touchstone.py), [live integration](../BoneWave-AI/tests/test_live.py), [Prototype](../Prototype/tests/).

## Setup and execution

Use Python 3.12. Component tests run through `python tests/run_tests.py` in the appropriate installed environment (see [README](README.md)). They execute on temporary copies. E2E independently starts the real FastAPI server in a temporary copy, uses the existing mock port, and loads real HTML/CSS/JavaScript in Chromium. HTTP and WebSocket responses are not stubbed. The default 3-sweep configuration is preserved; no hidden scan shortcut is invoked.

```sh
python -m pip install -r tests/e2e/requirements.txt
python -m playwright install chromium
python -m pytest tests/e2e -q --junitxml=test-results/latest/e2e/junit.xml
```

On Linux CI use `python -m playwright install --with-deps chromium`. The fixture starts/stops its own server, waits on server readiness and browser assertions, and saves screenshots, trace ZIPs, server logs and JUnit XML under `test-results/latest/e2e/`. Run that job separately from Python coverage: this E2E run does not measure JavaScript coverage or add server subprocess execution to Python coverage.

Entry criteria: dependencies/browser installed, reference files available, localhost binding allowed. Exit criteria: all selected tests pass without skips, E01 has no unhandled page errors, reports exist; investigate failures before recording a product defect. CI uploads results even on test failure. Test counts and coverage are observed results, not hardcoded acceptance targets.

## Remaining hardware and UI scope

Fake serial transport tests check command handling and error paths; they do not validate USB timing, actual firmware compatibility, calibration, measurement fidelity, cable/fixture effects, or real disconnection recovery. These require a NanoVNA hardware session with model, firmware, settings, raw traces and outcomes recorded. E01 covers one desktop Chromium workflow; full reference capture, mobile layout, other browsers, Streamlit UI and clinical performance are outside this test's scope.

Tool references: [Playwright Python library](https://playwright.dev/python/docs/library), [retrying assertions](https://playwright.dev/python/docs/test-assertions).
