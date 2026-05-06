from typing import Any, Optional
from pydantic import Field
from langchain.tools import BaseTool
from core.repo.graph.graphdb import GraphDB
from core.config import NeoStudent


class NeoTool(BaseTool):
    """Base class for Neo4j tools."""
    db_name: str = "test"
    tracker: Optional[Any] = Field(default=None, exclude=True)
    engine: GraphDB = GraphDB(config=NeoStudent)

    def _run(self, query: str):
        return self.run_query(query)

    def run_query(self, query, params=None):
        return self.engine.run_query(self.db_name, query, params)
