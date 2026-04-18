import os
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from core.config import *
from time import time
class GraphDB:
    def __init__(self, config: Neo = Neo):
        self.driver = GraphDatabase.driver(config.uri, auth=config.auth)
        self.setup_databases(["ref", "test", "final"])

        self.config =config

    def close(self):
        self.driver.close()

    def setup_databases(self, db_names: List[str]):
        with self.driver.session(database="system") as session:
            for db in db_names:
                session.run(f"CREATE DATABASE {db} IF NOT EXISTS WAIT")
                self.create_constraints(db)

    def create_constraints(self, db_name: str ):
        id_const = "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE"
        name_const = "CREATE CONSTRAINT node_name_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE"
        index_text = "CREATE FULLTEXT INDEX entity_text_index IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.id]"
        index_role = "CREATE INDEX entity_role_index IF NOT EXISTS FOR (n:Entity) ON (n.rrole)"
        
        with self.driver.session(database=db_name) as session:
            session.run(id_const)
            session.run(name_const)
            session.run(index_text)
            session.run(index_role)

    def reset(self, db_name: str):
        with self.driver.session(database="system") as session:
            session.run(f"CREATE OR REPLACE DATABASE {db_name} WAIT")
        self.create_constraints(db_name)

    def import_data(self, db_name: str =DB_NAME, nodes: List[Dict] = [], edges: List[Dict]= [], clusters: List[Dict]= []):
        start = time()
        with self.driver.session(database=db_name) as session:
            if nodes:
                session.execute_write(self._insert_nodes, nodes)
            if edges:
                session.execute_write(self._insert_edges, edges)
            if clusters:
                session.execute_write(self._insert_clusters, clusters)
        print(f"Graph inserted in {time() - start}")

    @staticmethod
    def _insert_nodes(tx, nodes: List[Dict]) -> None:
        nodes = [n for n in nodes if n.get('name') and str(n.get('name')).strip()]
        query = """
        UNWIND $nodes AS node_item
        MERGE (n:Entity {name: node_item.name})
        ON MATCH SET n.definition = coalesce(n.definition, node_item.definition)
        ON CREATE SET n = node_item
        WITH n, node_item
        CALL apoc.create.addLabels(n, [node_item.name]) YIELD node
        RETURN count(*)
        """
        tx.run(query, nodes=nodes)

    @staticmethod
    def _insert_edges(tx, edges: List[Dict]):
        edges = [e for e in edges if e.get('source_name') and e.get('target_name')]
        query = """
        UNWIND $edges AS edge_item
        MATCH (s:Entity {name: edge_item.source_name})
        MATCH (t:Entity {name: edge_item.target_name})
        WITH s, t, edge_item
        CALL apoc.merge.relationship(s, edge_item.type, {}, edge_item.props, t) YIELD rel
        RETURN count(*)
        """
        tx.run(query, edges=edges)

    @staticmethod
    def _insert_clusters(tx, clusters: List[Dict]):
        
        query = """
        UNWIND $clusters AS c
        MATCH (n:Entity {name: c.name})
        SET n.cluster_id = c.cluster_id,
            n.cluster_level = c.level
        """
        tx.run(query, clusters=clusters)

    def run_query(self, db_name: str, query: str, params: Dict = None) -> List[Dict]:
        with self.driver.session(database=db_name) as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
        
    def get_entity_by_id(self, db_name: str, node_id: str) -> Optional[Dict]:
        query = "MATCH (n:Entity {id: $id}) RETURN n"
        with self.driver.session(database=db_name) as session:
            result = session.run(query, id=node_id).single()
            return result["n"] if result else None
        
    def update_links(self,chunk_id, heading, storage_uri, links, db_name = "test"):
        with self.driver.session(database=db_name) as session:
                    session.run(
                        """
                        MERGE (c:TextbookChunk {id: $chunk_id})
                        SET c.heading = $heading, c.storage_uri = $storage_uri
                        WITH c
                        UNWIND $links AS link
                        MATCH (anchor {id: link.anchor_id})
                        MERGE (c)-[r:ELABORATES_ON]->(anchor)
                        SET r.justification = link.justification
                        """,
                        chunk_id=chunk_id, heading=heading, 
                        storage_uri=storage_uri, links=links
                    )
    def query(self, q = None, param = {}):
        if q == None or len(q) <=3:
            return
        db_name = self.config.db_name
        with self.driver.session(database=db_name) as session:
                    session.run(q,param)