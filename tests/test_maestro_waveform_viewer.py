from __future__ import annotations

import pytest

from virtuoso_bridge.virtuoso.maestro import (
    close_waveform_viewer,
    maestro_close_waveform_viewer_skill,
    maestro_open_waveform_viewer_skill,
    open_waveform_viewer,
)


def test_maestro_open_waveform_viewer_skill_plots_explicit_signals() -> None:
    skill = maestro_open_waveform_viewer_skill(
        "demoLib",
        "tb_inv",
        "Interactive.1",
        signals=["/IN", "/OUT"],
        results_dir="/tmp/psf/tran/psf",
        result="tran",
    )

    assert "isCallable('awvCreatePlotWindow)" in skill
    assert 'maeOpenSetup("demoLib" "tb_inv" "maestro" ?application "Assembler" ?mode "r")' in skill
    assert 'maeOpenResults(?session vbSession ?history "Interactive.1")' in skill
    assert 'openResults("/tmp/psf/tran/psf")' in skill
    assert 'v("/IN" ?result "tran" ?resultsDir vbResultsDir)' in skill
    assert 'v("/OUT" ?result "tran" ?resultsDir vbResultsDir)' in skill
    assert "awvCreatePlotWindow()" in skill
    assert 'awvPlotWaveform(vbWindowId vbWaveforms ?expr list("/IN" "/OUT"))' in skill


def test_maestro_open_waveform_viewer_keeps_results_session_alive() -> None:
    skill = maestro_open_waveform_viewer_skill(
        "demoLib",
        "tb_inv",
        "Interactive.1",
        signals=["/OUT"],
        results_dir="/tmp/psf/tran/psf",
    )

    assert "maeCloseResults" not in skill
    assert "maeCloseSession" not in skill


def test_maestro_open_waveform_viewer_skill_can_fallback_to_maestro_outputs() -> None:
    skill = maestro_open_waveform_viewer_skill(
        "demoLib",
        "tb_inv",
        "Interactive.1",
        signals=["vout"],
        test="tran",
    )

    assert 'maeGetOutputValue("vout" "tran")' in skill
    assert 'list("opened" "demoLib" "tb_inv" "maestro" "Interactive.1" vbSession vbWindowId)' in skill


def test_maestro_open_waveform_viewer_requires_signals() -> None:
    with pytest.raises(ValueError, match="signals must not be empty"):
        maestro_open_waveform_viewer_skill("demoLib", "tb_inv", "Interactive.1", signals=[])


def test_maestro_close_waveform_viewer_skill_closes_window_and_session() -> None:
    skill = maestro_close_waveform_viewer_skill(window="window:7", session="fnxSession2")

    assert "vbWindow = window(7)" in skill
    assert 'vbSession = "fnxSession2"' in skill
    assert "hiCloseWindow(vbWindow)" in skill
    assert "maeCloseSession(?session vbSession ?forceClose t)" in skill


def test_maestro_close_waveform_viewer_accepts_window_object_text() -> None:
    skill = maestro_close_waveform_viewer_skill(window="window(8)")

    assert "vbWindow = window(8)" in skill
    assert "vbSession = nil" in skill


def test_maestro_close_waveform_viewer_requires_target() -> None:
    with pytest.raises(ValueError, match="window or session must be provided"):
        maestro_close_waveform_viewer_skill()


def test_maestro_close_waveform_viewer_rejects_unsafe_window_ref() -> None:
    with pytest.raises(ValueError, match="window must be a window number"):
        maestro_close_waveform_viewer_skill(window='window(7) hiCloseWindow(window(1))')


def test_maestro_close_waveform_viewer_rejects_invalid_window_number() -> None:
    with pytest.raises(ValueError, match="positive window number"):
        maestro_close_waveform_viewer_skill(window=0)


def test_open_waveform_viewer_executes_generated_skill() -> None:
    class Client:
        skill: str | None = None
        timeout: int | None = None

        def execute_skill(self, skill: str, *, timeout: int):
            self.skill = skill
            self.timeout = timeout
            return {"status": "success", "output": '("opened" "demoLib" "tb_inv")'}

    client = Client()
    result = open_waveform_viewer(
        client,
        "demoLib",
        "tb_inv",
        "Interactive.1",
        signals=["/OUT"],
        timeout=30,
    )

    assert result == {"status": "success", "output": '("opened" "demoLib" "tb_inv")'}
    assert client.timeout == 30
    assert client.skill is not None
    assert 'awvPlotWaveform(vbWindowId vbWaveforms ?expr list("/OUT"))' in client.skill


def test_close_waveform_viewer_executes_generated_skill() -> None:
    class Client:
        skill: str | None = None
        timeout: int | None = None

        def execute_skill(self, skill: str, *, timeout: int):
            self.skill = skill
            self.timeout = timeout
            return {"status": "success", "output": '("closed" "fnxSession2" window:7)'}

    client = Client()
    result = close_waveform_viewer(
        client,
        window=7,
        session="fnxSession2",
        timeout=10,
    )

    assert result == {"status": "success", "output": '("closed" "fnxSession2" window:7)'}
    assert client.timeout == 10
    assert client.skill is not None
    assert "vbWindow = window(7)" in client.skill
    assert 'vbSession = "fnxSession2"' in client.skill
