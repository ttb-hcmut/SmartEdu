import os
from typing import List, Union, Dict
from neo4j import GraphDatabase
from knowledge.core.schema.graph import KG_Instance
from knowledge.repo.graph import insert
class GraphDB:
    def __init__(self, 
                 uri = "bolt://localhost:7687", 
                 auth=("neo4j", "graph123") ):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.setup_databases(["ref","test","final"])
    def close(self):
        self.driver.close()

    def setup_databases(self, db_names: List[str]):
        with self.driver.session(database="system") as session:
            for db in db_names:
                session.run(f"CREATE DATABASE {db} IF NOT EXISTS WAIT")
                self.create_constraints(db)

    def create_constraints(self, db_name: str):
        id_const  = "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE"
        name_const = "CREATE CONSTRAINT node_name_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE"

        index =[ "CREATE FULLTEXT INDEX entity_text_index IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.id]",
                "CREATE INDEX entity_role_index IF NOT EXISTS FOR (n:Entity) ON (n.rrole)"
                ]
        with self.driver.session(database=db_name) as session:
            session.run(id_const)
            session.run(name_const)
            for i in index:
                session.run(i)

    def import_graph(self, db_name: str, graph: KG_Instance):
        
        with self.driver.session(database=db_name) as session:
            # 1. Import Nodes
            nodes_list = []

            for node_id, node_data in graph.nodes.items():
                node_props = insert.serialize_data(node_data.model_dump())
                nodes_list.append(node_props)
               
            session.run("""
                UNWIND $nodes AS node_item
                MERGE (n:Entity {id: node_item.id})
                SET n += node_item
                WITH n, node_item
                CALL apoc.create.addLabels(n, [node_item.name]) YIELD node
                RETURN count(*)
                """, nodes=nodes_list)

            # 2. Import Edges
            edges_list = []
            for (src, tgt, rel_type), edge_data in graph.edges.items():
                edge_props =insert.serialize_data(edge_data.model_dump(exclude={"source", "target"}))

                edges_doc = {
                    "source": src,
                    "target": tgt,
                    **edge_props
                }

                print(edges_doc)
                edges_list.append(edges_doc)

            session.run("""
                UNWIND $edges AS edge_item
                MATCH (s:Entity {id: edge_item.source})
                MATCH (t:Entity {id: edge_item.target})
                
                WITH s, t, edge_item, 
                    apoc.map.clean(edge_item, ['source', 'target' ], []) AS props
                CALL apoc.merge.relationship(s, edge_item.type, {}, props, t) YIELD rel
                RETURN count(*)
            """, edges=edges_list)

            # 3. Import Clusters (Mapping nodes to clusters)
            if graph.clusters:
                cluster_list = []
                for cluster_id, cluster_data in graph.clusters.items():
                    for node_id in cluster_data.member_ids: 
                        cluster_list.append({
                            "cluster_id": cluster_id,
                            "node_id": node_id,
                            "level": getattr(cluster_data, 'level', 0)
                        })

                session.run("""
                    UNWIND $clusters AS c
                    MATCH (n:Entity {id: c.node_id})
                    SET n.cluster_id = c.cluster_id,
                        n.cluster_level = c.level
                    """, clusters=cluster_list)

    def reset(self, db_name: str):
        with self.driver.session(database="system") as session:
            session.run(f"CREATE OR REPLACE DATABASE {db_name} WAIT")
        self.create_constraints(db_name)