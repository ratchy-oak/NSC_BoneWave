import asyncio
import json
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .nanovna.acquisition import acquire_sweep
from .touchstone import Trace, interpolate_trace, write_touchstone

WARNING = "Research prototype — Not for medical diagnosis"


class Stabilizer:
    def __init__(self, size=5):
        self.items = deque(maxlen=size)

    def reset(self):
        self.items.clear()

    def add(self, result):
        self.items.append(result)
        labels = ("AIR", "NOT_FRACTURED", "FRACTURED")

        def probabilities(item):
            if "class_probabilities" in item:
                return item["class_probabilities"]
            fracture = float(item["fracture_probability"])
            return {
                "AIR": 0.0,
                "NOT_FRACTURED": 1.0 - fracture,
                "FRACTURED": fracture,
            }

        stabilized_probabilities = {
            label: float(
                np.median([probabilities(item)[label] for item in self.items])
            )
            for label in labels
        }
        result = dict(result)
        result["raw_prediction"] = result["prediction"]
        result["raw_fracture_probability"] = result["fracture_probability"]
        result["completed_sweeps"] = len(self.items)
        result["class_probabilities"] = stabilized_probabilities
        result["fracture_probability"] = stabilized_probabilities["FRACTURED"]
        ranked = sorted(
            stabilized_probabilities.items(), key=lambda item: item[1], reverse=True
        )
        winner, winner_probability = ranked[0]
        margin = winner_probability - ranked[1][1]
        live_winner_mode = (
            result.get("model_mode") == "live_three_class_reference_bank"
        )
        if live_winner_mode:
            similarity_fields = {
                "AIR": "similarity_air",
                "NOT_FRACTURED": "similarity_normal",
                "FRACTURED": "similarity_crack",
            }
            stabilized_similarities = {
                label: float(
                    np.median(
                        [
                            item.get(field, probabilities(item)[label])
                            for item in self.items
                        ]
                    )
                )
                for label, field in similarity_fields.items()
            }
            for label, field in similarity_fields.items():
                result[field] = stabilized_similarities[label]
            ranked = sorted(
                stabilized_similarities.items(),
                key=lambda item: item[1],
                reverse=True,
            )
            winner, winner_probability = ranked[0]
            margin = winner_probability - ranked[1][1]
        uncertain_votes = sum(
            item["prediction"] == "UNCERTAIN"
            or item.get("out_of_distribution", False)
            for item in self.items
        )
        if len(self.items) < 3:
            result["prediction"] = "PENDING"
        elif live_winner_mode:
            result["prediction"] = winner
        elif (
            uncertain_votes >= len(self.items) // 2 + 1
            or winner_probability < 0.55
            or margin < 0.15
        ):
            result["prediction"] = "UNCERTAIN"
        else:
            result["prediction"] = winner
        result["predicted_class"] = result["prediction"]
        result["confidence"] = winner_probability
        result["winning_margin"] = margin
        return result


