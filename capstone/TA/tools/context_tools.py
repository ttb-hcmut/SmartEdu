"""
Context Lookup Tools — TA agent retrieves recent tool results and thoughts.
Hard-capped to prevent token OOM on small VRAM models.

Session context is injected via Python ContextVar (concurrent-safe):
  - `ta_module.run()` sets `_current_session_context` before execute
  - Tools read from it at call time — no pydantic field needed
  - Always bound to TA agent at startup; context flows in at runtime
"""

from contextvars import ContextVar
from typing import Optional, Literal, Type

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from student.session_context import SessionContext

# ── Per-request session context (async-safe ContextVar) ───────────────────────
_current_session_context: ContextVar[Optional[SessionContext]] = ContextVar(
    "current_session_context", default=None
)

_HARD_LIMIT = 5        # absolute max entries returned
_OUTPUT_CHAR_CAP = 600 # chars per entry before truncation


class RecallResultsInput(BaseModel):
    limit: int = Field(
        default=3,
        description=f"Max results to return. Hard cap: {_HARD_LIMIT}.",
    )
    agent_type: Optional[Literal["rag", "teach"]] = Field(
        default=None,
        description=(
            "Filter by agent type: 'rag' (retrieve/roadmap nodes) or "
            "'teach' (lecture nodes). Omit for all."
        ),
    )


class RecallThoughtsInput(BaseModel):
    limit: int = Field(
        default=3,
        description=f"Max thought entries to return. Hard cap: {_HARD_LIMIT}.",
    )


# Maps agent_type label → node name prefixes stored in SessionContext
_AGENT_TYPE_NODE_PREFIX = {
    "rag":   ("RAG_Core", "RAG_Deep", "Roadmap_Explore"),
    "teach": ("Teach_Lecture", "Teach_RAG", "Teach_Lookup"),
}


class RecallToolResults(BaseTool):
    name: str = "recall_tool_results"
    description: str = (
        "Retrieve the N most recent tool execution results from this session. "
        "Specify agent_type='rag' for retrieval results or 'teach' for lecture-related results. "
        "Use when synthesis data is missing. Strictly capped to avoid context overflow."
    )
    args_schema: Type[BaseModel] = RecallResultsInput

    def _run(
        self,
        limit: int = 3,
        agent_type: Optional[Literal["rag", "teach"]] = None,
    ) -> str:
        session_context = _current_session_context.get()
        if not session_context:
            return "Session context not available for this request."

        limit = min(limit, _HARD_LIMIT)
        node_prefixes = _AGENT_TYPE_NODE_PREFIX.get(agent_type) if agent_type else None
        entries = session_context.get_recent_tool_results(n=_HARD_LIMIT)

        if node_prefixes:
            entries = [e for e in entries if any(e.node.startswith(p) for p in node_prefixes)]

        entries = entries[:limit]

        if not entries:
            return "No matching tool results found in session context."

        lines = []
        for e in entries:
            out = e.output
            if len(out) > _OUTPUT_CHAR_CAP:
                out = out[:_OUTPUT_CHAR_CAP] + "...[truncated]"
            lines.append(f"[{e.node}] {e.tool_name} → {out}")

        return f"RECALLED TOOL RESULTS (last {len(lines)}):\n" + "\n---\n".join(lines)

    async def _arun(
        self,
        limit: int = 3,
        agent_type: Optional[Literal["rag", "teach"]] = None,
    ) -> str:
        return self._run(limit=limit, agent_type=agent_type)


class RecallThoughts(BaseTool):
    name: str = "recall_thoughts"
    description: str = (
        "Retrieve the N most recent agent reasoning traces from this session for self-correction. "
        "Strictly capped to avoid context overflow."
    )
    args_schema: Type[BaseModel] = RecallThoughtsInput

    def _run(self, limit: int = 3) -> str:
        session_context = _current_session_context.get()
        if not session_context:
            return "Session context not available for this request."

        limit = min(limit, _HARD_LIMIT)
        entries = session_context.get_recent_thoughts(n=limit)

        if not entries:
            return "No agent thoughts found in session context."

        lines = []
        for e in entries:
            thought = (
                e.thought[:_OUTPUT_CHAR_CAP] + "...[truncated]"
                if len(e.thought) > _OUTPUT_CHAR_CAP
                else e.thought
            )
            lines.append(f"[{e.node}|{e.status}] {thought}")

        return f"RECALLED AGENT THOUGHTS (last {len(lines)}):\n" + "\n---\n".join(lines)

    async def _arun(self, limit: int = 3) -> str:
        return self._run(limit=limit)
