from typing import List, Optional, Tuple, Dict, Union, Literal, ClassVar
from pydantic import BaseModel, Field
from knowledge.core.schema.graph.graph import *


from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class RhetoricalItem(BaseModel):
    role: RhetoricalRole
    content: str = Field(..., description="Document content (refer exactly to the document)")
    confidence: int = Field(default=3, ge=1, le=1)

class ConceptBundle(BaseModel):
    name: str = Field(..., description="Comcept described by 3 word max (Ex: Linear Regression)")
    details: List[RhetoricalItem] = Field(default_factory=list)

class RelationEdge(BaseModel):
    name: str
    src: str
    tgt: str

class SkeletonStructure(BaseModel): # Phase 1
    tree: List[ConceptBundle]

class RelationStructure(BaseModel):# Phase 2
    edges: List[RelationEdge]



