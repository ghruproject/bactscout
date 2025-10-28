"""
Resource monitoring module for thread and memory usage tracking.

This module provides utilities for monitoring system resource usage (threads and memory)
during sample processing, useful for performance analysis, capacity planning, and
identifying resource-intensive samples.

Key Functions:
    - get_process_memory(): Get current process memory usage
    - get_process_threads(): Get current thread count
    - start_monitoring(): Initialize monitoring context
    - end_monitoring(): Finalize monitoring and return statistics

Workflow:
    1. Before processing: Record initial resource state
    2. During processing: Periodically sample resources (optional)
    3. After processing: Record final resource state
    4. Return: Min, max, average memory; thread count; duration

Dependencies:
    - psutil: Cross-platform process monitoring
    - time: Timing measurements

Example:
    >>> from bactscout.resource_monitor import ResourceMonitor
    >>> monitor = ResourceMonitor()
    >>> # ... do some work ...
    >>> stats = monitor.get_stats()
    >>> print(f"Peak memory: {stats['peak_memory_mb']:.2f} MB")
    >>> print(f"Duration: {stats['duration_sec']:.2f} seconds")
"""

import os
import threading
import time
from typing import Dict

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None  # type: ignore  # noqa: F841


class ResourceMonitor:
    """
    Monitor system resources (memory and threads) for a process.

    Tracks peak memory usage, average memory usage, thread count,
    and execution duration. Uses psutil for cross-platform compatibility.

    If psutil is not available, gracefully degrades with limited functionality.
    """

    def __init__(self, track_interval: float = 0.5):
        """
        Initialize resource monitor.

        Args:
            track_interval (float): Interval in seconds between memory samples
                during continuous monitoring. Default: 0.5 seconds.
        """
        self.track_interval = track_interval
        self.start_time = None
        self.end_time = None
        self.start_memory_mb = 0
        self.peak_memory_mb = 0
        self.memory_samples = []
        self.start_threads = 0
        self.peak_threads = 0
        self.monitoring_active = False
        self._monitor_thread = None
        self._process = None

        if HAS_PSUTIL:
            self._process = psutil.Process(os.getpid())  # type: ignore

    def start(self) -> None:
        """
        Start resource monitoring.

        Records initial state and starts continuous memory monitoring thread.
        """
        self.start_time = time.time()

        if HAS_PSUTIL and self._process:
            try:
                # Get initial memory
                mem_info = self._process.memory_info()
                self.start_memory_mb = mem_info.rss / (1024 * 1024)
                self.peak_memory_mb = self.start_memory_mb

                # Get initial thread count
                self.start_threads = self._process.num_threads()
                self.peak_threads = self.start_threads

                # Start continuous monitoring
                self.monitoring_active = True
                self._monitor_thread = threading.Thread(
                    target=self._monitor_resources, daemon=True
                )
                self._monitor_thread.start()
            except Exception:  # pylint: disable=broad-except
                # Process monitoring may fail, continue without it
                pass

    def end(self) -> None:
        """
        Stop resource monitoring and record final state.

        Stops continuous monitoring thread and captures final resource values.
        """
        self.end_time = time.time()
        self.monitoring_active = False

        # Wait for monitor thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

        # Final memory and thread count
        if HAS_PSUTIL and self._process:
            try:
                mem_info = self._process.memory_info()
                final_memory_mb = mem_info.rss / (1024 * 1024)
                self.memory_samples.append(final_memory_mb)
                self.peak_memory_mb = max(self.peak_memory_mb, final_memory_mb)

                final_threads = self._process.num_threads()
                self.peak_threads = max(self.peak_threads, final_threads)
            except Exception:  # pylint: disable=broad-except
                pass

    def _monitor_resources(self) -> None:
        """
        Continuously monitor resource usage (runs in separate thread).

        Periodically samples memory and thread usage at the specified interval.
        """
        while self.monitoring_active:
            if HAS_PSUTIL and self._process:
                try:
                    mem_info = self._process.memory_info()
                    current_memory_mb = mem_info.rss / (1024 * 1024)
                    self.memory_samples.append(current_memory_mb)
                    self.peak_memory_mb = max(self.peak_memory_mb, current_memory_mb)

                    current_threads = self._process.num_threads()
                    self.peak_threads = max(self.peak_threads, current_threads)
                except Exception:  # pylint: disable=broad-except
                    # Stop monitoring if process becomes inaccessible
                    self.monitoring_active = False
                    break

            time.sleep(self.track_interval)

    def get_stats(self) -> Dict[str, float]:
        """
        Get resource usage statistics.

        Returns:
            dict: Statistics containing:
                - duration_sec (float): Total elapsed time in seconds
                - peak_memory_mb (float): Peak memory usage in MB
                - avg_memory_mb (float): Average memory usage in MB (0 if not tracked)
                - start_memory_mb (float): Initial memory usage in MB
                - peak_threads (int): Maximum thread count observed
                - start_threads (int): Initial thread count
                - available (bool): True if psutil is available for accurate monitoring
        """
        duration = 0.0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        elif self.start_time:
            duration = time.time() - self.start_time

        avg_memory = 0.0
        if self.memory_samples:
            avg_memory = sum(self.memory_samples) / len(self.memory_samples)

        return {
            "duration_sec": duration,
            "peak_memory_mb": self.peak_memory_mb,
            "avg_memory_mb": avg_memory,
            "start_memory_mb": self.start_memory_mb,
            "peak_threads": self.peak_threads,
            "start_threads": self.start_threads,
            "available": HAS_PSUTIL,
        }


def get_process_memory() -> float:
    """
    Get current process memory usage in MB.

    Returns:
        float: Memory usage in MB, or 0 if unavailable
    """
    if not HAS_PSUTIL:
        return 0.0

    try:
        process = psutil.Process(os.getpid())  # type: ignore
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)
    except Exception:  # pylint: disable=broad-except
        return 0.0


def get_process_threads() -> int:
    """
    Get current process thread count.

    Returns:
        int: Thread count, or 0 if unavailable
    """
    if not HAS_PSUTIL:
        return 0

    try:
        process = psutil.Process(os.getpid())  # type: ignore
        return process.num_threads()
    except Exception:  # pylint: disable=broad-except
        return 0
