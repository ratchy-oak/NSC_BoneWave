# BoneWave test audit — 2026-09-20

Test execution date: **2026-09-20**. JUnit reports retain the original execution timestamps.

Tests ran against temporary copies of the working tree. No physical hardware was tested.

| Component | Passed | Failed | Python statement coverage | Scope |
|---|---:|---:|---:|---|
| BoneWave-AI | 27 | 0 | 85.10% (531/624) | app/ Python files; excludes browser JavaScript/CSS |
| Prototype | 6 | 0 | 55.85% (296/530) | src/ and scripts/; excludes Streamlit app.py |

Coverage is statement coverage, not branch or requirement coverage. No historical bug count or severity register was located. Passing tests do not establish absence of defects. Prototype uses simulated data; metrics do not establish clinical accuracy. Live acquisition tests use mocks.

Runtime: existing Python 3.12 environment with pytest 9.0.2. Temporary additional dependencies: fastapi 0.115.6, pyserial 3.5, httpx 0.28.1, coverage 7.16.1 and their dependencies. This was not a clean install of both pinned requirements files. Initial BoneWave-AI collection was blocked by missing FastAPI; the final run completed after temporary dependencies were added. BoneWave-AI emitted one Starlette/AnyIO deprecation warning.

Commands (run separately in each component directory):

```sh
python -m coverage run --source=app -m pytest -q --junitxml=../BoneWave-AI-junit.xml
python -m coverage report --precision=2
# Prototype:
python -m coverage run --source=src,scripts -m pytest -q --junitxml=../Prototype-junit.xml
python -m coverage report --precision=2
```

The environment used PYTHONPATH for temporary dependencies and a writable MPLCONFIGDIR. JUnit XML and detailed per-module coverage reports are alongside this file.
