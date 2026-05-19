"""
SessionContext — per-session in-memory context store.

Lưu tool results và agent thoughts theo từng chat turn.
Persist vào MongoDB để dùng lại giữa các turns trong cùng phiên.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class ToolResultEntry:
    tool_name: str
    args: Dict[str, Any]
    output: str
    node: str
    chat_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ThoughtEntry:
    node: str
    thought: str
    status: str
    chat_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SessionContext:
    """
    In-memory context store per chat session.
    - tool_results: {chat_id: [ToolResultEntry]}
    - thoughts:     {chat_id: [ThoughtEntry]}
    Auto-evicts oldest chat turns when > max_turns.
    """

    def __init__(self, session_id: str, max_turns: int = 10):
        self.session_id = session_id
        self.max_turns = max_turns
        # Ordered list of chat_ids to track eviction order
        self._chat_order: List[str] = []
        self.tool_results: Dict[str, List[ToolResultEntry]] = {}
        self.thoughts: Dict[str, List[ThoughtEntry]] = {}

    # ── Write ─────────────────────────────────────────────────────────────

    def store_tool_result(
        self,
        chat_id: str,
        tool_name: str,
        args: Dict[str, Any],
        output: str,
        node: str,
    ) -> None:
        self._ensure_chat(chat_id)
        self.tool_results[chat_id].append(
            ToolResultEntry(
                tool_name=tool_name, args=args, output=output,
                node=node, chat_id=chat_id
            )
        )

    def store_thought(
        self, chat_id: str, node: str, thought: str, status: str = "SUCCESS"
    ) -> None:
        self._ensure_chat(chat_id)
        self.thoughts[chat_id].append(
            ThoughtEntry(node=node, thought=thought, status=status, chat_id=chat_id)
        )

    # ── Read ──────────────────────────────────────────────────────────────

    def get_recent_tool_results(
        self, n: int = 3, tool_filter: Optional[str] = None
    ) -> List[ToolResultEntry]:
        """Return last n tool results across all turns, newest first."""
        all_results: List[ToolResultEntry] = []
        for chat_id in reversed(self._chat_order):
            for entry in reversed(self.tool_results.get(chat_id, [])):
                if tool_filter and entry.tool_name != tool_filter:
                    continue
                all_results.append(entry)
                if len(all_results) >= n:
                    return all_results
        return all_results

    def get_recent_thoughts(self, n: int = 3) -> List[ThoughtEntry]:
        """Return last n thoughts across all turns, newest first."""
        all_thoughts: List[ThoughtEntry] = []
        for chat_id in reversed(self._chat_order):
            for entry in reversed(self.thoughts.get(chat_id, [])):
                all_thoughts.append(entry)
                if len(all_thoughts) >= n:
                    return all_thoughts
        return all_thoughts

    def format_recent_tool_results(
        self, n: int = 3, tool_filter: Optional[str] = None
    ) -> str:
        entries = self.get_recent_tool_results(n=n, tool_filter=tool_filter)
        if not entries:
            return "No recent tool results found."
        lines = []
        for e in entries:
            out = e.output[:800] + "..." if len(e.output) > 800 else e.output
            lines.append(f"[{e.node}] {e.tool_name}({e.args}) → {out}")
        return "\n---\n".join(lines)

    def format_recent_thoughts(self, n: int = 3) -> str:
        entries = self.get_recent_thoughts(n=n)
        if not entries:
            return "No recent agent thoughts found."
        lines = []
        for e in entries:
            lines.append(f"[{e.node}|{e.status}] {e.thought}")
        return "\n---\n".join(lines)

    # ── Serialization (MongoDB) ────────────────────────────────────────────

    def to_dict(self) -> Dict:
        return {
            "tool_results": {
                cid: [vars(e) for e in entries]
                for cid, entries in self.tool_results.items()
            },
            "thoughts": {
                cid: [vars(e) for e in entries]
                for cid, entries in self.thoughts.items()
            },
            "chat_order": self._chat_order,
        }

    @classmethod
    def from_dict(cls, session_id: str, data: Dict, max_turns: int = 10) -> "SessionContext":
        ctx = cls(session_id=session_id, max_turns=max_turns)
        ctx._chat_order = data.get("chat_order", [])
        for cid, entries in data.get("tool_results", {}).items():
            ctx.tool_results[cid] = [ToolResultEntry(**e) for e in entries]
        for cid, entries in data.get("thoughts", {}).items():
            ctx.thoughts[cid] = [ThoughtEntry(**e) for e in entries]
        return ctx

    # ── Private ───────────────────────────────────────────────────────────

    def _ensure_chat(self, chat_id: str) -> None:
        if chat_id not in self.tool_results:
            self.tool_results[chat_id] = []
            self.thoughts[chat_id] = []
            self._chat_order.append(chat_id)
            self._evict()

    def _evict(self) -> None:
        while len(self._chat_order) > self.max_turns:
            old_id = self._chat_order.pop(0)
            self.tool_results.pop(old_id, None)
            self.thoughts.pop(old_id, None)
