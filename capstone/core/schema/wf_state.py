from collections import deque
from typing import Annotated, TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class ConceptNode(BaseModel):
    name: str = Field(description="Concept name")
    type: str = Field(default="", description="Node type (Concept, Method, etc)")
    course_name: str = Field(default="", description="Course this concept belongs to")
    out_degree: int = Field(default=0, description="Semantic out-degree (connection count)")
    description: str = Field(default="", description="First 50 chars of node content")
    mastery: int = Field(default=0, description="Student mastery level (0-6, Bloom's)")


class LearningProposal(BaseModel):
    type: Literal["roadmap", "advance", "bridge"] = "advance"
    new_current: Optional[ConceptNode] = None
    new_upcoming: List[ConceptNode] = Field(default_factory=list)
    reason: str = ""
    source_wf: str = ""
    auto_apply: bool = False


class StudentState(TypedDict):
    finished_communities: List[ConceptNode]
    current_pos: ConceptNode
    summary: str
    mastery_map: Dict[str, float]
    previous_nodes: List[ConceptNode]
    upcoming_nodes: List[ConceptNode]
    active_resource: Optional[str]
    pending_proposal: Optional[Dict[str, Any]]

class AgentOutput(BaseModel):
    thought: str = Field(description="Summary of agent thought when deciding on the stratergy")
    status: str = Field(default="SUCCESS", description="SUCCESS | FAIL | NEED_INFO")

class TAOutput(BaseModel):
    summary: str = Field(description="Short summary for memo heading")
    message: str = Field(description="Full message shown to user")

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    student_state: StudentState 
    intent: str
    status_flag: str
    worker_results: Dict[str, AgentOutput]
    user_query: str
    pending_proposal: Optional[Dict[str, Any]]
    _teach_mode: str
    _teach_context: Dict[str, Any]

"""
class BridgeConcept(BaseModel):
    id: str = Field(description="ID của node trong Neo4j")
    name: str = Field(description="Tên khái niệm (VN - EN - VN)")
    mastery: int = Field(description="Mức độ thông thạo hiện tại của sinh viên (0 - 6)")
    topic_id : Optional[str] = ""
    community_id: Optional[str] = ""
    
class RAGOutput(AgentOutput):
    entity_ids: List[str] = Field(default_factory=list, description="Thực thể chính được trích xuất từ query")
    content: str  = Field(description="Content của entity")
    bridge_concepts: List[BridgeConcept] = Field(default_factory=list)
    thought: Optional[str] = Field("", description="Tóm tắt suy nghĩ agent")
    is_deep: Optional[bool] = Field(False,description="Agents decided whether it is deep analysis")
    knowledge_gap_score: float = Field(0.0, description="")
"""




