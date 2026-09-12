from contextlib import asynccontextmanager
from pathlib import Path
import json,logging,secrets
from fastapi import FastAPI,HTTPException,WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .predictor import Predictor,WARNING
from .live_manager import LiveManager
from .nanovna.device import MockNanoVNA,available_ports,device_for_port
from .touchstone import load_standard_trace
ROOT=Path(__file__).resolve().parents[1]; logging.basicConfig(level=logging.INFO)
cfg=json.loads((ROOT/"config"/"device.json").read_text()); predictor=Predictor(); live=LiveManager(predictor,cfg,ROOT)
@asynccontextmanager
async def lifespan(app):
    yield
    await live.disconnect()
app=FastAPI(title="BoneWave AI",lifespan=lifespan); app.mount("/static",StaticFiles(directory=ROOT/"app"/"static"),name="static")
class ConnectRequest(BaseModel): port:str="COM4"; mock:bool=False
@app.get("/")
def index(): return FileResponse(ROOT/"app"/"static"/"index.html")
@app.get("/api/health")
def health(): return {"status":"ok","warning":WARNING}
@app.get("/api/model-info")
def model_info():
    references=predictor.reference_status()
    return {
        "mode":"live_three_class_reference_bank" if references["live_ready"] else "real_three_class_reference_bank",
        "usage":"Current NanoVNA live setup" if references["live_ready"] else "Same-specimen, multi-angle research prototype",
        **references,
        "independent_test_specimens":0,
        "warning":"No generalization or medical accuracy claim; Normal and Crack each contain angles from one specimen.",
    }
@app.get("/api/device/ports")
def ports(): return {"ports":available_ports()+[{"port":"MOCK","description":"Built-in test device"}]}
@app.post("/api/device/connect")
async def connect(req:ConnectRequest):
    try:
        same_mock = req.mock or req.port.upper() == "MOCK"
        if live.device and live.device.connected:
            current_port = getattr(live.device, "port", "MOCK")
            if (same_mock and current_port == "MOCK") or current_port == req.port:
                return {"status":"already_connected","info":live.device.info}
        device=MockNanoVNA() if req.mock or req.port.upper()=="MOCK" else device_for_port(req.port,cfg["baudrate"],cfg["serial_timeout_seconds"])
        return {"status":"connected","info":await live.connect(device)}
    except Exception as exc: raise HTTPException(503,str(exc)) from exc
@app.post("/api/device/disconnect")
async def disconnect(): await live.disconnect(); return live.status()
@app.post("/api/live/start")
async def start(fast:bool=False):
    try: return {"status":"started","session_id":await live.start(0.25 if fast else None,1 if fast else None)}
    except RuntimeError as exc: raise HTTPException(409,str(exc)) from exc
@app.post("/api/live/stop")
async def stop(): await live.stop(); return live.status()
@app.get("/api/live/status")
def status(): return live.status()
@app.get("/api/live/references")
def reference_status(): return predictor.reference_status()
@app.get("/api/hidden/trace/{label}")
def hidden_dataset_trace(label:str):
    classes={"AIR":"air","NOT_FRACTURED":"normal","FRACTURED":"crack"}
    normalized=label.upper()
    if normalized not in classes: raise HTTPException(404,"Unknown hidden trace class")
    kind=classes[normalized]
    files=predictor.reference_files[kind]
    if not files: raise HTTPException(503,f"No real {kind} traces are available")
    filename=secrets.choice(files)
    trace=load_standard_trace(ROOT/"data"/"real"/kind/filename)
    return {
        "class":normalized,
        "dataset_class":kind,
        "source_file":filename,
        "frequency_hz":trace.frequency_hz.tolist(),
        "s21_db":trace.s21_db.tolist(),
    }
@app.post("/api/live/reference/{kind}")
def capture_reference(kind:str):
    try:
        return {
            "status":"captured",
            "metadata":live.capture_reference(kind),
            "references":predictor.reference_status(),
        }
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(409,str(exc)) from exc
@app.post("/api/live/references/reset")
async def reset_references():
    await live.stop()
    return live.reset_references()
@app.websocket("/ws/live")
async def websocket(ws:WebSocket):
    await ws.accept(); live.clients.add(ws); await ws.send_json({"status":"connected","device":live.status(),"warning":WARNING})
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: live.clients.discard(ws)
