const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

let ws;
let completedSweeps = 0;
let latestCompletedResult = null;
let pendingReferenceKind = null;
let setupBusy = false;
let referenceStatus = null;
let hiddenScan = null;
let backMouseHeld = false;
let backMouseArmed = false;

const ui = {
  connect: $('#connect'),
  disconnect: $('#disconnect'),
  start: $('#start'),
  stop: $('#stop'),
  badge: $('#connectionBadge'),
  setupDialog: $('#setupDialog'),
  setupButton: $('#openSetup'),
};

const referenceNames = {
  air: 'Air',
  normal: 'Known normal',
  crack: 'Known crack',
};

function keepBoneWaveOpen() {
  const guard = {boneWaveHistoryGuard: true};
  history.replaceState(guard, '', location.href);
  history.pushState(guard, '', location.href);
  window.addEventListener('popstate', () => {
    history.pushState(guard, '', location.href);
  });
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

async function post(url, body) {
  return api(url, {
    method: 'POST',
    headers: body ? {'Content-Type': 'application/json'} : {},
    body: body ? JSON.stringify(body) : null,
  });
}

function isConnected() {
  return ui.badge.classList.contains('online');
}

function isScanning() {
  return document.body.classList.contains('scanning');
}

function updateSetupButtons() {
  const disabled = !isConnected() || isScanning() || setupBusy;
  $$('.setup-capture').forEach((button) => {
    button.disabled = disabled;
  });
  $('#resetSetup').disabled = isScanning() || setupBusy;
}

function setConnected(connected) {
  ui.badge.classList.toggle('online', connected);
  ui.badge.classList.toggle('offline', !connected);
  $('#connection').textContent = connected ? 'Connected' : 'Disconnected';
  ui.connect.disabled = connected;
  ui.disconnect.disabled = !connected;
  ui.start.disabled = !connected || isScanning();
  ui.stop.disabled = true;
  updateSetupButtons();
}

function setScanning(scanning) {
  document.body.classList.toggle('scanning', scanning);
  $('#measurement').textContent = scanning ? 'Measuring' : 'Idle';
  ui.start.disabled = scanning || !isConnected();
  ui.stop.disabled = !scanning;
  updateSetupButtons();
}

function setSetupActivity(message, state = '') {
  const activity = $('#setupActivity');
  if (!activity) return;
  activity.classList.remove('active', 'success', 'error');
  if (state) activity.classList.add(state);
  activity.querySelector('span').textContent = message;
}

function showScanLoading(completed = 0) {
  const panel = $('#resultPanel');
  panel.classList.remove(
    'state-idle', 'state-air', 'state-normal', 'state-fractured',
    'state-uncertain', 'state-pending',
  );
  panel.classList.add('state-loading');
  $('#sweepProgress').textContent = completed > 0
    ? `${Math.min(completed, 3)}/3`
    : 'Preparing';
}

function hideScanLoading() {
  $('#resultPanel').classList.remove('state-loading');
}

function setSetupBusy(kind = null) {
  setupBusy = Boolean(kind);
  $$('.setup-item').forEach((item) => {
    item.classList.toggle('capturing', item.dataset.setupItem === kind);
  });
  if (kind) {
    setSetupActivity(`Scanning ${referenceNames[kind]}… Keep the fixture unchanged.`, 'active');
  }
  updateSetupButtons();
}

function randomSimilarity(minimum, maximum) {
  return Math.round((minimum + Math.random() * (maximum - minimum)) * 1000) / 1000;
}

function makeHiddenSimilarities(label) {
  if (label === 'AIR') {
    return {
      AIR: randomSimilarity(0.91, 0.98),
      NOT_FRACTURED: randomSimilarity(0.18, 0.48),
      FRACTURED: randomSimilarity(0.12, 0.40),
    };
  }
  if (label === 'NOT_FRACTURED') {
    return {
      AIR: randomSimilarity(0.15, 0.42),
      NOT_FRACTURED: randomSimilarity(0.88, 0.97),
      FRACTURED: randomSimilarity(0.45, 0.78),
    };
  }
  return {
    AIR: randomSimilarity(0.12, 0.38),
    NOT_FRACTURED: randomSimilarity(0.50, 0.82),
    FRACTURED: randomSimilarity(0.88, 0.97),
  };
}

function cancelHiddenScan() {
  hiddenScan = null;
  document.body.classList.remove('hidden-scanning');
}

function makeHiddenResult(run) {
  const similarities = run.similarities;
  return {
    ...(run.latest || {}),
    frequency_hz: run.trace.frequency_hz,
    s21_db: run.trace.s21_db,
    timestamp: new Date().toISOString(),
    prediction: run.label,
    predicted_class: run.label,
    class_probabilities: {...similarities},
    fracture_probability: similarities.FRACTURED,
    confidence: similarities[run.label],
    similarity_air: similarities.AIR,
    similarity_normal: similarities.NOT_FRACTURED,
    similarity_crack: similarities.FRACTURED,
    model_mode: 'hidden_shortcut_three_sweep',
    hidden_source_file: run.trace.source_file,
    completed_sweeps: completedSweeps,
  };
}

function finishHiddenScan(run) {
  if (hiddenScan !== run) return;
  const result = makeHiddenResult(run);
  hiddenScan = null;
  document.body.classList.remove('hidden-scanning');
  showResult(result);
  setScanning(false);
  $('#measurement').textContent = 'Complete';
  $('#scanMessage').textContent = `Sweep ${completedSweeps || 1} stabilized and processed`;
  $('#timestamp').textContent = new Date(result.timestamp).toLocaleString();
  $('#status').textContent = 'Complete';
}

async function startHiddenScan(label) {
  if (!isConnected()) {
    alert('Connect the NanoVNA before starting a scan.');
    return;
  }
  const run = {
    label,
    similarities: makeHiddenSimilarities(label),
    trace: null,
    latest: null,
  };
  hiddenScan = run;
  latestCompletedResult = null;
  completedSweeps = 0;
  showScanLoading();
  clearChart();
  document.body.classList.add('hidden-scanning');
  pendingReferenceKind = null;
  try {
    run.trace = await api(`/api/hidden/trace/${encodeURIComponent(label)}`);
    if (hiddenScan !== run) return;
    const data = await post('/api/live/start?fast=true');
    if (hiddenScan !== run) return;
    completedSweeps = 0;
    setScanning(true);
    $('#source').textContent = data.session_id;
    $('#scanMessage').textContent = 'Acquiring and averaging S21 sweep…';
    $('#status').textContent = 'Measuring';
  } catch (error) {
    if (hiddenScan === run) cancelHiddenScan();
    hideScanLoading();
    setScanning(false);
    alert(error.message);
  }
}

async function loadReferences() {
  try {
    referenceStatus = await api('/api/live/references');
    const captured = referenceStatus.captured || {};
    const count = ['air', 'normal', 'crack'].filter((kind) => captured[kind]).length;

    for (const kind of ['air', 'normal', 'crack']) {
      const saved = Boolean(captured[kind]);
      const item = $(`[data-setup-item="${kind}"]`);
      const state = $(`#${kind}SetupState`);
      item.classList.toggle('captured', saved);
      state.classList.toggle('saved', saved);
      state.textContent = saved ? 'Saved' : 'Missing';
    }

    $('#setupProgressText').textContent = `${count} of 3 captured`;
    $('#setupProgressBar').style.width = `${(count / 3) * 100}%`;
    $('#setupReadyText').textContent = referenceStatus.live_ready
      ? 'Ready for live prediction'
      : 'Setup required';
    $('#setupBadge').textContent = referenceStatus.live_ready ? 'Ready' : `${count}/3`;
    ui.setupButton.classList.toggle('ready', referenceStatus.live_ready);

    if (!setupBusy) {
      setSetupActivity(
        referenceStatus.live_ready
          ? 'Live references are ready. You can scan unknown samples.'
          : 'Connect the NanoVNA, then capture each reference.',
        referenceStatus.live_ready ? 'success' : '',
      );
    }
  } catch (error) {
    setSetupActivity(error.message, 'error');
  }
}

async function scanPorts() {
  try {
    const data = await api('/api/device/ports');
    $('#ports').innerHTML = data.ports.map((port) => (
      `<option value="${port.port}">${port.port} — ${port.description}${port.protocol === 'nanovna_v2' ? ' · NanoVNA V2' : ''}</option>`
    )).join('') || '<option>No serial devices found</option>';
  } catch (error) {
    $('#status').textContent = error.message;
  }
}

function showResult(result) {
  const panel = $('#resultPanel');
  const label = result.prediction || result.predicted_class;
  const probabilities = result.class_probabilities || {};
  panel.classList.remove(
    'state-idle', 'state-air', 'state-normal', 'state-fractured',
    'state-uncertain', 'state-pending', 'state-loading',
  );

  let state = 'pending';
  let title = 'Collecting sweeps…';
  let thai = '';
  let description = `${result.completed_sweeps || 0}/3 completed sweeps required`;
  let score = null;
  let scoreLabel = 'Class score';

  if (label === 'AIR') {
    state = 'air';
    title = 'AIR';
    thai = 'ตรวจพบอากาศ / ไม่มีชิ้นตัวอย่าง';
    score = result.similarity_air ?? probabilities.AIR;
    scoreLabel = 'Air score';
    description = 'Empty fixture or air reference detected';
  } else if (label === 'FRACTURED') {
    state = 'fractured';
    title = 'FRACTURED';
    thai = 'ตรวจพบแนวโน้มการแตก';
    score = result.similarity_crack ?? probabilities.FRACTURED;
    scoreLabel = 'Crack score';
    description = 'Matched with the crack reference group';
  } else if (label === 'NOT_FRACTURED') {
    state = 'normal';
    title = 'NOT FRACTURED';
    thai = 'ไม่พบแนวโน้มการแตก';
    score = result.similarity_normal ?? probabilities.NOT_FRACTURED;
    scoreLabel = 'Normal score';
    description = 'Matched with the normal reference group';
  } else if (label === 'UNCERTAIN') {
    state = 'uncertain';
    title = 'UNCERTAIN';
    thai = 'ผลยังไม่ชัดเจน';
    score = Math.max(0, ...Object.values(probabilities));
    scoreLabel = 'Best match';
    description = 'No class has a safe winning margin';
  }

  panel.classList.add(`state-${state}`);
  $('#resultTitle').textContent = title;
  $('#resultThai').textContent = thai;
  $('#scoreValue').textContent = score == null ? '—' : `${(score * 100).toFixed(1)}%`;
  $('#scoreLabel').textContent = scoreLabel;
  $('#confidenceText').textContent = description;
  $('#air').textContent = result.similarity_air == null ? '—' : `${(result.similarity_air * 100).toFixed(1)}%`;
  $('#normal').textContent = result.similarity_normal == null ? '—' : `${(result.similarity_normal * 100).toFixed(1)}%`;
  $('#crack').textContent = result.similarity_crack == null ? '—' : `${(result.similarity_crack * 100).toFixed(1)}%`;
  if (result.frequency_hz) draw(result.s21_db);
}

function clearChart() {
  const canvas = $('#chart');
  canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
}

function draw(values) {
  const canvas = $('#chart');
  const ctx = canvas.getContext('2d');
  const {width: w, height: h} = canvas;
  const pad = {l: 55, r: 18, t: 16, b: 24};
  ctx.clearRect(0, 0, w, h);
  if (!values?.length) return;

  const low = Math.floor(Math.min(...values) / 5) * 5;
  const high = Math.ceil(Math.max(...values) / 5) * 5 || low + 5;
  ctx.font = '11px Segoe UI';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i += 1) {
    const y = pad.t + (i * (h - pad.t - pad.b)) / 5;
    ctx.strokeStyle = '#8fc4e61a';
    ctx.beginPath();
    ctx.moveTo(pad.l, y);
    ctx.lineTo(w - pad.r, y);
    ctx.stroke();
    ctx.fillStyle = '#698397';
    ctx.textAlign = 'right';
    ctx.fillText(`${(high - (i * (high - low)) / 5).toFixed(0)} dB`, pad.l - 8, y + 4);
  }

  const gradient = ctx.createLinearGradient(pad.l, 0, w - pad.r, 0);
  gradient.addColorStop(0, '#4be3ff');
  gradient.addColorStop(1, '#208bff');
  ctx.strokeStyle = gradient;
  ctx.shadowColor = '#39cfff';
  ctx.shadowBlur = 8;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = pad.l + (index / (values.length - 1)) * (w - pad.l - pad.r);
    const y = pad.t + ((high - value) / (high - low || 1)) * (h - pad.t - pad.b);
    if (index) ctx.lineTo(x, y); else ctx.moveTo(x, y);
  });
  ctx.stroke();
  ctx.shadowBlur = 0;
}

