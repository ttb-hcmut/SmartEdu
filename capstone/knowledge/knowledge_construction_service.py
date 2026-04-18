from knowledge.service.course_ingest import CourseIngestionService
from core.dependencies import *
from core.config import K_conf

class KnowledgeModule:
    def __init__(self, llm, graph_db, milvus_db, embedder, minio_repo, config =K_conf ):
        self.llm = llm
        self.graph_db = graph_db
        self.milvus_db = milvus_db
        self.embedder = embedder
        self.minio_repo = minio_repo

    def get_ingestion_service(self) -> CourseIngestionService:
        return CourseIngestionService(
            llm=self.llm,
            graph_db=self.graph_db,
            milvus_db=self.milvus_db,
            minio_repo=self.minio_repo,
            embedder=self.embedder
        )
    def close(self):
        self.graph_db.close()
        self.milvus_db.close()