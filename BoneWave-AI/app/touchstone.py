"""Strict Touchstone 1.x parsing and S21 extraction."""
from dataclasses import dataclass
from pathlib import Path
import io
import numpy as np

TARGET_FREQUENCIES = np.linspace(1.5e9, 3.0e9, 404)

class TouchstoneError(ValueError):
    pass

@dataclass
class Trace:
    frequency_hz: np.ndarray
    s11: np.ndarray
    s21: np.ndarray

    @property
    def s21_db(self):
        return 20 * np.log10(np.maximum(np.abs(self.s21), 1e-15))

    @property
    def s21_phase(self):
        return np.unwrap(np.angle(self.s21))

def _pair(a, b, fmt):
    if fmt == "RI": return complex(a, b)
    if fmt == "MA": return a * np.exp(1j * np.deg2rad(b))
    if fmt == "DB": return 10 ** (a / 20) * np.exp(1j * np.deg2rad(b))
    raise TouchstoneError(f"Unsupported Touchstone format: {fmt}")

def parse_touchstone(source):
    try:
        text = source.read_text(encoding="utf-8", errors="strict") if isinstance(source, Path) else (source.decode() if isinstance(source, bytes) else str(source))
    except (OSError, UnicodeError) as exc:
        raise TouchstoneError(f"Could not read Touchstone file: {exc}") from exc
    option = None; tokens = []
    for raw in io.StringIO(text):
        line = raw.split("!", 1)[0].strip()
        if not line: continue
        if line.startswith("#"):
            parts = line[1:].upper().split()
            if len(parts) < 3 or parts[1] != "S": raise TouchstoneError("Expected an S-parameter option line")
            option = parts
        elif not line.startswith("["):
            tokens.extend(line.split())
    if option is None: raise TouchstoneError("Missing Touchstone option line")
    scale = {"HZ":1, "KHZ":1e3, "MHZ":1e6, "GHZ":1e9}.get(option[0])
    fmt = next((x for x in option if x in {"RI","MA","DB"}), None)
    if scale is None or fmt is None: raise TouchstoneError("Unsupported frequency unit or data format")
    try: values = np.asarray([float(x) for x in tokens], dtype=float)
    except ValueError as exc: raise TouchstoneError("Touchstone contains non-numeric data") from exc
    if len(values) < 9 or len(values) % 9: raise TouchstoneError("Each .s2p row must contain 9 numeric values")
    rows = values.reshape(-1, 9); freq = rows[:,0] * scale
    if not np.all(np.isfinite(rows)) or np.any(np.diff(freq) <= 0): raise TouchstoneError("Frequencies must be finite and strictly increasing")
    # Touchstone order is S11, S21, S12, S22.
    s11 = np.array([_pair(r[1], r[2], fmt) for r in rows])
    s21 = np.array([_pair(r[3], r[4], fmt) for r in rows])
    return Trace(freq, s11, s21)

def interpolate_trace(trace, axis=TARGET_FREQUENCIES):
    axis = np.asarray(axis, dtype=float)
    # NanoVNA integer step rounding can miss an endpoint by a few dozen hertz.
    tolerance = max(100.0, (axis[-1] - axis[0]) / max(len(axis) - 1, 1) * 1e-3)
    if trace.frequency_hz[0] > axis[0] + tolerance or trace.frequency_hz[-1] < axis[-1] - tolerance:
        raise TouchstoneError("Measurement does not cover the required 1.5-3.0 GHz range")
    real = np.interp(axis, trace.frequency_hz, trace.s21.real)
    imag = np.interp(axis, trace.frequency_hz, trace.s21.imag)
    return Trace(axis.copy(), np.zeros(len(axis), complex), real + 1j * imag)

def load_standard_trace(source):
    return interpolate_trace(parse_touchstone(source))

def write_touchstone(path, frequency, s11, s21):
    lines = ["# HZ S RI R 50", "! BoneWave AI live acquisition"]
    for f,a,b in zip(frequency,s11,s21): lines.append(f"{f:.6f} {a.real:.12g} {a.imag:.12g} {b.real:.12g} {b.imag:.12g} 0 0 0 0")
    Path(path).write_text("\n".join(lines)+"\n", encoding="utf-8")