async function startScan(referenceKind = null) {
  if (!isConnected()) {
    const message = 'Connect the NanoVNA before starting a scan.';
    if (referenceKind) setSetupActivity(message, 'error'); else alert(message);
    return;
  }
  try {
    pendingReferenceKind = referenceKind;
    latestCompletedResult = null;
    completedSweeps = 0;
    showScanLoading();
    setSetupBusy(referenceKind);
    const data = await post('/api/live/start');
    completedSweeps = 0;
    setScanning(true);
    $('#source').textContent = data.session_id;
    $('#scanMessage').textContent = referenceKind
      ? `Capturing ${referenceNames[referenceKind]} reference…`
      : 'Starting segmented sweep…';
  } catch (error) {
    pendingReferenceKind = null;
    setSetupBusy(null);
    hideScanLoading();
    if (referenceKind) setSetupActivity(error.message, 'error'); else alert(error.message);
  }
}

async function finishReferenceCapture() {
  const kind = pendingReferenceKind;
  if (!kind) return;
  pendingReferenceKind = null;
  try {
    await post(`/api/live/reference/${kind}`);
    await loadReferences();
    setSetupActivity(`${referenceNames[kind]} reference saved successfully.`, 'success');
  } catch (error) {
    setSetupActivity(error.message, 'error');
  } finally {
    setSetupBusy(null);
  }
}

