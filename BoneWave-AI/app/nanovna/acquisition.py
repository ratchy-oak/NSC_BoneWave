import numpy as np
from .device import DeviceError
def merge_segments(segments,expected_points=None):
    rows=[]
    for f,s11,s21 in segments:
        if not (len(f)==len(s11)==len(s21)) or len(f)<2: raise DeviceError("Malformed or incomplete sweep segment")
        rows.extend(zip(f,s11,s21))
    rows.sort(key=lambda x:x[0]); unique=[]
    for row in rows:
        if unique and np.isclose(row[0],unique[-1][0],rtol=0,atol=.5): unique[-1]=row
        else: unique.append(row)
    if expected_points and len(unique)!=expected_points: raise DeviceError(f"Expected {expected_points} unique sweep points, received {len(unique)}")
    return tuple(np.asarray(x) for x in zip(*unique))
async def acquire_sweep(device,cfg):
    edges=np.linspace(cfg["start_frequency_hz"],cfg["stop_frequency_hz"],cfg["segments"]+1); segments=[]
    for i in range(cfg["segments"]): segments.append(await device.acquire_segment(edges[i],edges[i+1],cfg["points_per_segment"]))
    expected=cfg["segments"]*(cfg["points_per_segment"]-1)+1
    return merge_segments(segments,expected)

