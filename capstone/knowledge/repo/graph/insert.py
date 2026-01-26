import os
from typing import List, Union
from pydantic import BaseModel, Field
from neo4j import GraphDatabase

# Local import to avoid circular dependency
if __name__ == "__main__":
    from test_schema import Graph
else:
    from knowledge.repo.graph.test_schema import Graph


# --- 2. graphDB Logic ---
class GraphDB:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def setup_databases(self, db_names: Union[List[str]]):
        """
        Connects to 'system' DB to create requested databases.
        Required Enterprise Edition.
        """
        print(f"Checking databases: {db_names}...")
        with self.driver.session(database="system") as session:
            for db in db_names:
                # CREATE DATABASE IF NOT EXISTS is idempotent
                session.run(f"CREATE DATABASE {db} IF NOT EXISTS WAIT")
        print("Databases setup complete.")

    def create_constraints(self, db_name: str):
        """
        Creates uniqueness constraint on Entity(id).
        Critically important for performance of edge insertion.
        """
        query = "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE"
        with self.driver.session(database=db_name) as session:
            session.run(query)
        print(f"[{db_name}] Constraints ensured.")

    def import_graph(self, db_name: str, graph: Graph):
        source_tag = graph.source
        self.create_constraints(db_name)

        with self.driver.session(database=db_name) as session:
            
            print(f"[{db_name}] Merging {len(graph.entities)} nodes from source '{source_tag}'...")
            session.run("""
                UNWIND $entities AS entity_id
                MERGE (n:Entity {id: entity_id})
                
                ON CREATE SET 
                    n.created_at = datetime(),
                    n.sources = [$source_tag],
                    n.frequency = 1
                
                ON MATCH SET 
                    n.updated_at = datetime(),
                    n.sources = CASE 
                        WHEN NOT $source_tag IN n.sources THEN n.sources + $source_tag 
                        ELSE n.sources 
                    END,
                    n.frequency = n.frequency + 1
                """, entities=list(graph.entities), source_tag=source_tag)

            # 2. MERGE EDGES with Weight boosting
            # Logic: Tăng trọng số 'weight' mỗi khi gặp lại quan hệ cũ
            print(f"[{db_name}] Merging {len(graph.relations)} relationships...")
            session.run("""
                UNWIND $relations AS row
                MATCH (s:Entity {id: row[0]})
                MATCH (o:Entity {id: row[2]})
                
                // Dùng APOC để merge cạnh động
                CALL apoc.merge.relationship(s, row[1], {}, {}, o) YIELD rel
                
                // Cập nhật thuộc tính trên cạnh (Edge properties)
                SET rel.sources = CASE 
                        WHEN rel.sources IS NULL THEN [$source_tag]
                        WHEN NOT $source_tag IN rel.sources THEN rel.sources + $source_tag 
                        ELSE rel.sources 
                    END,
                    rel.weight = COALESCE(rel.weight, 0) + 1,
                    rel.last_seen = datetime()
                """, relations=list(graph.relations), source_tag=source_tag)
            
            print(f"[{db_name}] Merge finished.")
    
    def reset(self, db_name: str):
        
        print(f"[{db_name}] Performing HARD RESET (DROP & RE-CREATE)...")
        try:
            with self.driver.session(database="system") as session:
                session.run(f"CREATE OR REPLACE DATABASE {db_name} WAIT")
            
            print(f"[{db_name}] Database re-created. Re-applying constraints...")
            
            self.create_constraints(db_name)
            
            print(f"[{db_name}] Reset successfully.")
            
        except Exception as e:
            print(f"[{db_name}] Reset FAILED: {e}")
            raise e




if __name__ == "__main__":
    import json
    with open("test/graph.json", 'r') as f:
        raw_data = json.load(f)
    graph_data = Graph(**raw_data)

    # Init Neo4j graphDB
    # Note: 'localhost' maps to ports exposed in docker-compose.
    graphDB = GraphDB(uri="bolt://localhost:7687", auth=("neo4j", "graph123"))

    try:
        # 1. Setup Databases (One time setup)
        target_dbs = ["kggen", "test", "final"]
        graphDB.setup_databases(target_dbs)
    
        graphDB.reset("kggen")
        graphDB.import_graph("kggen", graph_data)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        graphDB.close()