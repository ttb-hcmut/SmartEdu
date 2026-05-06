from core.llm.llm_engine import CoreLLMEngine
from core.repo.graph.graphdb import GraphDB
from core.repo.milvus_db.mil import MilvusDB
from core.model.embedding import Embedder
from core.repo.storage.minio_repo import MinioDB
from fastapi import Request
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends

from knowledge.service.course_ingest import CourseIngestionService
from knowledge.knowledge_construction_service import KnowledgeModule


from TA.ta_module import TAModule


# Legacy code, new update gather it under 1 module
"""
def get_minio_repo(request: Request) -> MinioDB:
    return request.app.state.minio_repo

def get_llm_engine(request: Request) -> CoreLLMEngine:
    return request.app.state.llm_engine

def get_graph_db(request: Request) -> GraphDB:
    return request.app.state.graph_db

def get_milvus_db(request: Request) -> MilvusDB:
    return request.app.state.milvus_db

def get_embedder(request: Request) -> Embedder:
    return request.app.state.embedder

"""



def get_knowledge_module(request: Request) ->KnowledgeModule:
    return request.app.state.knowledge # Safe management module only

def get_ingestion_service(module: KnowledgeModule  = Depends(get_knowledge_module)) -> CourseIngestionService:
    return module.get_ingestion_service()



def get_TA_module(request: Request) ->TAModule:
    return request.app.state.TA

