from typing import Any, Optional
from pydantic import Field
from langchain.tools import BaseTool
from core.repo.graph.graphdb import GraphDB
from student.Student_Tracker import Student_Tracker


class NeoTool(BaseTool):
    """Base class for Neo4j tools."""
    db_name: str = "test"
    tracker: Student_Tracker = Field(exclude=True)
    engine: GraphDB = Field(exclude=True)

    def _run(self, query: str):
        return self.run_query(query)

    def run_query(self, query, params=None):
        return self.engine.run_query(self.db_name, query, params)
