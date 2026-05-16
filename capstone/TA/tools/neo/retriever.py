import requests
import asyncio
from typing import Type, Optional
from pydantic import BaseModel
from langchain.tools import BaseTool
from TA.tools.neo.base import *
from TA.tools.neo.schema import *
from knowledge.engine.graph.helper.normalize import wiki_resolver


class EntityFinder(NeoTool):
    name: str = "entity_finder"
    description: str = "Resolve entity names to IDs using internal graph or Wikidata fallback."

    def _run(self, query: str):
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str):
        print("Run ", self.name, " with query: ", query)
        wiki_results = await wiki_resolver([query])
        wiki_data = wiki_results.get(query, {})
        wiki_id = wiki_data.get("id")
        print("wiki: ", wiki_id)
        
        cypher = """
        MATCH (n:Entity) 
        WHERE n.id = $wiki_id 
           OR toLower(n.name) = toLower($query)
           OR n.id = $query
        RETURN n.id AS id, n.name AS name LIMIT 1
        """
        params = {"wiki_id": wiki_id if wiki_id else "NO_WIKI_ID", "query": query}
        res = self.run_query(query=cypher, params=params)

        print("Ent finder: ", res)
        if res:
            return f"SUCCESS: Found Entity '{res[0]['name']}' with ID '{res[0]['id']}'. Use this ID for other tools."
        return f"ERROR: Entity '{query}' not found in internal knowledge graph."

class RhetoricalRetriever(NeoTool):
    name: str = "rhetorical_retriever"
    description: str = "Retrieve educational content using Node ID and rhetorical role."
    args_schema: Type[BaseModel] = ContentInput

    def _run(self, node_id: str, role: Optional[str] = None, limit: int = 5):
        print(f"Run {self.name} with role {role} limit {limit}")
        if role:
            cypher = """
            MATCH (n:Entity {id: $id})-[:CONTENT]->(c:Entity)
            WHERE toLower(c.rrole) = toLower($role)
            RETURN c.rrole AS role, c.content AS content LIMIT $limit
            """
            params = {"id": node_id, "role": role, "limit": limit}
        else:
            cypher = """
            MATCH (n:Entity {id: $id})-[:CONTENT]->(c:Entity)
            RETURN c.rrole AS role, c.content AS content LIMIT $limit
            """
            params = {"id": node_id, "limit": limit}

        results = self.run_query(cypher, params)
        print("Result: ", results)
        
        if not results:
            role_msg = f" for role '{role}'" if role else ""
            return f"INFO: No content found{role_msg} on node {node_id}."
        
        content_text = "\n".join([f"- [{r['role']}] {r['content']}" for r in results])
        role_msg = f" ({role})" if role else " (ALL)"
        return f"SOURCE_DATA{role_msg} for {node_id}:\n{content_text}"

    async def _arun(self, node_id: str, role: Optional[str] = None, limit: int = 5):
        return self._run(node_id, role, limit)
    
class EdgeExplorer(NeoTool):
    name: str = "edge_explorer"
    description: str = "Explore multi-hop relationships (excluding CONTENT edges)."
    

    def _run(self, node_id: str):
        print("Run ", self.name , " with node_id: ", node_id)
        cypher = """
        MATCH (n:Entity {id: $id})
        OPTIONAL MATCH path = (n)-[r*1..2]-(m:Entity)
        WHERE ALL(rel IN relationships(path) WHERE type(rel) <> 'CONTENT')
          AND m.id <> $id AND m.rrole IS NULL
        WITH n, m, path
        LIMIT 20
        RETURN 
            m.name as name, 
            m.id as id, 
            type(relationships(path)[0]) as rel_type,
            CASE WHEN startNode(relationships(path)[0]) = n THEN 'OUTGOING' ELSE 'INCOMING' END as direction,
            length(path) as distance
        """
        results = self.run_query(cypher, {"id": node_id})
        print(results)
        
        if not results or not any(r['id'] for r in results):
            return f"INFO: No semantic relationships found for ID {node_id}."

        in_rels = []
        out_rels = []
        for r in results:
            if not r['id']: continue
            line = f"- {r['name']} (ID: {r['id']}) via {r['rel_type']}"
            if r['distance'] > 1: line += f" ({r['distance']} hops)"
            
            if r['direction'] == 'INCOMING':
                in_rels.append(line)
            else:
                out_rels.append(line)

        output = [f"Semantic Connections for {node_id}:"]
        if in_rels:
            output.append("\nPARENT/CONTEXT CONCEPTS (Incoming):")
            output.extend(in_rels)
        if out_rels:
            output.append("\nRELATED/SUB CONCEPTS (Outgoing):")
            output.extend(out_rels)

        return "\n".join(output)

    async def _arun(self, node_id: str):
        print("aaaaa")
        return self._run(node_id)