from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List
from neo4j import GraphDatabase
from knowledge.repo.graph.graphdb import GraphDB

class NeoTool(BaseTool):
    """Base class for Neo4j"""
    db_name: str = "test"
    engine: GraphDB
    def _run(self, query: str):
        return self.run_query(query)

    def run_query(self, query, params=None):
        return self.engine.run_query(self.db_name, query, params)
        
class EntityInput(BaseModel):
    entity_name: str = Field(description="Name of entity")

class ContentInput(BaseModel):
    node_id: str = Field(description="ID")
    role: str = Field(description="Rhetorical Role: Definition, Example, Objective, Problem, Statement")

class ExplorerInput(BaseModel):
    node_id: str = Field(description="ID của node gốc để tìm kiếm các thực thể liên quan qua các cạnh.")