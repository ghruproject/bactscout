from types import SimpleNamespace

import pytest

from bactscout import resource_monitor as rm


def test_get_process_memory_threads_with_psutil(monkeypatch):
    """When psutil is available, functions should return converted memory and thread counts."""

    # Create a fake Process object that returns deterministic values
    class FakeProcess:
        def __init__(self, pid):
            self._pid = pid

        def memory_info(self):
            return SimpleNamespace(rss=50 * 1024 * 1024)  # 50 MB

        def num_threads(self):
            return 7

    # Fake psutil module with a Process factory
    fake_psutil = SimpleNamespace(Process=lambda pid: FakeProcess(pid))

    # Monkeypatch the module to behave as if psutil is installed
    monkeypatch.setattr(rm, "HAS_PSUTIL", True)
    monkeypatch.setattr(rm, "psutil", fake_psutil)

    mem_mb = rm.get_process_memory()
    threads = rm.get_process_threads()

    assert pytest.approx(mem_mb, rel=1e-3) == 50.0
    assert threads == 7


def test_get_process_memory_threads_without_psutil(monkeypatch):
    """When psutil is not available, functions should return sensible defaults (0)."""

    monkeypatch.setattr(rm, "HAS_PSUTIL", False)
    monkeypatch.setattr(rm, "psutil", None)

    assert rm.get_process_memory() == 0.0
    assert rm.get_process_threads() == 0
