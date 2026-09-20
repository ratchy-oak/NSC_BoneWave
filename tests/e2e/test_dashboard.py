import json
import re
import hashlib
import pytest

from playwright.sync_api import expect
from conftest import ARTIFACTS


def exercise_scan(dashboard, browser_page, port, artifact_name, expected_label=None):
    base_url, work = dashboard
    page = browser_page
    errors = []
    frames = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("websocket", lambda ws: ws.on("framereceived", lambda payload: frames.append(json.loads(payload))))
    page.goto(base_url)
    expect(page.locator("#connection")).to_have_text("Disconnected")
    expect(page.locator("#start")).to_be_disabled()
    page.locator("#ports").select_option(port)
    with page.expect_response("**/api/device/connect") as connection:
        page.locator("#connect").click()
    info = connection.value.json()["info"]
    if port == "REPLAY":
        assert info["data_source"] == "recorded_real_measurement_replay"
        source = next((work / "data/real").rglob(info["source_file"]))
        assert info["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        (ARTIFACTS / f"{artifact_name}-source.json").write_text(json.dumps(info, indent=2))
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
    if expected_label:
        assert label == expected_label
    expect(page.locator("#resultTitle")).to_have_text(label.replace("_", " "))
    expect(page.locator("#scoreValue")).to_have_text(re.compile(r"\d+\.\d%"))
    assert any(frame.get("sample_complete") for frame in frames)
    assert len(list((work / "data/live_sessions").rglob("*.s2p"))) == 3
    page.screenshot(path=str(ARTIFACTS / f"{artifact_name}.png"), full_page=True)

    page.locator("#disconnect").click()
    expect(page.locator("#connection")).to_have_text("Disconnected")
    expect(page.locator("#start")).to_be_disabled()
    assert not page.request.get(base_url + "/api/live/status").json()["connected"]
    assert errors == []


def test_mock_scan_completes_and_disconnects(dashboard, browser_page):
    """Synthetic mock remains a deterministic regression test."""
    exercise_scan(dashboard, browser_page, "MOCK", "completed-scan")


@pytest.mark.parametrize("dashboard,expected_label", [
    ("air", "AIR"), ("normal", "NOT_FRACTURED"), ("crack", "FRACTURED"),
], indirect=["dashboard"])
def test_recorded_real_scan(dashboard, expected_label, browser_page):
    """Recorded real input, real backend/browser; same-reference matching only."""
    exercise_scan(dashboard, browser_page, "REPLAY", f"real-{expected_label.lower()}", expected_label)
