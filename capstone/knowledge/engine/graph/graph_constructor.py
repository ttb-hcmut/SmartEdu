import uuid
import asyncio
from typing import Dict, List, Optional
from knowledge.core.schema.factory import *
from knowledge.core.schema.graph import *
from knowledge.engine.graph.helper.analyzer import *
from knowledge.engine.graph.visualize_kg import visualize

import json

class KG_Handler:
    def __init__(self, doc_id: str = "test_01", doc_name: str = "ML for beginner"):
        self.doc_id = doc_id
        self.doc_name = doc_name
        self.kg = KG_Instance()
        self.node_cache: Dict[str, EduNode] = {}

    def build(self, skeleton: SkeletonStructure, relations: RelationStructure, topic_name: str = None) -> KG_Instance:
        source_cluster = self._create_source_cluster()
        self.kg.clusters[source_cluster.id] = source_cluster
        if topic_name:
            topic_cluster = self._handle_topic_clustering(topic_name)
        node_list, relations = analyze(skeleton, relations)

        for node in node_list:            
            concept_node = self._create_concept_node(node)
            self._add_node_to_kg(concept_node)
            self._add_to_cluster(source_cluster, concept_node)
            if topic_name:
                self._add_to_cluster(topic_cluster, concept_node, 1)
            for detail in node.get("details"):
                rhet_node = self._create_rhetorical_node(detail, concept_node)
                self._add_node_to_kg(rhet_node)
                self._add_to_cluster(source_cluster, rhet_node)
                
                self._create_edge(
                    src=concept_node,
                    tgt=rhet_node,
                    name=f"{concept_node.name}-{detail.role.value.upper()}"
                )

        for rel in relations.edges:
            if rel.src in self.node_cache and rel.tgt in self.node_cache:
                src_node = self.node_cache[rel.src]
                tgt_node = self.node_cache[rel.tgt]
                edge_name = rel.name if hasattr(rel, 'name') else "RELATED_TO"
                self._create_edge(
                    src=src_node,
                    tgt=tgt_node,
                    name=f"{src_node.name}-{edge_name}-{tgt_node.name}" 
                )

        return self.kg

    def _create_source_cluster(self) -> Cluster:
        c_id = f"cluster_source_{self.doc_id}"

        return Cluster(
            id=c_id,
            label=self.doc_name,
            type=ClusterType.SOURCE,
            metadata={"doc_id": self.doc_id}
        )

    def _create_concept_node(self, node: Dict) -> ConceptNode:
        node_id = node["id"]
        name = node.get("name")
        description = node.get("desc", "")

        node = ConceptNode(
            id=node_id,
            name=name,
            content=description,
            typeNode=NodeType.CONCEPT)
        
        self.node_cache[name] = node
        return node

    def _create_rhetorical_node(self, item: RhetoricalItem, concept_node: ConceptNode) -> RhetoricalNode:
        node_id = f"{concept_node.id}_{item.role.value}"
        name = f"{concept_node.name}_{item.role.value}"
        return RhetoricalNode(
            id=node_id,
            rrole=item.role.value,
            name=name,
            concept_id=concept_node.id,
            content=item.content,
            score=item.confidence,
            typeNode=NodeType.RHETORICAL,
            metadata={}
        )

    def _add_node_to_kg(self, node: EduNode) -> str:
        self.kg.nodes[node.id] = node
        return node.id


    def _create_edge(self, src: EduNode, tgt: EduNode, name: str):
        typ = edge_type(src, tgt)
        edge_key = (src.id, tgt.id, typ)
        if edge_key not in self.kg.edges:
            edge = EduEdge(source=src, target=tgt, name=name, type=typ)
            self.kg.edges[edge_key] = edge

    def _add_to_cluster(self, cluster: Cluster, node: EduNode, mode = 0):
        cluster.member_ids.append(node.id)

        
        if mode == 1:
            anchor_node = self.kg.nodes[cluster.anchor_node]
            self._create_edge(src = anchor_node , tgt=node, name= "")

    def _handle_topic_clustering(self, topic_name: str):
        id = "Q2539"
        t_id = f"topic_{id}"
        node = TopicNode(id = id,name =topic_name)
        self._add_node_to_kg(node)
        if t_id not in self.kg.clusters:
            topic_cluster = Cluster(
                id=f"cluster_{t_id}",
                label=topic_name,
                type=ClusterType.TOPIC,
                anchor_node=node.id
            )
            
            self.kg.clusters[topic_cluster.id] = topic_cluster
            return topic_cluster
        else: return self.kg.clusters[t_id]


    def save_json(self, path="test/kg.json"):
        data = self.kg.model_dump(exclude_none=True, exclude_defaults=True)

        if 'edges' in data:
            new_edges = {}
            for key, edge in data['edges'].items():
                str_key = str(key) 
                
                if isinstance(edge.get('source'), dict):
                    edge['source'] = edge['source'].get('id')
                if isinstance(edge.get('target'), dict):
                    edge['target'] = edge['target'].get('id')
                
                new_edges[str_key] = edge
            data['edges'] = new_edges

        with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def load_kg_from_json(self, path="test/kg.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.kg = KG_Instance.model_validate_json(f.read())
        except Exception as e:
            print(f"{e}")
        
    def visualize_kg(self):
        visualize(self.kg)