class LiveManager:
    def __init__(self, predictor, cfg, root):
        self.predictor = predictor
        self.cfg = cfg
        self.root = Path(root)
        self.device = None
        self.task = None
        self.clients = set()
        self.stabilizer = Stabilizer()
        self.recent_traces = deque(maxlen=cfg.get("sweeps_per_sample", 5))
        self.state = "disconnected"
        self.last_error = None
        self.session_id = None
        self.run_interval_seconds = cfg["measurement_interval_seconds"]
        self.run_average_count = cfg["average_count"]

    async def connect(self, device):
        if self.device:
            await self.disconnect()
        info = await device.connect()
        self.device = device
        self.state = "connected"
        self.last_error = None
        return info

    async def disconnect(self):
        await self.stop()
        if self.device:
            await self.device.disconnect()
        self.device = None
        self.state = "disconnected"

    async def start(self, measurement_interval_seconds=None, average_count=None):
        if not self.device or not self.device.connected:
            raise RuntimeError("Connect a NanoVNA first")
        if self.task and not self.task.done():
            raise RuntimeError("Live acquisition is already running")
        self.stabilizer.reset()
        self.recent_traces.clear()
        self.run_interval_seconds = (
            self.cfg["measurement_interval_seconds"]
            if measurement_interval_seconds is None
            else max(0.0, float(measurement_interval_seconds))
        )
        self.run_average_count = (
            self.cfg["average_count"]
            if average_count is None
            else max(1, int(average_count))
        )
        self.session_id = (
            datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        )
        self.state = "measuring"
        self.task = asyncio.create_task(self._loop())
        return self.session_id

    async def stop(self):
        if self.task and not self.task.done():
            self.task.cancel()
        if self.task:
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        if self.device and self.device.connected:
            self.state = "connected"

    async def broadcast(self, message):
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)

    def status(self):
        return {
            "state": self.state,
            "connected": bool(self.device and self.device.connected),
            "running": bool(self.task and not self.task.done()),
            "session_id": self.session_id,
            "last_error": self.last_error,
            "device_info": getattr(self.device, "info", None),
        }

    def capture_reference(self, kind):
        if kind not in {"air", "normal", "crack"}:
            raise ValueError("Reference kind must be air, normal, or crack")
        traces = list(self.recent_traces)
        if len(traces) < 3:
            raise RuntimeError("Complete a sample scan before capturing this reference")
        folder = self.root / "data" / "live_references" / kind
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.glob("*.s2p"):
            path.unlink()
        for index, trace in enumerate(traces, start=1):
            write_touchstone(
                folder / f"sweep_{index:03d}.s2p",
                trace.frequency_hz,
                trace.s11,
                trace.s21,
            )
        metadata = {
            "kind": kind,
            "role": "live_target_reference",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "sweeps": len(traces),
            "synthetic": False,
            "warning": WARNING,
        }
        metadata_path = self.root / "data" / "live_references" / f"{kind}.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        self.predictor.set_live_reference_bank(kind, traces)
        self.recent_traces.clear()
        self.stabilizer.reset()
        return metadata

    def reset_references(self):
        root = self.root / "data" / "live_references"
        removed = []
        for kind in ("air", "normal", "crack"):
            folder = root / kind
            if folder.exists():
                for path in folder.glob("*.s2p"):
                    path.unlink()
                    removed.append(str(path.relative_to(root)))
                folder.rmdir()
            metadata = root / f"{kind}.json"
            if metadata.exists():
                metadata.unlink()
                removed.append(metadata.name)
        self.predictor.clear_live_references()
        self.recent_traces.clear()
        self.stabilizer.reset()
        return {
            "status": "reset",
            "removed": removed,
            "references": self.predictor.reference_status(),
        }

    async def _loop(self):
        errors = 0
        index = 0
        folder = self.root / "data" / "live_sessions" / self.session_id
        folder.mkdir(parents=True, exist_ok=True)
        try:
            while True:
                await self.broadcast(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "measuring",
                        "warning": WARNING,
                    }
                )
                try:
                    acquisitions = [
                        await acquire_sweep(self.device, self.cfg)
                        for _ in range(self.run_average_count)
                    ]
                    frequency = acquisitions[0][0]
                    s11 = np.mean([item[1] for item in acquisitions], axis=0)
                    s21 = np.mean([item[2] for item in acquisitions], axis=0)
                    trace = interpolate_trace(Trace(frequency, s11, s21))
                    self.recent_traces.append(trace)
                    result = self.stabilizer.add(
                        self.predictor.predict(trace, prefer_live=True)
                    )
                    stamp = datetime.now(timezone.utc).isoformat()
                    base = folder / f"sweep_{index:05d}"
                    write_touchstone(base.with_suffix(".s2p"), frequency, s11, s21)
                    message = {
                        "timestamp": stamp,
                        "status": "complete",
                        "frequency_hz": trace.frequency_hz.tolist(),
                        "s21_db": trace.s21_db.tolist(),
                        **result,
                    }
                    base.with_suffix(".json").write_text(
                        json.dumps(message, indent=2), encoding="utf-8"
                    )
                    await self.broadcast(message)
                    errors = 0
                    index += 1
                    if index >= self.cfg.get("sweeps_per_sample", 5):
                        self.state = "connected"
                        device_status = self.status()
                        device_status["running"] = False
                        await self.broadcast(
                            {
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "status": "connected",
                                "device": device_status,
                                "sample_complete": True,
                                "warning": WARNING,
                            }
                        )
                        break
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    errors += 1
                    self.last_error = str(exc)
                    error = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "error",
                        "error": str(exc),
                        "attempt": errors,
                        "warning": WARNING,
                    }
                    (folder / f"error_{index:05d}_{errors}.json").write_text(
                        json.dumps(error, indent=2), encoding="utf-8"
                    )
                    await self.broadcast(error)
                    if errors >= self.cfg["maximum_consecutive_errors"]:
                        self.state = "error"
                        await self.device.disconnect()
                        break
                await asyncio.sleep(self.run_interval_seconds)
        finally:
            if self.state == "measuring":
                self.state = (
                    "connected"
                    if self.device and self.device.connected
                    else "disconnected"
                )
