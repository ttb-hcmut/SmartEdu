from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Union, Literal
from enum import Enum

# ================= BASE FOR GRAPH ========================
class Ref(BaseModel):
    db: str = ""
    id: str
    name: str
    summary : str = ""
    p_num : Tuple[int, int] = (1, 1)  


class BaseNode(BaseModel):
    id : str = ""
    name: str
    content: str = ""
    hard_ref: Optional[Ref] = None
    weight: float = 1.0
    soft_ref: List[Ref] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)



class RhetoricalRole(str, Enum):
    FORMULA = "Formula"
    OBJECTIVE = "Objective"
    
    PROBLEM = "Problem"             
    SOLUTION = "Solution"           
    PROOF = "Proof"                 
    
    APPLICATION = "Application"
    EXPERIMENT = "Experiment"  
    STATEMENT = "Statement"

    QUIZ = "Quiz"
    
    DEFINITION = "Definition"
    THEOREM = "Theorem"

class NodeType(str, Enum):
    COMMUNITY = "Community"
    TOPIC = "Topic"
    CONCEPT = "Concept"
    RHETORICAL = "Rhetorical"


class EdgeType(str, Enum):
    PART_OF = "PART_OF"
    RELATED_TO = "RELATED_TO"
    PREREQUISITE_OF = "PREREQUISITE_OF"
    
    




    