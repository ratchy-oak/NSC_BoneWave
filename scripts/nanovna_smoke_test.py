"""Connect to one NanoVNA and acquire a short hardware-validation sweep."""
import argparse, asyncio, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.nanovna.device import device_for_port

async def run(port):
    device=device_for_port(port,115200,5)
    print(f"Adapter: {type(device).__name__}")
    try:
        print(f"Device: {await device.connect()}")
        frequency,_,s21=await device.acquire_segment(1_500_000_000,1_510_000_000,11)
        print(f"Sweep OK: {len(frequency)} points, first S21={s21[0]}")
    finally:
        await device.disconnect()

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--port",default="COM4");args=parser.parse_args();asyncio.run(run(args.port))
