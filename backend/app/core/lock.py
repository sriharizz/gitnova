# backend/app/core/lock.py
"""
GitNova Ingestion Concurrency Lock

Ensures strictly ONE canonical ingestion job executes at a time.
Prevents multiple background processes from competing for LLM rate limits,
embedding resources, or Supabase write locks.
"""

import os
import sys
import time
import atexit
from typing import Optional

LOCK_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ingestion.lock")


class IngestionLockError(Exception):
    """Raised when an ingestion job attempts to start while another job holds the lock."""
    pass


class IngestionLock:
    """
    File-based process lock for GitNova ingestion pipelines.
    Guarantees mutual exclusion across standalone CLI runs, background jobs, and cron workers.
    """

    def __init__(self, lock_path: str = LOCK_FILE_PATH, timeout_seconds: int = 0):
        self.lock_path = lock_path
        self.timeout_seconds = timeout_seconds
        self.is_acquired = False

    def acquire(self) -> bool:
        """
        Attempts to acquire the lock.
        Returns True if acquired. Raises IngestionLockError if held by an active process.
        """
        start_time = time.time()
        while True:
            if os.path.exists(self.lock_path):
                # Inspect existing lock
                try:
                    with open(self.lock_path, "r") as f:
                        content = f.read().strip()
                    parts = content.split(":")
                    if len(parts) >= 2:
                        pid = int(parts[0])
                        created_at = float(parts[1])
                        
                        # Check if process is still alive (Windows/POSIX)
                        if not self._is_pid_running(pid):
                            print(f"⚠️ IngestionLock: Removing stale lock from dead PID {pid}.")
                            self._force_release()
                        elif (time.time() - created_at) > 3600:  # 1 hour stale cutoff
                            print(f"⚠️ IngestionLock: Lock held by PID {pid} exceeded 1h timeout. Overriding stale lock.")
                            self._force_release()
                except Exception:
                    pass

            # Attempt atomic creation
            try:
                # O_CREAT | O_EXCL is atomic across OS processes
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(f"{os.getpid()}:{time.time()}:{sys.argv}")
                self.is_acquired = True
                atexit.register(self.release)
                return True
            except FileExistsError:
                if self.timeout_seconds <= 0 or (time.time() - start_time) >= self.timeout_seconds:
                    with open(self.lock_path, "r") as f:
                        holder_info = f.read().strip()
                    raise IngestionLockError(
                        f"Ingestion already in progress! Lock held by process: {holder_info}. "
                        f"Refusing to spawn duplicate ingestion."
                    )
                time.sleep(1.0)

    def release(self) -> None:
        """Releases the lock safely if owned by the current process."""
        if self.is_acquired and os.path.exists(self.lock_path):
            try:
                with open(self.lock_path, "r") as f:
                    content = f.read().strip()
                if content.startswith(f"{os.getpid()}:"):
                    os.remove(self.lock_path)
            except Exception:
                pass
            finally:
                self.is_acquired = False

    def _force_release(self) -> None:
        try:
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
        except Exception:
            pass

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        """Checks if a process ID is currently alive on the host system."""
        if pid <= 0:
            return False
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if h_process:
                kernel32.CloseHandle(h_process)
                return True
            return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
