from typing import List, Optional, Tuple, Dict, Union, Literal
from pydantic import BaseModel, Field, model_validator

from core.schema.graph.type import * # --- NODE MODELS ---

class TopicNode(BaseNode):
    typeNode: Literal[NodeType.TOPIC] = NodeType.TOPIC

class CommunityNode(BaseNode):
    typeNode: Literal[NodeType.COMMUNITY] = NodeType.COMMUNITY
    description: str = ""

class ConceptNode(BaseNode):
    typeNode: Literal[NodeType.CONCEPT] = NodeType.CONCEPT
    content : str =""

class RhetoricalNode(BaseNode):
    concept_id : str
    typeNode: Literal[NodeType.RHETORICAL] = NodeType.RHETORICAL
    rrole: RhetoricalRole
    content: str = Field(..., description="Detailed content.")
    score: float = Field(default=0, description="Pruning ")

EduNode = Union[ConceptNode, TopicNode, CommunityNode, RhetoricalNode]

class EduEdge(BaseModel):
    source: EduNode
    target: EduNode
    relationship: str = ""
    name: str = Field(default="") 
    type : str = Field(default="") 
    weight: float = 1.0
    hard_ref: Optional[str] = None 
    soft_ref: Optional[str] = None

    

