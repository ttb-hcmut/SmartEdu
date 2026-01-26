import uuid
from typing import Dict, List
from knowledge.core.schema.factory import *
from knowledge.engine.normalize import normalize

# Factory: turns into graph via: SkeletonStructure -- Union -- RelationStructure
## Create concept nodes: {id = wikidata.id, name=  wikidata.label, content = wikidata.description}
## Create edges ......

class GraphFactory:
    def __init__(self, doc_id: str, doc_name: str):
        self.doc_id = doc_id
        self.doc_name = doc_name
        self.kg = GlobalKG() 
        
        self.node_cache: Dict[str, EduNode] = {} 

    def build(self, skeleton: SkeletonStructure, relations: RelationStructure) -> None:
        """Hàm chính để build graph"""
        
        source_cluster = self._create_source_cluster()
        self.kg.clusters[source_cluster.id] = source_cluster

        for bundle in skeleton.bundles:
            concept_node = self._create_concept_node(bundle.name)
            self._add_node_to_kg(concept_node)
            self._add_to_cluster(source_cluster, concept_node)

            for detail in bundle.details:
                rhet_node = self._create_rhetorical_node(detail)
                self._add_node_to_kg(rhet_node)
                self._add_to_cluster(source_cluster, rhet_node)
                
                # Tạo cạnh: Concept --HAS_...--> Rhetorical
                self._create_edge(
                    src=concept_node, 
                    tgt=rhet_node, 
                    rel_type=f"HAS_{detail.role.upper()}"
                )

        for rel in relations.edges:
            if rel.src in self.node_cache and rel.tgt in self.node_cache:
                src_node = self.node_cache[rel.src]
                tgt_node = self.node_cache[rel.tgt]
                
                self._create_edge(
                    src=src_node, 
                    tgt=tgt_node, 
                    rel_type="RELATED_TO" # Hoặc lấy từ rel.type nếu schema có
                )
                
                self._handle_topic_clustering(src_node, tgt_node)



    def _create_source_cluster(self) -> Cluster:
        """Tạo cluster đại diện cho cả tài liệu"""
        c_id = f"cluster_source_{self.doc_id}"
        return Cluster(
            id=c_id,
            label=self.doc_name,
            type=ClusterType.SOURCE,
            metadata={"doc_id": self.doc_id}
        )

    def _create_concept_node(self, name: str) -> ConceptNode:

        node_id = f"concept_{hash(name)}" 
        node = ConceptNode(id=node_id, name=name, typeNode=NodeType.CONCEPT)
        self.node_cache[name] = node 
        return node

    def _create_rhetorical_node(self, item: RhetoricalItem) -> RhetoricalNode:
        # ID của Rhetorical là hash nội dung -> Tránh duplicate text
        node_id = f"rhet_{hash(item.content)}"
        return RhetoricalNode(
            id=node_id,
            rrole=item.role,
            content=item.content,
            score=item.confidence,
            typeNode=NodeType.RHETORICAL
        )

    def _add_node_to_kg(self, node: EduNode):
        self.kg.nodes[node.id] = node

    def _create_edge(self, src: EduNode, tgt: EduNode, rel_type: str):
        edge = EduEdge(source=src, target=tgt, name=rel_type)
        # Key của Edge Dictionary là Tuple (SrcID, TgtID, Type)
        edge_key = (src.id, tgt.id, rel_type)
        self.kg.edges[edge_key] = edge

    def _add_to_cluster(self, cluster: Cluster, node: EduNode):
        """Thêm node ID vào danh sách thành viên của Cluster"""
        cluster.member_ids[node.id] = node # Hoặc chỉ lưu ID tùy schema

    def _handle_topic_clustering(self, child: EduNode, parent: EduNode):
        """Logic: Nếu Parent là TopicNode, tự động tạo Cluster và nhét Child vào"""
        if isinstance(parent, TopicNode): # Check type
            cluster_id = f"cluster_topic_{parent.id}"
            
            # 1. Tìm hoặc tạo Cluster Topic
            if cluster_id not in self.kg.clusters:
                topic_cluster = Cluster(
                    id=cluster_id,
                    label=parent.name,
                    type=ClusterType.TOPIC,
                    anchor_node=parent.id # Neo vào Topic Node này
                )
                self.kg.clusters[cluster_id] = topic_cluster
            
            # 2. Thêm con vào Cluster
            self.kg.clusters[cluster_id].member_ids[child.id] = child