import asyncio
import uuid
from typing import List, Tuple, Dict, Any, Set
from knowledge.core.schema.factory import (
    SkeletonStructure, 
    RelationStructure, 
    RelationEdge, 
    RhetoricalItem,
    RhetoricalRole
)
from knowledge.core.schema.graph.graph import *
from knowledge.engine.graph.helper.normalize import wiki_resolver, nlp_normalize

SUBJECT_FILE = "subjects.csv"
RHET_SUFFIXES = {"objective", "goal", "problem", "challenge", "benefit", "drawback", "aim", "issue", "limitation"}
PARENT_SUFFIXES = {"model", "algorithm", "system", "framework", "method", "approach", "network", "theory", "technique"}

def edge_type(s: EduNode, t: EduNode):
        type = None
        if isinstance(t, RhetoricalNode):
            name = f"{s.name}-{t.rrole.value.upper()}"
            type = "CONTENT"
            
        if isinstance(s, RhetoricalNode):
            name = f"{t.rrole.value.upper()}_ref_{t.name}"
            type = "REFERENCE"
        elif isinstance(s, ConceptNode):
            if isinstance(t, ConceptNode):
                type = "SEMANTIC"
            if isinstance(t, TopicNode) or isinstance(t, CommunityNode):
                type = "PART_OF"
        elif isinstance(s, TopicNode):
            if isinstance(t, TopicNode):
                type = "RELATED"
            elif isinstance(t, CommunityNode):
                type = "PART_OF"
                name = f"{s.name}_within_{t.name}"
        elif isinstance(s, CommunityNode) and isinstance(t, CommunityNode):
            type = "PREREQUISITE"

        if type is None:
            type = "RELATED"
        
        return type

def analyze(skeleton: SkeletonStructure, relations: RelationStructure) -> Tuple[List[Dict[str, Any]], RelationStructure]:
    actions = {}
    concepts_to_fetch = set()

    def get_content(c):
        return getattr(c, "content", "") or (c.details[0].content if c.details else "")

    for c in skeleton.tree:
        clean = nlp_normalize(c.name)
        tokens = clean.split()
        head = tokens[-1].lower() if tokens else ""
        parent_name = " ".join(tokens[:-1]) if len(tokens) > 1 else ""
        content = get_content(c)

        if head in RHET_SUFFIXES and parent_name:
            actions[c.name] = {
                "type": "DOWNGRADE",
                "parent": parent_name,
                "role": head.upper(),
                "content": content,
                "existing_details": c.details
            }
            concepts_to_fetch.add(parent_name)
            
        elif head in PARENT_SUFFIXES and parent_name:
            actions[c.name] = {
                "type": "HIERARCHY",
                "self": clean,
                "parent": parent_name,
                "content": content,
                "existing_details": c.details
            }
            concepts_to_fetch.add(clean)
            concepts_to_fetch.add(parent_name)
            
        else:
            actions[c.name] = {
                "type": "KEEP", 
                "self": clean, 
                "content": content,
                "existing_details": c.details
            }
            concepts_to_fetch.add(clean)

    try:
        try:
            wiki_map = asyncio.run(wiki_resolver(list(concepts_to_fetch), SUBJECT_FILE))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            wiki_map = loop.run_until_complete(wiki_resolver(list(concepts_to_fetch), SUBJECT_FILE))
    except Exception:
        wiki_map = {}

    concept_storage: Dict[str, Dict[str, Any]] = {}
    name_mapping = {}

    def get_or_create_concept(name, desc_fallback=""):
        w = wiki_map.get(name, {})
        final_label = w.get("label", name)
        if len(final_label) > 60 or len(final_label.split()) > 5: 
            final_label = name
        if final_label not in concept_storage:
            uid = w.get("id") or f"local_{uuid.uuid5(uuid.NAMESPACE_DNS, final_label).hex[:8]}"
            concept_storage[final_label] = {
                "id": uid,
                "name": final_label,
                "desc": w.get("desc") or desc_fallback,
                "status": "WIKI" if w.get("id") else "LOCAL",
                "details": []
            }
        return concept_storage[final_label]

    generated_edges = []

    for original_name, act in actions.items():
        if act["type"] == "DOWNGRADE":
            p_data = get_or_create_concept(act["parent"], "Extracted Parent Concept")
            try:
                new_rheto = RhetoricalItem(
                    role=act["role"],
                    content=act["content"],
                    confidence=3
                )
                p_data["details"].append(new_rheto)
            except Exception:
                pass 
            
            p_data["details"].extend(act["existing_details"])
            name_mapping[original_name] = p_data["name"]

        else:
            self_name = act["self"]
            node_data = get_or_create_concept(self_name, act["content"])
            node_data["details"].extend(act["existing_details"])
            name_mapping[original_name] = node_data["name"]

            if act["type"] == "HIERARCHY":
                p_name = act["parent"]
                p_data = get_or_create_concept(p_name, "General Concept")
                
                generated_edges.append(RelationEdge(
                    src=node_data["name"], 
                    tgt=p_data["name"], 
                    name="PART_OF"
                ))

    final_edges = []
    for rel in relations.edges:
        s_new = name_mapping.get(rel.src)
        t_new = name_mapping.get(rel.tgt)
        
        if s_new and t_new and s_new != t_new:
            new_edge = rel.model_copy()
            new_edge.src = s_new
            new_edge.tgt = t_new
            final_edges.append(new_edge)
    
    final_edges.extend(generated_edges)
    node_list = list(concept_storage.values())

    return node_list, relations.model_copy(update={"edges": final_edges})