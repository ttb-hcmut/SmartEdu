from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Union, Literal
from enum import Enum

# ================= BASE FOR GRAPH ========================
class Ref(BaseModel):
    db: str = ""
    id: str
    name: str
    summary : str = ""


class BaseNode(BaseModel):
    id : str = ""
    name: str
    content: str = ""
    hard_ref: Optional[Ref] = None
    weight: float = 1.0
    soft_ref: List[Ref] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)



class RhetoricalRole(str, Enum):
    DEFINITION = "Definition"       
    FORMULA = "Formula"
    OBJECTIVE = "Objective"
    
    PROBLEM = "Problem"             
    SOLUTION = "Solution"           
    PROOF = "Proof"                 
    
    APPPLICATION = "Application"
    EXPERIMENT = "Experiment"  
    STATEMENT = "Statement"

class NodeType(str, Enum):
    COMMUNITY = "Community"
    TOPIC = "Topic"
    CONCEPT = "Concept"
    RHETORICAL = "Rhetorical"





    