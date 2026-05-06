import uuid
import json
from typing import Dict, List, Optional, Tuple, Any
from core.schema.factory import SkeletonStructure, RelationStructure, RhetoricalItem
from core.schema.graph import (
    Cluster, ConceptNode, EduEdge, EduNode, KG_Instance, 
    NodeType, ClusterType, TopicNode, CommunityNode, RhetoricalNode, Ref
)
from knowledge.engine.graph.helper.analyzer import *
import asyncio
class KG_Handler:
    def __init__(self):
        self.kg = KG_Instance()
        self.node_cache: Dict[str, Any] = {}
        self.NAMESPACE = uuid.NAMESPACE_DNS
        

    def _get_identity(self, name: str):
        results: Dict = asyncio.run(wiki_resolver([name])).get(name)

        wiki_id = results.get("id", None)
        name = results.get("label", name)
        name = nlp_normalize(text = str(name))
        content =results.get("desc", "").lower()
        if wiki_id:
            return wiki_id, name, content 
        return uuid.uuid5(self.NAMESPACE, name=f"{self.course_name}_{name.lower().strip()}").hex[:12], name, "Course-specific concept without wiki page"

    def _init_course_community(self) -> CommunityNode:
        c_id, name, content = self._get_identity(self.course_name)
        
        node = CommunityNode(
            id=c_id, 
            name=name, 
            content=content,
            typeNode=NodeType.COMMUNITY
        )
        self.kg.nodes[node.id] = node
        self.node_cache[self.course_name.lower()] = node
        return node

    def build(self, skeleton: SkeletonStructure, relations: RelationStructure, 
              topic_name: str = None, 
              hard_ref: Ref = None,
              soft_refs: List[Ref] = None,
              course_name: str = "Machine Learning", 
              doc_id: str = "test_01") -> KG_Instance:
        self.course_name = course_name.strip()
        root_community = self._init_course_community()
        nodes, relations = analyze(skeleton, relations)

        topic_cluster = None
        if topic_name:
            topic_wiki_id = next((n.get("id") for n in nodes if n["name"].lower() == topic_name.lower() and "local_" not in str(n.get("id"))), None)
            topic_cluster = self._handle_topic_clustering(topic_name, root_community, topic_wiki_id)

        for node_data in nodes:            
            concept_node = self._create_concept_node(node_data, topic_name=topic_name)
            self.kg.nodes[concept_node.id] = concept_node
            
            if topic_cluster:
                self._add_to_cluster(topic_cluster, concept_node, mode=1)

            if hard_ref: concept_node.hard_ref = hard_ref
            if soft_refs: concept_node.soft_ref.extend(soft_refs)
                
            for detail in node_data.get("details", []):
                rhet_node = self._create_rhetorical_node(detail, concept_node)
                self.kg.nodes[rhet_node.id] = rhet_node
                if topic_cluster:
                    self._add_to_cluster(topic_cluster, rhet_node, mode=0)
                
                self._create_edge(src=concept_node, tgt=rhet_node, name=detail.role.value.upper(), content="This concept contains this knowledge")

        for rel in relations.edges:
            src_node = self.node_cache.get(rel.src.lower())
            tgt_node = self.node_cache.get(rel.tgt.lower())
            content = rel.rel
            if src_node and tgt_node:
                self._create_edge(src=src_node, tgt=tgt_node, name=rel.name, content=content)

        return self.kg

    def _handle_topic_clustering(self, topic_name: str, root_community,wiki_id: Optional[str] = None) -> Cluster:
        t_id = wiki_id if wiki_id else self._get_identity(topic_name)[0]
        c_id = f"cluster_{t_id}"

        if t_id not in self.kg.nodes:
            node = TopicNode(id=t_id, name=topic_name, content=f"Topic: {topic_name}", typeNode=NodeType.TOPIC)
            self.kg.nodes[node.id] = node
            self.node_cache[topic_name.lower()] = node
            self._create_edge(src=node, tgt=root_community, name="PART_OF", content = "Source concept is essentially a part of target topic")

        if c_id not in self.kg.clusters:
            self.kg.clusters[c_id] = Cluster(id=c_id, label=topic_name, type=ClusterType.TOPIC, anchor_node=t_id)
        return self.kg.clusters[c_id]

    def _create_concept_node(self, node_data: Dict, topic_name: str = None) -> ConceptNode:
        name = node_data.get("name").strip()
        node_id = node_data.get("id")
        if node_id == "local":
            node_id = uuid.uuid5(self.NAMESPACE, f"{self.course_name}_{name.lower().strip()}").hex[:12]
        if name.lower() == topic_name.lower() or self.course_name.lower() == name.lower():
            higher_level_node = self.node_cache.get(name.lower())
            if higher_level_node:
                higher_level_node.content = node_data.get("desc", higher_level_node.content)
                return higher_level_node
            
        if node_id in self.kg.nodes:
            node = self.kg.nodes[node_id]
            if len(node_data.get("desc", "")) > len(node.content):
                node.content = node_data.get("desc")
            return node
        
        node = ConceptNode(id=node_id, name=name, content=node_data.get("desc", ""), typeNode=NodeType.CONCEPT)
        self.node_cache[name.lower()] = node
        return node

    def _create_rhetorical_node(self, item: RhetoricalItem, concept_node: ConceptNode) -> RhetoricalNode:
        node_id = f"{concept_node.id}_{item.role.value}"
        return RhetoricalNode(
            id=node_id,
            rrole=item.role.value,
            name=f"{concept_node.name}_{item.role.value}",
            concept_id=concept_node.id,
            content=item.content,
            score=item.confidence,
            typeNode=NodeType.RHETORICAL
        )

    def _create_edge(self, src: EduNode, tgt: EduNode, name: str, content: str = ""):
        if src.id == tgt.id: return
        typ = edge_type(src, tgt)
        edge_key = (src.id, tgt.id, typ)
        if edge_key not in self.kg.edges:
            self.kg.edges[edge_key] = EduEdge(source=src, target=tgt, name=name, type=typ, relationship=content  )

    def _add_to_cluster(self, cluster: Cluster, node: EduNode, mode = 0):
        if node.id not in cluster.member_ids:
            cluster.member_ids.append(node.id)
        if mode == 1 and cluster.anchor_node and node.id != cluster.anchor_node:
            anchor_node = self.kg.nodes[cluster.anchor_node]
            self._create_edge(src=node, tgt=anchor_node, name="BELONGS_TO", content = "Source concept is estimately the foundation and root to the target concept")

    def save_json(self, name: str = "kg.json"):
        data = self.kg.model_dump(exclude_none=True, exclude_defaults=True)
        if 'edges' in data:
            data['edges'] = {str(k): v for k, v in data['edges'].items()}
            for edge in data['edges'].values():
                if isinstance(edge.get('source'), dict): edge['source'] = edge['source']['id']
                if isinstance(edge.get('target'), dict): edge['target'] = edge['target']['id']
        with open(f"test/graph_const/{name}", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)