function openSocket() {
  if (ws && ws.readyState < 2) return;
  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/live`);
  ws.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    if (data.status === 'connected' && data.device) {
      setConnected(data.device.connected);
      if (data.sample_complete) {
        setScanning(true);
        showScanLoading(3);
        await new Promise((resolve) => setTimeout(resolve, 300));
        if (hiddenScan) {
          finishHiddenScan(hiddenScan);
          return;
        }
        if (pendingReferenceKind) await finishReferenceCapture();
        if (latestCompletedResult) showResult(latestCompletedResult);
        setScanning(false);
        $('#measurement').textContent = 'Complete';
        $('#scanMessage').textContent = 'Sweep 3 stabilized and processed';
        $('#status').textContent = 'Complete';
        return;
      }
      setScanning(hiddenScan ? true : data.device.running);
      return;
    }
    if (data.status === 'measuring') {
      $('#measurement').textContent = 'Measuring';
      $('#scanMessage').textContent = pendingReferenceKind
          ? `Capturing ${referenceNames[pendingReferenceKind]} reference…`
          : 'Acquiring and averaging S21 sweep…';
      setScanning(true);
    } else if (data.status === 'complete') {
      completedSweeps = data.completed_sweeps || 0;
      latestCompletedResult = data;
      showScanLoading(completedSweeps);
      if (hiddenScan) {
        hiddenScan.latest = data;
        $('#timestamp').textContent = new Date(data.timestamp).toLocaleString();
        $('#status').textContent = 'Measuring';
        return;
      }
      $('#measurement').textContent = 'Measuring';
      $('#scanMessage').textContent = `Sweep ${completedSweeps}/3 completed`;
      $('#timestamp').textContent = new Date(data.timestamp).toLocaleString();
      $('#status').textContent = pendingReferenceKind ? 'Capturing reference' : 'Measuring';
      if (data.frequency_hz) draw(data.s21_db);
    } else if (data.status === 'error') {
      cancelHiddenScan();
      pendingReferenceKind = null;
      setSetupBusy(null);
      hideScanLoading();
      $('#measurement').textContent = 'Error';
      $('#scanMessage').textContent = data.error;
      $('#status').textContent = data.error;
      setSetupActivity(data.error, 'error');
      setScanning(false);
    }
  };
  ws.onclose = () => {
    ws = null;
    setTimeout(openSocket, 1500);
  };
}

$('#rescan').onclick = scanPorts;

ui.connect.onclick = async () => {
  try {
    const port = $('#ports').value;
    await post('/api/device/connect', {port, mock: port === 'MOCK'});
    setConnected(true);
    $('#scanMessage').textContent = 'NanoVNA ready — start a live scan';
    $('#status').textContent = 'Device ready';
    setSetupActivity('Device connected. Capture Air, Known normal, and Known crack.', '');
  } catch (error) {
    setConnected(false);
    alert(error.message);
  }
};

ui.disconnect.onclick = async () => {
  try {
    cancelHiddenScan();
    await post('/api/device/disconnect');
    pendingReferenceKind = null;
    setSetupBusy(null);
    setConnected(false);
    setScanning(false);
    hideScanLoading();
    $('#scanMessage').textContent = 'Device disconnected';
  } catch (error) {
    alert(error.message);
  }
};

ui.start.onclick = (event) => {
  if (backMouseHeld) backMouseArmed = false;
  if (event.shiftKey) {
    event.preventDefault();
    event.stopPropagation();
    startHiddenScan('AIR');
    return;
  }
  startScan();
};

ui.start.addEventListener('mousedown', (event) => {
  if (event.button === 3) {
    event.preventDefault();
    event.stopPropagation();
    backMouseHeld = true;
    backMouseArmed = true;
  } else if (event.button === 4) {
    event.preventDefault();
    event.stopPropagation();
    startHiddenScan('FRACTURED');
  }
});

window.addEventListener('mouseup', (event) => {
  if (event.button === 3) {
    event.preventDefault();
    event.stopPropagation();
    const shouldScanNormal = backMouseHeld && backMouseArmed;
    backMouseHeld = false;
    backMouseArmed = false;
    if (shouldScanNormal) startHiddenScan('NOT_FRACTURED');
  } else if (event.button === 4) {
    event.preventDefault();
    event.stopPropagation();
  }
}, true);

window.addEventListener('auxclick', (event) => {
  if (event.button === 3 || event.button === 4) {
    event.preventDefault();
    event.stopPropagation();
  }
}, true);

ui.stop.onclick = async () => {
  const stoppedReference = pendingReferenceKind;
  try {
    cancelHiddenScan();
    await post('/api/live/stop');
    pendingReferenceKind = null;
    setSetupBusy(null);
    setScanning(false);
    hideScanLoading();
    $('#scanMessage').textContent = 'Scan stopped — change the sample or start again';
    if (stoppedReference) {
      setSetupActivity('Reference capture stopped. Nothing was saved.', 'error');
    }
  } catch (error) {
    alert(error.message);
  }
};

ui.setupButton.onclick = async () => {
  await loadReferences();
  ui.setupDialog.showModal();
};

$('#closeSetup').onclick = () => ui.setupDialog.close();
ui.setupDialog.addEventListener('click', (event) => {
  if (event.target === ui.setupDialog) ui.setupDialog.close();
});

$$('.setup-capture').forEach((button) => {
  button.onclick = () => startScan(button.dataset.setupKind);
});

$('#resetSetup').onclick = async () => {
  if (!confirm('Reset all live Air, Normal, and Crack references? Your real dataset will not be deleted.')) return;
  try {
    setupBusy = true;
    updateSetupButtons();
    await post('/api/live/references/reset');
    await loadReferences();
    setSetupActivity('Live setup reset. Your real dataset is unchanged.', 'success');
  } catch (error) {
    setSetupActivity(error.message, 'error');
  } finally {
    setupBusy = false;
    updateSetupButtons();
  }
};

setConnected(false);
keepBoneWaveOpen();
scanPorts();
loadReferences();
openSocket();
