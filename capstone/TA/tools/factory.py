from typing import List
from TA.tools.neo.retriever import EntityFinder, RhetoricalRetriever, EdgeExplorer
from TA.tools.neo.explore import RecommendNew, CourseBackbone, CourseRelevance, OptimalPath
from TA.tools.minio.pdf_tools import GetConcept, GetPages, FEToPage

from core.repo.graph.graphdb import GraphDB


class ToolFactory:
    def __init__(self, graph_db: GraphDB, milvus_db, embedder, minio, tracker=None):
        self.graph_db = graph_db
        self.milvus_db = milvus_db
        self.embedder = embedder
        self.minio = minio
        self.tracker = tracker

        self.agent_tools = {
            "RAG": self.get_retrieve_tools,
            "TA": self.get_teach_tools,
            "Generator": lambda: []
        }

    def get_retrieve_tools(self) -> List:
        return [
            EntityFinder(engine=self.graph_db),
            RhetoricalRetriever(engine=self.graph_db),
            EdgeExplorer(engine=self.graph_db),
            RecommendNew(engine=self.graph_db, tracker=self.tracker),
            CourseBackbone(engine=self.graph_db, tracker=self.tracker),
            CourseRelevance(engine=self.graph_db),
            OptimalPath(engine=self.graph_db, tracker=self.tracker),
        ]

    def get_teach_tools(self) -> List:
        return [
            GetConcept(engine=self.graph_db),
            GetPages(minio=self.minio),
            FEToPage()
        ]
    
    def get_tools(self, agent_name: str):
        if agent_name not in self.agent_tools:
            print(f"Unknown agent: {agent_name}")
            return []
        return self.agent_tools[agent_name]()