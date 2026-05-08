from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from core.schema.wf_state import AgentOutput, AgentState, ConceptNode



class RAGCore(BaseModel):
    thought: str = Field(description="Brief reasoning about the retrieval strategy")
    entity_ids: List[str] = Field(default_factory=list, description="Resolved entity IDs from the KG")
    content: str = Field(default="", description="Synthesized content from tools")
    status: str = Field(default="SUCCESS", description="SUCCESS or FAIL")

class RAGDeep(BaseModel):
    is_deep: bool = Field(description="Whether query requires deep analysis")
    bridge_concepts: List[Dict[str, Any]] = Field(default_factory=list, description="Prerequisite concepts the student needs")
    knowledge_gap_score: float = Field(default=0.0, description="0.0 = no gap, 1.0 = huge gap")

class TeachEvalOutput(BaseModel):
    """Structured eval — only used in Teach_Evaluate node."""
    criteria: str = Field(description="Evaluation criteria derived from session questions")
    user_eval: str = Field(description="Assessment of the student's responses")
    passed: bool = Field(description="Whether the student demonstrated sufficient mastery")

class DeepDecision(BaseModel):
    decision: Literal["DEEP", "SKIP"] = Field(description="DEEP if deep analysis needed, SKIP otherwise")
    reasoning: str = Field(default="", description="Brief justification for the decision")

class RoadmapExplore(BaseModel):
    start_node: Optional[ConceptNode] = None
    goal: str
    steps: List[ConceptNode]
    reasoning: str

class RoadmapCritique(BaseModel):
    is_feasible: bool
    reasoning: str

class RoadmapFinal(BaseModel):
    final_steps: List[ConceptNode]
    pedagogical_advice: str

class RouterDecision(BaseModel):
    intent: Literal["retrieve", "roadmap", "teaching", "confirm", "clarify"] = Field(
        description="Classified intent of the student query"
    )

class TeachLectureOutput(BaseModel):
    """Structured output from Teach_Lecture node."""
    lecture: str = Field(description="The lecture content to present to the student")
    challenge_question: str = Field(default="", description="A Socratic question to test understanding")