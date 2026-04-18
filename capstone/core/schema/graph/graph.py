from typing import List, Optional, Tuple, Dict, Union, Literal, ClassVar
from pydantic import BaseModel, Field
from core.schema.graph.ontology import * # --- CORE ONTOLOGY TO CONSTRUCT GRAPH ---

class ClusterType(str, Enum):
    SOURCE = "Source"       # Toàn bộ tài liệu
    TOPIC = "Topic"         # Một Slide hoặc một Chương 
    SEMANTIC = "Semantic"   # AI tự gom (Leiden/K-Means)

# ---  CLUSTER MODEL ---
class Cluster(BaseModel):
    id: str 
    label: str
    type: ClusterType
    
    anchor_node: Optional[str] = Field(default=None, description="Name and ID of the TopicNode governing this cluster")
    
    centroid: Optional[List[float]] = None
    member_ids: List[str] = Field(default_factory=list) 
    metadata: Dict[str, str] = Field(default_factory=dict)


# --- KG MODEL ---

class KG_Instance(BaseModel):
    nodes: Dict[str, EduNode] = Field(default_factory=dict)
    edges: Dict[Tuple[str, str, str], EduEdge] = Field(default_factory=dict)
    clusters: Dict[str, Cluster] = Field(default_factory=dict)
    
    PRUNING_THRESHOLD: ClassVar[float] = 0.2 

    