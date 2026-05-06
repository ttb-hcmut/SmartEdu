from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Prep layer
PAGE_PER_PDF = 15

# App Layer
DB_NAME = os.getenv("NEO4J_DB_NAME", "test")

@dataclass
class App_settings:
    name = "Capstone Gateway"
    endpoint = "/internal/v1/knowledge"
    port = 8001


# Knowledge Module
## Logic Layer
@dataclass
class K_conf:
    profile_name = "graph"

@dataclass
class Ingest_param:
    path = "data/"
    PAGE_PER_TB = 10
    PAGE_PER_SLIDE = 15

### Infratructure Layer
@dataclass
class Mil_conf:
    collection_name = os.getenv("MILVUS_COLLECTION", DB_NAME)
    uri: str = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    dim: int = 768
    retries = 5
    delay = 15

@dataclass
class Emb_conf:
    model_name: str = os.getenv("EMBEDDING_MODEL", 'allenai/scibert_scivocab_uncased')
    dim: int = 768
    retries = 5
    max_token = 512
    
@dataclass
class Neo:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASS", "graph123"))
    db_name = os.getenv("NEO4J_DB_NAME", DB_NAME)

@dataclass
class Minio_conf:
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

@dataclass
class Mongo_conf:
    uri = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", DB_NAME)

# TA module
## Logic Layer

from core.llm.prompt.agents import RAG_PROMPT, TA_PROMPT, GEN_PROMPT,EVAL_PROMPT
from core.schema.wf_state import RAGOutput
class TA_conf:
    AGENTS = [("TA",TA_PROMPT,None ) , 
             ("Generator", GEN_PROMPT, None), 
             ("RAG", RAG_PROMPT, RAGOutput)
             ]
# ("Evaluator", EVAL_PROMPT, None)
@dataclass
class TA_serv:
    model_type: str = "ta"


from enum import Enum
@dataclass
class Bloom(Enum):
    """ Bloom's Taxonomy levels """
    REMEMBER = 1
    UNDERSTAND = 2
    APPLY = 3
    ANALYZE = 4
    EVALUATE = 5
    CREATE = 6

NeoStudent = Neo(db_name = "students")

# Student logic

