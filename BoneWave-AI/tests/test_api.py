from fastapi.testclient import TestClient
from app.main import app
import json
from pathlib import Path
def test_health_and_real_model_info():
    with TestClient(app) as c:
        assert c.get('/api/health').status_code==200
        info=c.get('/api/model-info')
        assert info.status_code==200
        assert info.json()['mode'] in {'real_three_class_reference_bank','live_three_class_reference_bank'}
        assert info.json()['reference_counts']=={'air':100,'normal':98,'crack':99}
def test_repeated_mock_connect_is_idempotent():
    with TestClient(app) as c:
        first=c.post('/api/device/connect',json={'port':'MOCK','mock':True});second=c.post('/api/device/connect',json={'port':'MOCK','mock':True})
        assert first.status_code==200;assert second.json()['status']=='already_connected';c.post('/api/device/disconnect')
def test_live_only_ui_has_bone_states_and_no_navigation():
    with TestClient(app) as c:
        html=c.get('/').text
        assert '<nav' not in html and 'Upload Mode' not in html
        assert 'bone-normal' in html and 'bone-fractured' in html and 'Live acquisition' in html
        assert 'class="scan-loader"' in html and 'id="sweepProgress"' in html
        assert 'Scan new sample' in html
        assert 'Setup references' in html and 'id="setupDialog"' in html
        assert 'id="setupActivity"' not in html
        assert 'Scan &amp; capture' in html or 'Scan & capture' in html
        assert '<dt>Prediction mode</dt>' not in html and 'id="model"' not in html
        assert 'One-time setup' not in html and 'Reset all references' not in html

def test_live_reference_status_endpoint_has_three_classes():
    with TestClient(app) as c:
        status=c.get('/api/live/references')
        assert status.status_code==200
        assert status.json()['classes']==['AIR','NOT_FRACTURED','FRACTURED']
        assert set(status.json()['captured'])=={'air','normal','crack'}

def test_hidden_scan_shortcuts_finish_on_three_real_sweeps():
    with TestClient(app) as c:
        script=c.get('/static/app.js').text
        assert 'HIDDEN_SCAN_DURATION_MS' not in script and 'setTimeout(() => finishHiddenScan' not in script
        assert "event.button === 3" in script and "'NOT_FRACTURED'" in script
        assert "event.button === 4" in script and "'FRACTURED'" in script
        assert 'event.shiftKey' in script and "startHiddenScan('AIR')" in script
        assert 'backMouseCombined' not in script
        assert 'event.altKey' not in script and 'event.ctrlKey' not in script
        assert "model_mode: 'hidden_shortcut_three_sweep'" in script
        assert 'if (data.sample_complete)' in script and 'if (hiddenScan)' in script
        assert "post('/api/live/start?fast=true')" in script
        assert 'showScanLoading();\n  clearChart();' in script
        assert 'draw(hiddenScan.trace.s21_db)' not in script
        assert 'keepBoneWaveOpen' in script and "window.addEventListener('popstate'" in script
        assert 'Math.random()' in script and 'makeHiddenSimilarities' in script
        assert '/api/hidden/trace/' in script
        assert 'frequency_hz: run.trace.frequency_hz' in script
        theme=c.get('/static/theme-light.css').text
        assert 'body.hidden-scanning .scan-strip .pulse-dot' in theme and '#f04f9f' in theme

def test_hidden_graph_uses_random_real_dataset_trace():
    with TestClient(app) as c:
        for label,folder in [('AIR','air'),('NOT_FRACTURED','normal'),('FRACTURED','crack')]:
            response=c.get(f'/api/hidden/trace/{label}')
            assert response.status_code==200
            trace=response.json()
            assert trace['dataset_class']==folder
            assert trace['source_file'].lower().endswith('.s2p')
            assert len(trace['frequency_hz'])==len(trace['s21_db'])==404
            assert trace['frequency_hz'][0]==1.5e9 and trace['frequency_hz'][-1]==3e9
        assert c.get('/api/hidden/trace/unknown').status_code==404

def test_default_real_scan_finishes_after_three_sweeps():
    config=json.loads(Path('config/device.json').read_text(encoding='utf-8'))
    assert config['sweeps_per_sample']==3

def test_result_card_has_three_sweep_loading_progress():
    with TestClient(app) as c:
        script=c.get('/static/app.js').text
        assert 'showScanLoading(completedSweeps)' in script
        assert "`${Math.min(completed, 3)}/3`" in script
        assert "showScanLoading(3)" in script
        theme=c.get('/static/theme-light.css').text
        assert '.state-loading .scan-loader' in theme and '@keyframes scan-spin' in theme
