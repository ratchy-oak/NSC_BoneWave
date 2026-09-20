import json
import re

from playwright.sync_api import expect
from conftest import ARTIFACTS


def test_mock_scan_completes_and_disconnects(dashboard, browser_page):
    """Real browser -> HTTP/WebSocket -> backend -> built-in mock -> rendered result."""
    base_url, work = dashboard
    page = browser_page
    errors = []
    frames = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("websocket", lambda ws: ws.on("framereceived", lambda payload: frames.append(json.loads(payload))))
    page.goto(base_url)
    expect(page.locator("#connection")).to_have_text("Disconnected")
    expect(page.locator("#start")).to_be_disabled()
    page.locator("#ports").select_option("MOCK")
    page.locator("#connect").click()
    expect(page.locator("#connection")).to_have_text("Connected")
    expect(page.locator("#start")).to_be_enabled()
    page.locator("#openSetup").click()
    expect(page.locator("#setupDialog")).to_be_visible()
    expect(page.locator("#setupProgressText")).to_have_text("0 of 3 captured")
    page.get_by_role("button", name="Close setup").click()
    expect(page.locator("#setupDialog")).not_to_be_visible()

    page.locator("#start").click()
    expect(page.locator("#measurement")).to_have_text("Measuring")
    expect(page.locator("#start")).to_be_disabled()
    expect(page.locator("#stop")).to_be_enabled()
    expect(page.locator("#measurement")).to_have_text("Complete", timeout=30000)
    expect(page.locator("#status")).to_have_text("Complete")
    expect(page.locator("#start")).to_be_enabled()
    expect(page.locator("#stop")).to_be_disabled()
    completed = [frame for frame in frames if frame.get("status") == "complete"]
    assert [frame["completed_sweeps"] for frame in completed] == [1, 2, 3]
    label = completed[-1]["prediction"]
    expect(page.locator("#resultTitle")).to_have_text(label.replace("_", " "))
    expect(page.locator("#scoreValue")).to_have_text(re.compile(r"\d+\.\d%"))
    assert any(frame.get("sample_complete") for frame in frames)
    assert len(list((work / "data/live_sessions").rglob("*.s2p"))) == 3
    page.screenshot(path=str(ARTIFACTS / "completed-scan.png"), full_page=True)

    page.locator("#disconnect").click()
    expect(page.locator("#connection")).to_have_text("Disconnected")
    expect(page.locator("#start")).to_be_disabled()
    assert not page.request.get(base_url + "/api/live/status").json()["connected"]
    assert errors == []
