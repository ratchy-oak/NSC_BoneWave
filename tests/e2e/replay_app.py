"""Test-only server adapter: replay a recorded S2P file through acquisition."""
import hashlib
import os
from pathlib import Path

import numpy as np

import app.main as main
from app.nanovna.device import DeviceError, MockNanoVNA
from app.touchstone import load_standard_trace

SOURCE = Path(os.environ["BONEWAVE_REPLAY_FILE"])


class RecordedNanoVNA(MockNanoVNA):
    port = "REPLAY"

    def __init__(self):
        super().__init__()
        self.trace = load_standard_trace(SOURCE)
        self.info = {"device": "Recorded real dataset replay", "source_file": SOURCE.name,
                     "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                     "data_source": "recorded_real_measurement_replay", "live_hardware": False}

    async def acquire_segment(self, start, stop, points):
        if not self.connected:
            raise DeviceError("Device is not connected")
        frequency = np.linspace(start, stop, points)
        return (frequency, np.interp(frequency, self.trace.frequency_hz, self.trace.s11),
                np.interp(frequency, self.trace.frequency_hz, self.trace.s21))


def replay_device(port, *args):
    if port != "REPLAY":
        raise DeviceError("Replay test server only accepts REPLAY")
    return RecordedNanoVNA()


main.available_ports = lambda: [{"port": "REPLAY", "description": "Recorded real dataset replay"}]
main.device_for_port = replay_device
app = main.app
