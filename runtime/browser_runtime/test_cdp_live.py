from pathlib import Path

from runtime.browser_runtime import cdp_live


def test_isolated_browser_launcher_hides_windows_console(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict]] = []

    class _Process:
        pid = 4242

        def poll(self):
            return None

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

        def kill(self):
            return None

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(cdp_live.os, "name", "nt")
    monkeypatch.setattr(cdp_live.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(cdp_live, "_find_browser_executable", lambda: "C:/Browser/chrome.exe")
    monkeypatch.setattr(cdp_live, "_profile_temp_root", lambda: tmp_path)

    def fake_mkdtemp(*, prefix: str, dir: str) -> str:
        profile = Path(dir) / f"{prefix}test"
        profile.mkdir(parents=True, exist_ok=True)
        return str(profile)

    def fake_popen(args, **kwargs):
        calls.append((list(args), dict(kwargs)))
        return _Process()

    monkeypatch.setattr(cdp_live.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(cdp_live.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(cdp_live.urllib.request, "urlopen", lambda url, timeout=1: _Response())

    launcher = cdp_live.IsolatedBrowserLauncher(port=9333)

    try:
        result = launcher.launch()
    finally:
        launcher.close()

    assert result["cdp_endpoint"] == "http://127.0.0.1:9333"
    assert calls
    assert calls[0][1]["creationflags"] == 0x08000000
    assert calls[0][1]["stdout"] is cdp_live.subprocess.PIPE
    assert calls[0][1]["stderr"] is cdp_live.subprocess.PIPE
