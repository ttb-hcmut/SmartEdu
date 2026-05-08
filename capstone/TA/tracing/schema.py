"""
Trace log schema — SmartEdu TA Agent
Version: 1.0

Output format:
{
  "schema_version": "1.0",
  "session_id": "student_123",
  "chat": [
    {
      "chat_id": "20260507_191233",
      "query": "...",
      "agent": [
        {
          "node": "TA_Router",
          "prompt": "...",
          "state": { ... },
          "tool_result": {},
          "output": "..."
        }
      ]
    }
  ]
}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepTrace(BaseModel):
    """Trace logical step: tool call, textual, though"""

    node: str = Field(description="Node name (TA_Router, RAG_Core, ...)")
    prompt: str = Field(default="", description="Prompt đưa vào LLM tại bước này")
    state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of StudentState (serialized, stringified)"
    )
    tool_result: Dict[str, Any] = Field(
        default_factory=dict,
        description="tools (worker_results snapshot)"
    )
    output: str = Field(default="", description="Raw LLM output hoặc kết quả node")


class ChatTrace(BaseModel):
    """Trace of chat turn: query → full agent execution (divided into steps) --> output --> serialized response"""

    chat_id: str = Field(description="Timestamp YYYYMMDD_HHMMSS")
    query: str = Field(description="User query")
    intent: str = Field(default="", description="Intent routered")
    agent: List[StepTrace] = Field(default_factory=list, description=" Agentic steps")
    final_output: str = Field(default="", description="Serialized response trả về user")
    status: str = Field(default="SUCCESS", description="SUCCESS | FAIL")


class TraceSession(BaseModel):
    """full state of a session"""

    schema_version: str = Field(default="1.0", description="Dùng để migrate khi schema thay đổi")
    session_id: str = Field(default="default")
    chat: List[ChatTrace] = Field(default_factory=list)
