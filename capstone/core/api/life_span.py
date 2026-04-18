
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.llm.llm_engine import CoreLLMEngine

from core.repo.graph.graphdb import GraphDB
from core.repo.milvus_db.mil import MilvusDB
from core.model.embedding import Embedder
from core.repo.storage.minio_repo import MinioDB

from knowledge.knowledge_construction_service import KnowledgeModule
from TA.ta_module import TAModule, TA_service
from core.config import *

@asynccontextmanager
async def lifespan(app: FastAPI):

    llm = CoreLLMEngine()
    graph_db = GraphDB(config = Neo())
    milvus_db = MilvusDB(config=Mil_conf())
    embedder = Embedder(config=Emb_conf())
    minio_repo = MinioDB(config = Minio_conf())

    mongo = None
    sql = None

    knowledge_mod = KnowledgeModule(
        llm=llm, 
        graph_db=graph_db, 
        milvus_db=milvus_db, 
        embedder=embedder, 
        minio_repo=minio_repo,
        config= K_conf()
    )
    app.state.knowledge = knowledge_mod
    
    TA = TAModule(
        llm=llm, 
        graph_db=graph_db, 
        milvus_db=milvus_db, 
        embedder=embedder, 
        minio=minio_repo,
        mongo_db=mongo,
        sql_db= sql,
        config= TA_conf()
    )
    app.state.TA = TA
    yield
    
    # --- SHUTDOWN ---
    knowledge_mod.close()
    TA.close()