"""
Thread-safe JSON writer cho agent trace logs.
Output: test/TA/{session_id}.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Optional

from TA.tracing.schema import TraceSession

logger = logging.getLogger(__name__)

# Root output directory 
_DEFAULT_LOG_DIR = Path(__file__).resolve().parents[3] / "test" / "TA"


class TraceWriter:
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or _DEFAULT_LOG_DIR
        self._thread_lock = threading.Lock()
        self._async_lock: Optional[asyncio.Lock] = None

    def _get_async_lock(self) -> asyncio.Lock:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    def _resolve_path(self, session_id: str) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        return self.log_dir / f"{session_id}.json"

    def write_sync(self, session: TraceSession) -> Path:
        """TraceSession to JSON (blocking)."""
        path = self._resolve_path(session.session_id)
        payload = session.model_dump()
        with self._thread_lock:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        logger.debug(f"[TraceWriter] Written: {path}")
        return path

    # ── Async write ───────────────────────────────────────────────────────

    async def write_async(self, session: TraceSession) -> Path:
        """Async-safe write. Used in multi-thread context."""
        async with self._get_async_lock():
            # Offload blocking I/O ra thread pool
            loop = asyncio.get_event_loop()
            path = await loop.run_in_executor(
                None, self.write_sync, session
            )
        return path
