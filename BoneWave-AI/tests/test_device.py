"""Driver contracts with a fake serial transport; no USB device is required."""
import asyncio
import struct
from types import SimpleNamespace

import numpy as np
import pytest
import serial
from serial.tools import list_ports

from app.nanovna.device import (
    DeviceError, MockNanoVNA, NanoVNAV2, SerialNanoVNA,
    available_ports, device_for_port,
)
from app.nanovna.protocol import ProtocolError


class FakeSerial:
    def __init__(self, replies=(), binary=b"", chunk_size=7):
        self.replies = iter(replies)
        self.binary = bytearray(binary)
        self.chunk_size = chunk_size
        self.writes = []
        self.closed = False

    def reset_input_buffer(self):
        pass

    def write(self, payload):
        self.writes.append(payload)

    def flush(self):
        pass

    def read_until(self, prompt):
        assert prompt == b"ch>"
        try:
            return next(self.replies)
        except StopIteration:
            raise OSError("serial response unavailable") from None

    def read(self, size):
        count = min(size, self.chunk_size, len(self.binary))
        result = bytes(self.binary[:count])
        del self.binary[:count]
        return result

    def close(self):
        self.closed = True


@pytest.mark.parametrize("driver", [MockNanoVNA, SerialNanoVNA, NanoVNAV2])
def test_disconnected_acquisition_is_rejected(driver):
    device = driver() if driver is MockNanoVNA else driver("TEST")
    with pytest.raises(DeviceError, match="not connected"):
        asyncio.run(device.acquire_segment(100, 200, 2))


def test_shell_connect_acquire_disconnect(monkeypatch):
    transport = FakeSerial([b"NanoVNA\nch>", b"1.0\nch>", b"ch>",
                            b"0.1 0.2\n0.3 0.4\nch>", b"0.5 0.6\n0.7 0.8\nch>"])
    monkeypatch.setattr(serial, "Serial", lambda *a, **k: transport)

    async def scenario():
        device = SerialNanoVNA("TEST")
        assert "1.0" in (await device.connect())["firmware"]
        frequency, s11, s21 = await device.acquire_segment(100, 200, 2)
        np.testing.assert_array_equal(frequency, [100, 200])
        np.testing.assert_allclose(s11, [.1+.2j, .3+.4j])
        np.testing.assert_allclose(s21, [.5+.6j, .7+.8j])
        assert transport.writes == [b"info\r", b"version\r", b"sweep 100 200 2\r", b"data 0\r", b"data 1\r"]
        await device.disconnect()
        await device.disconnect()
        assert transport.closed and not device.connected and device.serial is None
    asyncio.run(scenario())


@pytest.mark.parametrize("driver", [SerialNanoVNA, NanoVNAV2])
def test_connect_failure_cleans_up_transport(monkeypatch, driver):
    # Empty shell replies or wrong V2 variant fail after the port was opened.
    transport = FakeSerial(binary=bytes([9, 1, 1, 1, 0]))
    monkeypatch.setattr(serial, "Serial", lambda *a, **k: transport)
    device = driver("TEST")
    with pytest.raises(DeviceError, match="Unable to connect"):
        asyncio.run(device.connect())
    assert transport.closed and device.serial is None and not device.connected


@pytest.mark.parametrize("driver", [SerialNanoVNA, NanoVNAV2])
def test_port_open_failure_is_reported(monkeypatch, driver):
    def denied(*a, **k):
        raise OSError("port busy")
    monkeypatch.setattr(serial, "Serial", denied)
    device = driver("TEST")
    with pytest.raises(DeviceError, match="port busy"):
        asyncio.run(device.connect())
    assert not device.connected and device.serial is None


def test_shell_malformed_data_is_reported():
    device = SerialNanoVNA("TEST")
    device.connected = True
    device.serial = FakeSerial([b"ch>", b"invalid\nch>"])
    with pytest.raises(DeviceError, match="Expected 2 values"):
        asyncio.run(device.acquire_segment(100, 200, 2))


def test_v2_connect_fragmented_fifo_and_disconnect(monkeypatch):
    payload = b"".join(struct.pack("<iiiiiihxxxxxx", 100, 0, 10, 0, 20, 0, i) for i in range(2))
    transport = FakeSerial(binary=bytes([2, 1, 3, 4, 5]) + payload, chunk_size=3)
    monkeypatch.setattr(serial, "Serial", lambda *a, **k: transport)

    async def scenario():
        device = NanoVNAV2("TEST")
        info = await device.connect()
        assert info["variant"] == 2 and info["firmware"] == "4.5"
        frequency, s11, s21 = await device.acquire_segment(100, 200, 2)
        np.testing.assert_array_equal(frequency, [100, 200])
        np.testing.assert_allclose(s11, [.1, .1])
        np.testing.assert_allclose(s21, [.2, .2])
        assert transport.writes[-1] == device.protocol.read_fifo(2)
        await device.disconnect()
        assert transport.closed and device.serial is None and not device.connected
    asyncio.run(scenario())


def test_v2_short_read_times_out(monkeypatch):
    import app.nanovna.device as module
    device = NanoVNAV2("TEST", timeout=1)
    device.serial = FakeSerial(binary=b"x")
    ticks = iter([0, 0, 2])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(ticks))
    with pytest.raises(ProtocolError, match="1 of 2 bytes"):
        device._read_exact(2)


def test_v2_invalid_sweep_is_wrapped():
    device = NanoVNAV2("TEST")
    device.serial = FakeSerial()
    device.connected = True
    with pytest.raises(DeviceError, match="at least two points"):
        asyncio.run(device.acquire_segment(100, 200, 1))


def test_port_discovery_and_driver_selection(monkeypatch):
    ports = [SimpleNamespace(device="COM4", description="V2", vid=0x04B4, pid=0x0008),
             SimpleNamespace(device="COM5", description="Shell", vid=1, pid=2)]
    monkeypatch.setattr(list_ports, "comports", lambda: ports)
    assert [p["protocol"] for p in available_ports()] == ["nanovna_v2", "shell"]
    assert isinstance(device_for_port("com4"), NanoVNAV2)
    assert isinstance(device_for_port("COM5"), SerialNanoVNA)
    assert isinstance(device_for_port("UNKNOWN"), SerialNanoVNA)


def test_port_discovery_failure_falls_back(monkeypatch):
    def unavailable():
        raise OSError("enumeration failed")
    monkeypatch.setattr(list_ports, "comports", unavailable)
    assert available_ports() == []
    assert isinstance(device_for_port("TEST"), SerialNanoVNA)
