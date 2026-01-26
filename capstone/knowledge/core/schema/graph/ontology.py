from typing import List, Optional, Tuple, Dict, Union, Literal
from pydantic import BaseModel, Field, model_validator

from knowledge.core.schema.graph.type import * # --- NODE MODELS ---

class TopicNode(BaseNode):
    typeNode: Literal[NodeType.TOPIC] = NodeType.TOPIC

class CommunityNode(BaseNode):
    typeNode: Literal[NodeType.COMMUNITY] = NodeType.COMMUNITY
    description: str = ""

class ConceptNode(BaseNode):
    typeNode: Literal[NodeType.CONCEPT] = NodeType.CONCEPT
    content : str =""
# [FIX]: Kế thừa BaseNode để có ID và validate được trong Union

class RhetoricalNode(BaseNode):
    typeNode: Literal[NodeType.RHETORICAL] = NodeType.RHETORICAL
    rrole: RhetoricalRole
    content: str = Field(..., description="Nội dung chi tiết (Markdown/Latex)")
    score: int = Field(default=0, description="Dùng cho thuật toán Pruning (Top-K)")

EduNode = Union[ConceptNode, TopicNode, CommunityNode, RhetoricalNode]

class EduEdge(BaseModel):
    source: EduNode
    target: EduNode
    
    name: str = Field(default="") 
    
    weight: float = 1.0
    hard_ref: Optional[str] = None 
    soft_ref: Optional[str] = None

    @model_validator(mode='after')
    def validate_topology_and_name(self):
        s = self.source
        t = self.target
        
        if isinstance(s, RhetoricalNode):
            self.name = f"{t.rrole.value.upper()}_ref_{t.name}"

        if isinstance(t, RhetoricalNode):
            self.name = f"{s.name}-{t.rrole.value.upper()}"
            
        return self


