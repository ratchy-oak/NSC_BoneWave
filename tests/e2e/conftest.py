"""Launch the real FastAPI app in an isolated copy for Chromium tests."""
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = Path(os.environ.get("E2E_ARTIFACTS", ROOT / "test-results/latest/e2e")).resolve()


@pytest.fixture
def dashboard(tmp_path):
    work = tmp_path / "BoneWave-AI"
    for folder in ("app", "config", "data/real"):
        shutil.copytree(ROOT / "BoneWave-AI" / folder, work / folder,
                        ignore=shutil.ignore_patterns("__pycache__"))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with (ARTIFACTS / "server.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                                    "--host", "127.0.0.1", "--port", str(port)],
                                   cwd=work, stdout=log, stderr=subprocess.STDOUT)
        try:
            base_url = f"http://127.0.0.1:{port}"
            deadline = time.monotonic() + 20
            while True:
                if process.poll() is not None:
                    pytest.fail("Dashboard server exited; inspect server.log")
                try:
                    with urlopen(base_url + "/api/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                if time.monotonic() > deadline:
                    pytest.fail("Dashboard startup timed out; inspect server.log")
                time.sleep(.1)
            yield base_url, work
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture
def browser_page(request):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        try:
            yield page
        finally:
            ARTIFACTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(ARTIFACTS / f"{request.node.name}.png"), full_page=True)
            context.tracing.stop(path=str(ARTIFACTS / f"{request.node.name}.zip"))
            context.close()
            browser.close()
