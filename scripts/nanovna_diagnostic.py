"""Record raw NanoVNA responses to identify firmware command compatibility."""
import argparse,asyncio,json,logging,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.nanovna.device import SerialNanoVNA
async def run(port,baudrate):
    log=ROOT/"data"/"live_sessions"/f"diagnostic_{datetime.now():%Y%m%d_%H%M%S}"; log.mkdir(parents=True,exist_ok=True)
    dev=SerialNanoVNA(port,baudrate); logging.basicConfig(filename=log/"raw_serial.log",level=logging.DEBUG,force=True)
    try:
        info=await dev.connect(); (log/"device_info.json").write_text(json.dumps({"timestamp":datetime.now(timezone.utc).isoformat(),**info},indent=2)); print(f"Diagnostic saved to {log}")
    finally: await dev.disconnect()
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--port",default="COM4");p.add_argument("--baudrate",type=int,default=115200);a=p.parse_args();asyncio.run(run(a.port,a.baudrate))

