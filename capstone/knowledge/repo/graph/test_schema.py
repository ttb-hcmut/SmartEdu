from pydantic import BaseModel, Field
from typing import List,Optional, Tuple, Set

class Graph(BaseModel):
    source : str 
    entities: Set[str] = Field(
        ..., description="All entities including additional ones from response"
    )
    edges: Set[str] = Field(..., description="All edges")
    relations: Set[Tuple[str, str, str]] = Field(
        ..., description="List of (subject, predicate, object) triples"
    )
    entity_clusters: Optional[dict[str, Set[str]]] = None
    edge_clusters: Optional[dict[str, Set[str]]] = None

