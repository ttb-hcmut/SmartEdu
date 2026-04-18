from typing import List, Optional, Tuple, Dict, Union, Literal, ClassVar
from pydantic import BaseModel, Field
from core.schema.graph.graph import *


from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Skeleton frame for Graph Construction
class RhetoricalItem(BaseModel):
    role: RhetoricalRole
    content: str = Field(..., description="Document content (refer exactly to the document)")
    confidence: float = Field(default=0.7, ge=0, le=1)

class ConceptBundle(BaseModel):
    name: str = Field(..., description="Concept described by 4 word max (Ex: Linear Regression)")
    details: List[RhetoricalItem] = Field(default_factory=list)

class RelationEdge(BaseModel):
    name: str
    src: str
    tgt: str

class SkeletonStructure(BaseModel): # Phase 1
    tree: List[ConceptBundle]

class RelationStructure(BaseModel):# Phase 2
    edges: List[RelationEdge]


# Sorf link structure
class AnchorLink(BaseModel):
    anchor_id: str = Field(description="The exact ID of the candidate anchor")
    justification: str = Field(description="Brief explanation of why this textbook chunk relates to the anchor")

class AnchorLinkStructure(BaseModel):
    links: List[AnchorLink]