import requests
from typing import Type, Optional
from pydantic import BaseModel
from langchain.tools import BaseTool

from TA.tools.neo.base import *

class EntityFinder(NeoTool):
    name: str = "entity_finder"
    description: str = "Resolve entity names using Wikipedia to get Q-ID, then verify in the internal graph."

    def _get_wikidata_id(self, query: str) -> Optional[str]:
        url = "https://en.wikipedia.org/w/api.php"
        params = {"action": "query", "prop": "pageprops", "titles": query, "format": "json", "redirects": 1}
        try:
            response = requests.get(url, params=params).json()
            pages = response.get("query", {}).get("pages", {})
            for pid in pages:
                return pages[pid].get("pageprops", {}).get("wikibase_item")
        except:
            return None
        return None

    def _run(self, query: str):
        wiki_id = self._get_wikidata_id(query)
        
        if wiki_id:
            cypher = "MATCH (n:Entity {id: $value}) RETURN n.id AS id, n.name AS name LIMIT 1"
            res = self.run_query(cypher, {"value": wiki_id})
            if res: return {"source": "wiki_bridge", "status": "SUCCESS", "data": res[0]}

        cypher = "MATCH (n:Entity {name: $value}) RETURN n.id AS id, n.name AS name LIMIT 1"
        res = self.run_query(cypher, {"value": query})
        if res: return {"source": "graph_fallback", "status": "SUCCESS", "data": res[0]}

        return f"ERROR: Entity '{query}' not found in internal knowledge graph."

class RhetoricalRetriever(NeoTool):
    name: str = "rhetorical_retriever"
    description: str = "Retrieve educational content using Node ID and rhetorical role."
    args_schema: Type[BaseModel] = ContentInput

    def _run(self, node_id: str, role: str):
        cypher = """
        MATCH (n:Entity {id: $id})-[:CONTENT]->(c:Entity)
        WHERE c.rrole = $role
        RETURN c.content AS content
        """
        results = self.run_query( cypher, {"id": node_id, "role": role})
        
        if not results:
            return f"INFO: No content found for role '{role}'."
        
        return f"SOURCE_DATA ({role}): " + "\n".join([r['content'] for r in results])
    
class EdgeExplorer(NeoTool):
    name: str = "edge_explorer"
    description: str = "Explore related concepts by searching both incoming and outgoing edges in the graph."
    engine: GraphDB
    db_name: str = "test"

    def _run(self, node_id: str):
        cypher = """
        MATCH (n:Entity {id: $id})
        OPTIONAL MATCH (n)-[r_out]->(m_out:Entity) 
        WHERE m_out.rrole IS NULL AND m_out.id <> $id
        OPTIONAL MATCH (n)<-[r_in]-(m_in:Entity) 
        WHERE m_in.rrole IS NULL AND m_in.id <> $id
        RETURN 
            collect(DISTINCT {name: m_out.name, type: type(r_out), id: m_out.id, dir: 'OUTGOING'}) as out_rels,
            collect(DISTINCT {name: m_in.name, type: type(r_in), id: m_in.id, dir: 'INCOMING'}) as in_rels
        """
        results = self.run_query(cypher, {"id": node_id})
        
        if not results or (not results[0]['out_rels'] and not results[0]['in_rels']):
            return f"INFO: No relationships found for ID {node_id}."

        output = []
        res = results[0]
        
        if res['in_rels']:
            output.append("PARENT/CONTEXT CONCEPTS (Incoming):")
            for r in res['in_rels']:
                if r['name']: output.append(f"- {r['name']} (ID: {r['id']}) via {r['type']}")
        
        if res['out_rels']:
            output.append("\nRELATED/SUB CONCEPTS (Outgoing):")
            for r in res['out_rels']:
                if r['name']: output.append(f"- {r['name']} (ID: {r['id']}) via {r['type']}")

        return "\n".join(output)