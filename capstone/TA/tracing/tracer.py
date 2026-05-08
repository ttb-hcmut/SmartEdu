"""
AgentTracer — per-session in-memory tracer với async flush ra JSON.

Usage:
    tracer = AgentTracer(session_id="student_123")
    chat_id = tracer.begin_chat(query="What is ML?")
    tracer.log_step(chat_id, node="TA_Router", prompt="...", state={}, output="retrieve")
    tracer.log_step(chat_id, node="RAG_Core",  prompt="...", state={}, tool_result={...}, output="...")
    await tracer.end_chat(chat_id, final_output="...", intent="retrieve")

Langfuse integration:
    Activate by default if found env vars LANGFUSE_SECRET_KEY + LANGFUSE_PUBLIC_KEY.
    Otherwise silent skip (Consider it a disabled state, NOT an error).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from TA.tracing.schema import ChatTrace, StepTrace, TraceSession
from TA.tracing.writer import TraceWriter

logger = logging.getLogger(__name__)


def _serialize_student_state(state: Any) -> Dict[str, Any]:
    """
    Serialize and truncate StudentState (TypedDict) to plain dict for JSON storage.
    """
    if not state:
        return {}
    if not isinstance(state, dict):
        try:
            state = dict(state)
        except Exception:
            return {"raw": str(state)}

    result: Dict[str, Any] = {}

    # current_pos (ConceptNode)
    cp = state.get("current_pos")
    if cp is not None:
        try:
            result["current_pos"] = cp.model_dump() if hasattr(cp, "model_dump") else dict(cp)
        except Exception:
            result["current_pos"] = str(cp)

    # previous_nodes (List[ConceptNode]) — chỉ lấy 3 gần nhất
    prev = state.get("previous_nodes", [])
    result["previous_nodes"] = [
        (n.name if hasattr(n, "name") else str(n)) for n in list(prev)[:3]
    ]

    # upcoming_nodes
    upcoming = state.get("upcoming_nodes", [])
    result["upcoming_nodes"] = [
        (n.name if hasattr(n, "name") else str(n)) for n in list(upcoming)[:3]
    ]

    # mastery_map — chỉ giữ entries có value > 0
    mastery = state.get("mastery_map", {})
    if mastery:
        result["mastery_map"] = {k: v for k, v in mastery.items() if v and v > 0}

    # summary
    if state.get("summary"):
        result["summary"] = str(state["summary"])[:200]

    return result


class AgentTracer:
    """
    Per-session tracer. Mỗi TAModule.run() = 1 chat turn.
    Thread-safe: dùng in-memory dict cho buffer, flush async khi end_chat.
    """

    def __init__(self, session_id: str = "default", writer: Optional[TraceWriter] = None):
        self.session_id = session_id
        self._session = TraceSession(session_id=session_id)
        self._writer = writer or TraceWriter()
        self._active_chats: Dict[str, ChatTrace] = {}  # chat_id → ChatTrace buffer

        # Langfuse — optional, lazy init
        self._langfuse_handler = None
        self._init_langfuse()

    # ── Langfuse (optional) ───────────────────────────────────────────────

    def _init_langfuse(self):
        """Khởi tạo Langfuse CallbackHandler nếu env vars tồn tại."""
        secret = os.getenv("LANGFUSE_SECRET_KEY")
        public = os.getenv("LANGFUSE_PUBLIC_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not secret or not public:
            logger.debug("[AgentTracer] Langfuse env vars not set — skipping Langfuse init.")
            return

        try:
            from langfuse.langchain import CallbackHandler
            self._langfuse_handler = CallbackHandler(
                secret_key=secret,
                public_key=public,
                host=host,
                session_id=self.session_id,
            )
            logger.info(f"[AgentTracer] Langfuse active → host={host}")
        except ImportError:
            logger.warning("[AgentTracer] langfuse not installed. Run: pip install langfuse")
        except Exception as e:
            logger.warning(f"[AgentTracer] Langfuse init failed: {e}")

    @property
    def langfuse_handler(self):
        """Trả về Langfuse CallbackHandler để inject vào RunnableConfig callbacks."""
        return self._langfuse_handler

    # ── Chat lifecycle ────────────────────────────────────────────────────

    def begin_chat(self, query: str) -> str:
        """
        Bắt đầu một chat turn mới.
        Trả về chat_id (YYYYMMDD_HHMMSS) để dùng cho các log_step tiếp theo.
        """
        chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        chat = ChatTrace(chat_id=chat_id, query=query)
        self._active_chats[chat_id] = chat
        logger.debug(f"[AgentTracer] begin_chat: session={self.session_id} chat_id={chat_id}")
        return chat_id

    def log_step(
        self,
        chat_id: str,
        node: str,
        prompt: str = "",
        state: Any = None,
        tool_result: Optional[Dict[str, Any]] = None,
        output: str = "",
    ):
        """
        Ghi một bước suy luận vào buffer.
        Thread-safe (chỉ append vào in-memory list, không I/O).
        """
        chat = self._active_chats.get(chat_id)
        if chat is None:
            logger.warning(f"[AgentTracer] log_step: unknown chat_id={chat_id}")
            return

        step = StepTrace(
            node=node,
            prompt=prompt[:3000] if prompt else "",  # cap để tránh file quá lớn
            state=_serialize_student_state(state),
            tool_result=tool_result or {},
            output=str(output)[:2000] if output else "",
        )
        chat.agent.append(step)

    async def end_chat(
        self,
        chat_id: str,
        final_output: str = "",
        intent: str = "",
        status: str = "SUCCESS",
    ):
        """
        Kết thúc chat turn: flush buffer ra JSON file.
        Gọi sau khi SmartEdu.execute() hoàn thành.
        """
        chat = self._active_chats.pop(chat_id, None)
        if chat is None:
            logger.warning(f"[AgentTracer] end_chat: unknown chat_id={chat_id}")
            return

        chat.final_output = str(final_output)[:2000]
        chat.intent = intent
        chat.status = status

        self._session.chat.append(chat)
        path = await self._writer.write_async(self._session)
        logger.info(f"[AgentTracer] Trace saved → {path} (turn {len(self._session.chat)})")

        # Flush Langfuse telemetry data immediately if active
        if self._langfuse_handler:
            try:
                self._langfuse_handler.langfuse.flush()
            except Exception as e:
                logger.warning(f"[AgentTracer] Langfuse flush failed: {e}")

        return path
