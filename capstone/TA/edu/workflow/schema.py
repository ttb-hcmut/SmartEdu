from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from core.schema.wf_state import AgentOutput, AgentState, ConceptNode


## -- Reasoning fields FIRST for CoT generation order
## -- ai_message on UI-facing schemas only

class RAGCore(BaseModel):
    """Intermediate — no ai_message needed."""
    thought: str = Field(description="Brief reasoning about the retrieval strategy")
    entity_ids: List[str] = Field(default_factory=list, description="Resolved entity IDs from the KG")
    content: str = Field(default="", description="Synthesized content from tools")
    status: str = Field(default="SUCCESS", description="SUCCESS or FAIL")

class RAGDeep(BaseModel):
    """Intermediate — no ai_message needed."""
    thought: str = Field(description="Reasoning about the knowledge gap and bridge concepts")
    is_deep: bool = Field(description="Whether query requires deep analysis")
    bridge_concepts: List[Dict[str, Any]] = Field(default_factory=list, description="Prerequisite concepts the student needs")
    knowledge_gap_score: float = Field(default=0.0, description="0.0 = no gap, 1.0 = huge gap")

class DeepDecision(BaseModel):
    reasoning: str = Field(default="", description="Brief justification for the decision")
    decision: Literal["DEEP", "SKIP"] = Field(description="DEEP if deep analysis needed, SKIP otherwise")

class RouterDecision(BaseModel):
    intent: Literal["retrieve", "roadmap", "teaching", "confirm", "clarify"] = Field(
        description="Classified intent of the student query"
    )

## -- Roadmap schemas: UI-facing, need ai_message

class RoadmapExplore(BaseModel):
    reasoning: str = Field(description="Brief analysis of the topic and exploration strategy")
    start_node: Optional[ConceptNode] = None
    goal: str = Field(description="Learning goal extracted from query")
    steps: List[ConceptNode] = Field(default_factory=list, description="Ordered hub nodes for the path")
    ai_message: str = Field(default="", description="Natural language narrative for the student about this exploration")

class RoadmapCritique(BaseModel):
    reasoning: str = Field(description="Detailed analysis of prerequisites and cognitive load")
    is_feasible: bool = Field(description="Whether the proposed path is feasible for this student")
    ai_message: str = Field(default="", description="Natural language critique summary for downstream synthesis")

class RoadmapFinal(BaseModel):
    thought: str = Field(description="Synthesize backbone and critique into a coherent plan")
    final_steps: List[ConceptNode] = Field(default_factory=list, description="Finalized ordered steps")
    pedagogical_advice: str = Field(description="Actionable advice for the student")
    ai_message: str = Field(default="", description="Natural language roadmap narrative for the student")

## -- Teach schemas

class TeachLectureOutput(BaseModel):
    """UI-facing: lecture field IS the narrative."""
    thought: str = Field(description="Pedagogical reasoning for the lecture and question")
    lecture: str = Field(description="The lecture content to present to the student")
    challenge_question: str = Field(default="", description="A Socratic question to test understanding")

class TeachEvalOutput(BaseModel):
    """UI-facing via finish node."""
    criteria: str = Field(description="Evaluation criteria derived from session questions")
    user_eval: str = Field(description="Assessment of the student's responses")
    passed: bool = Field(description="Whether the student demonstrated sufficient mastery")
    ai_message: str = Field(default="", description="Natural language evaluation feedback for the student")

class NextTopicOutput(BaseModel):
    """Structured output for next topic selection."""
    reasoning: str = Field(description="Why these topics were selected based on eval and graph connectivity")
    selected_nodes: List[str] = Field(default_factory=list, description="Ordered list of next topic names, 1-3 max")