# Verified local test run — 2026-09-21

Test execution date: **2026-09-21**. JUnit reports, screenshots, server logs and Playwright traces retain their original runtime timestamps.

| Suite | Passed / collected | Failed / errors / skipped | Statement coverage |
|---|---:|---:|---:|
| BoneWave-AI Python | 41/41 | 0 / 0 / 0 | 94.55% (590/624) |
| Prototype Python | 6/6 | 0 / 0 / 0 | 55.85% (296/530) |
| Chromium browser E2E | 4/4 | 0 / 0 / 0 | Not measured |
| Total | 51/51 | 0 / 0 / 0 | Separate scopes |

`app/nanovna/device.py`: 85/85 executable statements covered (100%), up from 33/85 (38.82%). The backend total increased from 85.10% to 94.55%. These percentages describe statement execution with mocked serial transport, not branch coverage or hardware validation.

## Evidence

- Backend: [coverage](BoneWave-AI/coverage.txt), [JUnit](BoneWave-AI/junit.xml), [summary](BoneWave-AI/summary.json), [environment](BoneWave-AI/environment.txt)
- Prototype: [coverage](Prototype/coverage.txt), [JUnit](Prototype/junit.xml), [summary](Prototype/summary.json), [environment](Prototype/environment.txt)
- Browser: [JUnit](e2e/junit.xml), [completed scan screenshot](e2e/completed-scan.png), [trace ZIP](e2e/test_mock_scan_completes_and_disconnects.zip), [mock server log](e2e/test_mock_scan_completes_and_disconnects-server.log)
- [SHA-256 hashes of tested backend, browser assets and test source](source-sha256.json)

## Recorded real measurement replay

The repository dataset declares `real_measurements`, with 100 files per group (Air/Normal/Crack). The reference loader uses 297 unique files after excluding 3 exact duplicates. Each Normal and Crack group has only one physical specimen measured at multiple angles; there are no independent test specimens.

All three recorded-input browser cases passed. A test-only device adapter supplies complex S11/S21 samples from the original S2P files to the acquisition pipeline. The browser uses the visible REPLAY port and ordinary Scan button, with real HTTP/WebSocket traffic and no forced classification. Each case verifies the expected class, 3 sweeps, saved S2P output, source file/hash, UI state and disconnection.

| Input | Expected result | Evidence |
|---|---|---|
| `air/Air_002.s2p` | AIR | [screenshot](e2e/real-air.png), [source/hash](e2e/real-air-source.json) |
| `normal/Normal_002.s2p` | NOT_FRACTURED | [screenshot](e2e/real-not_fractured.png), [source/hash](e2e/real-not_fractured-source.json) |
| `crack/Crack_002.s2p` | FRACTURED | [screenshot](e2e/real-fractured.png), [source/hash](e2e/real-fractured-source.json) |

These files are also in the reference bank: the results establish pipeline consistency, not unseen-specimen performance, clinical accuracy or live hardware operation. Original source data files were not edited.

![Recorded normal trace through the dashboard](e2e/real-not_fractured.png)


The mock scan rendered UNCERTAIN, matching the backend response. This is a software workflow test, not an accuracy evaluation. The test verifies 3 completed WebSocket sweeps, 3 persisted S2P files, UI control states, result rendering, disconnection, and absence of unhandled JavaScript page errors. The trace includes ordinary mouse clicks; no hidden classification shortcuts were used.

## Runtime and reproduction

Python 3.12.4 on macOS arm64, pytest 9.0.2, coverage 7.16.1, Playwright 1.63.0, Chromium 153.0.8010.12, Uvicorn 0.34.0 and websockets 14.1. Python tests used the existing project virtualenv plus temporary dependencies under `/tmp/bonewave-audit-deps`; E2E additionally used `/tmp/bonewave-browser-deps` and browser binaries under `/tmp/bonewave-playwright`. This was not a clean install of the component requirements. One dependency deprecation warning was emitted by Starlette/AnyIO in the backend tests. No product defect is inferred from that warning.

Run the commands in [the test plan](../../TEST_PLAN.md) and [main test README](../../README.md). Backend coverage scopes are `app` and `src,scripts` respectively. Browser execution is a separate job and is not included in Python coverage. The E2E fixture uses a disposable application copy and its own localhost server; it does not modify project measurement data.

During setup, sandbox restrictions initially blocked browser download and localhost binding; the final E2E run used approved execution outside those restrictions. An early fake-transport test helper was corrected before this final run. These setup/test-authoring failures are not counted as product bugs.

This is local evidence from an uncommitted working tree based on the revision recorded in each summary. It is not a claim that GitHub Actions has already run. JUnit timestamps are the original execution timestamps. The Python suite results were retained from the preceding run because only E2E code changed; all four E2E cases were rerun for this update.
