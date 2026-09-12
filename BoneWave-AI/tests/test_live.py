import asyncio
from pathlib import Path
import numpy as np,pytest
from fastapi.testclient import TestClient
from app.main import app,live
from app.live_manager import Stabilizer,LiveManager
from app.nanovna.device import MockNanoVNA,DeviceError
from app.nanovna.protocol import NanoVNAV2Protocol,ProtocolError
from app.nanovna.acquisition import merge_segments
def test_mock_connect_disconnect():
    async def go():
        d=MockNanoVNA();await live.connect(d);assert d.connected;await live.disconnect();assert not d.connected
    asyncio.run(go())
def test_duplicate_boundaries_and_malformed():
    a=(np.array([1.,2.]),np.ones(2),np.ones(2));b=(np.array([2.,3.]),np.ones(2),np.ones(2));assert len(merge_segments([a,b],3)[0])==3
    with pytest.raises(DeviceError):merge_segments([(np.array([1,2]),np.ones(1),np.ones(2))])
def test_stabilizer():
    s=Stabilizer();base=lambda p:{'fracture_probability':p,'prediction':'FRACTURED' if p>.5 else 'NOT_FRACTURED'}
    assert s.add(base(.8))['prediction']=='PENDING';s.add(base(.7));assert s.add(base(.9))['prediction']=='FRACTURED';s.reset();s.add(base(.45));s.add(base(.55));assert s.add(base(.5))['prediction']=='UNCERTAIN'
def test_stabilizer_keeps_air_as_a_real_class():
    s=Stabilizer();air=lambda:{'fracture_probability':.01,'prediction':'AIR','class_probabilities':{'AIR':.94,'NOT_FRACTURED':.05,'FRACTURED':.01}}
    assert s.add(air())['prediction']=='PENDING';s.add(air());result=s.add(air())
    assert result['prediction']=='AIR' and result['class_probabilities']['AIR']==pytest.approx(.94)

def test_live_stabilizer_always_selects_highest_percentage():
    s=Stabilizer()
    narrow=lambda:{'fracture_probability':.50,'prediction':'FRACTURED','model_mode':'live_three_class_reference_bank','class_probabilities':{'AIR':.01,'NOT_FRACTURED':.49,'FRACTURED':.50}}
    assert s.add(narrow())['prediction']=='PENDING';s.add(narrow());result=s.add(narrow())
    assert result['prediction']=='FRACTURED'
    assert result['confidence']==pytest.approx(.50)
def test_websocket_and_loop_cancellation():
    with TestClient(app) as c:
        c.post('/api/device/connect',json={'port':'MOCK','mock':True})
        with c.websocket_connect('/ws/live') as ws:
            assert ws.receive_json()['status']=='connected';assert c.post('/api/live/start').status_code==200;msg=ws.receive_json();assert msg['status']=='measuring';assert c.post('/api/live/stop').status_code==200
        c.post('/api/device/disconnect')
def test_release_after_errors():
    async def go():
        d=MockNanoVNA(fail_after=1);old=live.cfg['maximum_consecutive_errors'];live.cfg['maximum_consecutive_errors']=1;await live.connect(d);await live.start();await live.task;assert not d.connected and live.state=='error';live.cfg['maximum_consecutive_errors']=old;await live.disconnect()
    asyncio.run(go())
def test_v2_binary_protocol_commands_and_fifo():
    import struct
    p=NanoVNAV2Protocol();cmd=p.configure_sweep(1_500_000_000,1_875_000_000,101)
    assert cmd[0:2]==bytes((p.WRITE8,p.SWEEP_START));assert p.read_fifo(101)==bytes((p.READ_FIFO,p.VALUES_FIFO,101))
    records=[]
    for index in range(2): records.append(struct.pack('<iiiiiihxxxxxx',100,0,10+index,0,20+index,0,index))
    s11,s21=p.parse_fifo(b''.join(records),2);assert s11==[.1+.0j,.11+.0j];assert s21==[.2+.0j,.21+.0j]
    with pytest.raises(ProtocolError):p.parse_fifo(b'bad',2)
def test_stabilizer_keeps_raw_probability():
    s=Stabilizer();r=s.add({'fracture_probability':.8,'prediction':'FRACTURED'});assert r['raw_fracture_probability']==.8
