# BoneWave AI

Local research prototype for matching live NanoVNA S21 measurements as
**AIR**, **NOT FRACTURED**, or **FRACTURED**. A same-device live setup is used
when available; the real, multi-angle dataset remains the fallback reference
bank.

> Research prototype — not for medical diagnosis. The current Normal and Crack
> references contain multiple angles from one physical specimen per class. They
> do not demonstrate generalization or independent medical accuracy.

## Windows setup and run

From PowerShell or Command Prompt in this folder:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

For hardware, close NanoVNA Saver and every serial terminal first, select the
NanoVNA COM port, and click **Connect**. Only one application can own the port.
Click **Scan new sample** once for each sample or angle. Each click acquires three
completed sweeps, stabilizes the result, stores the raw output, and stops.

For the most reliable live matching, click **Setup references** at the top and
capture all three conditions with the current NanoVNA, cables, fixture, and
frequency settings:

1. Empty fixture (**Air**)
2. Known normal specimen
3. Known cracked specimen

Each **Scan & capture** button performs one automatic three-sweep scan and saves
that condition. When the setup shows **Ready**, subsequent sample scans use the
same-device three-class bank. Resetting live setup does not delete `data/real`.
For this live bank, the stabilized class with the highest displayed similarity
is selected directly as the result, even when the top two values are close.

Use the built-in `MOCK` port for a hardware-free acquisition check.

## Real reference data

The application loads `.s2p` files automatically from:

```text
data/real/air/
data/real/normal/
data/real/crack/
```

- Air, Normal, and Crack are three prediction classes. AIR represents an empty
  fixture or no specimen in the sensing path.
- Exact duplicate files are ignored automatically.
- Every file must cover 1.5–3.0 GHz and be readable as Touchstone 1.x RI, MA, or
  DB data.
- Dataset provenance and limitations are recorded in
  `data/real/dataset_info.json`.

The predictor compares each live sweep with the five closest reference traces
per class and reports three class probabilities. Distant measurements or class
ties return `UNCERTAIN` instead of forcing a class.

Live setup files are stored separately under `data/live_references/`. Once Air,
Normal, and Crack all contain at least three completed sweeps, this bank takes
priority over the offline real dataset for live prediction.

## Live data and diagnostics

Device settings are in `config/device.json`. Completed live scans are saved
under `data/live_sessions/<session_id>/` as `.s2p` and `.json` files. Repeated
serial failures stop acquisition and release the port.

NanoVNA V2 binary register/FIFO communication and common NanoVNA shell commands
are isolated under `app/nanovna/`. To inspect another firmware safely:

```bat
python scripts\nanovna_diagnostic.py --port COM4
```

Diagnostic responses are stored under `data/live_sessions/diagnostic_*`.

## Tests

```bat
pytest -q
```

## Main files

- `app/main.py`: FastAPI routes, WebSocket, and lifecycle shutdown
- `app/predictor.py`: live and real three-class reference-bank matching
- `app/touchstone.py`: strict Touchstone parsing, interpolation, and writing
- `app/live_manager.py`: per-sample acquisition, stabilization, and persistence
- `app/nanovna/`: protocols, devices, and segmented acquisition
- `app/static/`: live-only user interface
- `scripts/`: NanoVNA diagnostics and smoke tests
- `tests/`: parser, API, reference bank, WebSocket, and acquisition coverage

## Scientific limitation

Repeated angles from one specimen are not independent specimens. Before making
any accuracy claim, collect multiple independent Normal and Crack specimens,
split evaluation by specimen ID, and use a locked independent test cohort.
