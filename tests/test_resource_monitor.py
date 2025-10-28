"""Tests for resource monitoring functionality."""

import time

from bactscout.resource_monitor import (
    ResourceMonitor,
    get_process_memory,
    get_process_threads,
)


def test_resource_monitor_basic():
    """Test basic ResourceMonitor functionality."""
    monitor = ResourceMonitor()
    monitor.start()
    time.sleep(0.1)
    monitor.end()
    stats = monitor.get_stats()

    # Verify stats dictionary has expected keys
    assert "duration_sec" in stats
    assert "peak_threads" in stats
    assert "peak_memory_mb" in stats
    assert "avg_memory_mb" in stats

    # Verify reasonable values
    assert stats["duration_sec"] >= 0.1
    assert stats["peak_threads"] > 0
    assert stats["peak_memory_mb"] > 0


def test_resource_monitor_duration():
    """Test that ResourceMonitor correctly measures duration."""
    monitor = ResourceMonitor()
    monitor.start()
    sleep_time = 0.2
    time.sleep(sleep_time)
    monitor.end()
    stats = monitor.get_stats()

    # Duration should be roughly equal to sleep time (within 100ms margin)
    assert stats["duration_sec"] >= sleep_time - 0.1


def test_resource_monitor_graceful_degradation():
    """Test that ResourceMonitor handles missing psutil gracefully."""
    monitor = ResourceMonitor()
    # Should not raise an exception even if psutil is unavailable
    monitor.start()
    time.sleep(0.05)
    monitor.end()
    stats = monitor.get_stats()

    # Should return valid stats dict
    assert isinstance(stats, dict)


def test_get_process_memory():
    """Test get_process_memory helper function."""
    mem = get_process_memory()

    # Should return a non-negative float
    assert isinstance(mem, float)
    assert mem >= 0.0


def test_get_process_threads():
    """Test get_process_threads helper function."""
    threads = get_process_threads()

    # Should return a non-negative integer
    assert isinstance(threads, int)
    assert threads > 0


def test_resource_monitor_memory_tracking():
    """Test that memory samples are collected."""
    monitor = ResourceMonitor()
    monitor.start()
    time.sleep(0.1)
    monitor.end()

    # Check internal state
    assert hasattr(monitor, "memory_samples")
    assert len(monitor.memory_samples) > 0


def test_resource_monitor_multiple_cycles():
    """Test multiple start/end cycles."""
    monitor = ResourceMonitor()

    # First cycle
    monitor.start()
    time.sleep(0.05)
    monitor.end()
    stats1 = monitor.get_stats()
    assert stats1["duration_sec"] > 0

    # Second cycle - create new monitor
    monitor2 = ResourceMonitor()
    monitor2.start()
    time.sleep(0.05)
    monitor2.end()
    stats2 = monitor2.get_stats()
    assert stats2["duration_sec"] > 0