def test_real_multi_angle_bank_and_air_guard():
    from app.predictor import Predictor
    from app.touchstone import load_standard_trace
    p=Predictor();p.clear_live_references();status=p.reference_status()
    assert status["source"]=="real_multi_angle_fallback"
    assert status["reference_counts"]=={"air":100,"normal":98,"crack":99}
    assert status["ignored_exact_duplicates"]==3 and status["load_errors"]==0
    normal=p.predict(load_standard_trace(Path("data/real/normal/Normal_002.s2p")),prefer_live=True)
    crack=p.predict(load_standard_trace(Path("data/real/crack/Crack_002.s2p")),prefer_live=True)
    air=p.predict(load_standard_trace(Path("data/real/air/Air_002.s2p")),prefer_live=True)
    assert normal["prediction"]=="NOT_FRACTURED"
    assert crack["prediction"]=="FRACTURED"
    assert air["prediction"]=="AIR"
    assert set(air["class_probabilities"])=={"AIR","NOT_FRACTURED","FRACTURED"}
def test_one_sample_scan_stops_after_configured_sweeps(tmp_path):
    from app.predictor import Predictor
    async def go():
        cfg={"start_frequency_hz":1.5e9,"stop_frequency_hz":3e9,"segments":1,"points_per_segment":101,"average_count":1,"measurement_interval_seconds":0,"maximum_consecutive_errors":1,"sweeps_per_sample":2}
        manager=LiveManager(Predictor(),cfg,tmp_path);device=MockNanoVNA();await manager.connect(device);await manager.start();await manager.task
        assert manager.state=="connected" and device.count==2
        assert len(manager.recent_traces)==2
        await manager.disconnect()
    asyncio.run(go())

def test_hidden_scan_can_override_only_the_interval(tmp_path):
    from app.predictor import Predictor
    async def go():
        cfg={"start_frequency_hz":1.5e9,"stop_frequency_hz":3e9,"segments":1,"points_per_segment":101,"average_count":1,"measurement_interval_seconds":2,"maximum_consecutive_errors":1,"sweeps_per_sample":3}
        manager=LiveManager(Predictor(),cfg,tmp_path);device=MockNanoVNA();await manager.connect(device)
        await manager.start(measurement_interval_seconds=.25,average_count=1)
        assert manager.run_interval_seconds==.25 and manager.run_average_count==1
        await manager.stop();await manager.disconnect()
    asyncio.run(go())

def test_live_setup_persists_and_resets_three_sweep_reference(tmp_path):
    from app.predictor import Predictor
    async def go():
        cfg={"start_frequency_hz":1.5e9,"stop_frequency_hz":3e9,"segments":1,"points_per_segment":101,"average_count":1,"measurement_interval_seconds":0,"maximum_consecutive_errors":1,"sweeps_per_sample":3}
        predictor=Predictor();predictor.clear_live_references()
        manager=LiveManager(predictor,cfg,tmp_path);device=MockNanoVNA()
        await manager.connect(device);await manager.start();await manager.task
        metadata=manager.capture_reference("air")
        saved=sorted((tmp_path/"data"/"live_references"/"air").glob("*.s2p"))
        assert metadata["sweeps"]==3 and len(saved)==3
        assert len(manager.recent_traces)==0
        assert predictor.reference_status()["captured"]["air"] is True
        result=manager.reset_references()
        assert result["references"]["live_reference_counts"]=={"air":0,"normal":0,"crack":0}
        assert not (tmp_path/"data"/"live_references"/"air").exists()
        await manager.disconnect()
    asyncio.run(go())

def test_complete_live_setup_classifies_air_normal_and_crack():
    from app.predictor import Predictor
    from app.touchstone import load_standard_trace
    predictor=Predictor();predictor.clear_live_references()
    samples={"air":("Air","AIR"),"normal":("Normal","NOT_FRACTURED"),"crack":("Crack","FRACTURED")}
    for kind,(prefix,_) in samples.items():
        traces=[load_standard_trace(Path(f"data/real/{kind}/{prefix}_{index:03d}.s2p")) for index in range(1,6)]
        predictor.set_live_reference_bank(kind,traces)
    assert predictor.reference_status()["live_ready"] is True
    for kind,(prefix,label) in samples.items():
        result=predictor.predict(load_standard_trace(Path(f"data/real/{kind}/{prefix}_002.s2p")),prefer_live=True)
        assert result["prediction"]==label
        assert result["model_mode"]=="live_three_class_reference_bank"
