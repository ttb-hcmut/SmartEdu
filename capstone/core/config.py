from dataclasses import dataclass, field

# Prep layer
PAGE_PER_PDF = 15

# App Layer

DB_NAME = "final"

@dataclass
class App_settings:
    name = "Capstone Gateway"
    endpoint = "/internal/v1/knowledge"
    port = 8001


# Knowledge Module
## Logic Layer
@dataclass
class K_conf:
    profile_name = "deep"

@dataclass
class Ingest_param:
    path = "data/"

### Infratructure Layer
@dataclass
class Mil_conf:
    collection_name = DB_NAME
    uri: str = "http://127.0.0.1:19530"
    dim: int = 768
    retries = 5
    delay = 15

@dataclass
class Emb_conf:
    model_name: str = 'allenai/scibert_scivocab_uncased'
    dim: int = 768
    retries = 5
    max_token = 512
    
@dataclass
class Neo:
    uri="bolt://localhost:7687"
    auth=("neo4j", "graph123")
    db_name = DB_NAME

@dataclass
class Minio_conf:
    endpoint="localhost:9000"
    access_key="minioadmin"
    secret_key="minioadmin"
    
    secure: bool = False

# TA module
## Logic Layer
@dataclass
class TA_conf:
    profile_name = "deep"

@dataclass
class TA_serv:
    model_type: str = "ta"