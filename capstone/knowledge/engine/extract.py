import json
from time import time
from typing import Tuple, List, Union, Dict

from core.schema.graph.type import Ref
from core.schema.factory import SkeletonStructure, RelationStructure, AnchorLinkStructure
from knowledge.engine.graph.graph_constructor import KG_Handler

from core.llm.prompt.graph import prompt_p0, prompt_p1, prompt_p2, TEXTBOOK_EXTRACTION_PROMPT
from core.llm.llm_engine import CoreLLMEngine
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

class GraphExtractionService:
    def __init__(self, llm_engine: CoreLLMEngine, test: bool = False):
        self.llm_engine = llm_engine
        self.parser_p1 = PydanticOutputParser(pydantic_object=SkeletonStructure)
        self.parser_p2 = PydanticOutputParser(pydantic_object=RelationStructure)
        self.parser_links = PydanticOutputParser(pydantic_object=AnchorLinkStructure)
        self.kg_handler = KG_Handler()
        self.test = test

    def extract_and_build(self, 
                         texts: List[Tuple[str, str]], 
                         course_name: str = "General Course",
                         save: str =  "kg_new.json", 
                         hard_ref: List[Ref] = None, 
                         soft_refs: List[Ref] = None):
        
        for i, (topic_name, text) in enumerate(iterable=texts):
            start: float = time()
            raw_name = topic_name
            topic_name: str = self.llm_engine.invoke_with_retry(
                prompt_template=prompt_p0,
                parser=StrOutputParser(),
                input_data={
                "raw_name": raw_name,
                "text_content": text[:100]
                },
                profile_name="worker"
            )

            print(f"Old: {raw_name}, new: {topic_name}")
            print(f"Finish in {time()-start} s")
            p1_result: SkeletonStructure = self.llm_engine.invoke_with_retry(
                prompt_template=prompt_p1,
                parser=self.parser_p1,
                input_data={
                    "text": f"Topic: {topic_name} \n{text}",
                    "course": course_name,
                    "format_instructions": self.parser_p1.get_format_instructions()
                },
                profile_name="graph"
            )

            if not p1_result:
                continue

            extracted_concepts: List[str] = [b.name for b in p1_result.tree]

            p2_result: RelationStructure = self.llm_engine.invoke_with_retry(
                prompt_template=prompt_p2,
                parser=self.parser_p2,
                input_data={
                    "text": text,
                    "concept_list": ", ".join(extracted_concepts),
                    "format_instructions": self.parser_p2.get_format_instructions()
                },
                profile_name="graph"
            )

            if not p2_result:
                continue

            if save:
                literature_union = {
                    "og": text,
                    "meta": {
                        "model": self.llm_engine.config.profiles["graph"].model_name,
                        "concept_count": len(extracted_concepts),
                        "relation_count": len(p2_result.edges)
                    },
                    "skeleton_phase": p1_result.model_dump(),
                    "relation_phase": p2_result.model_dump()
                }
                with open(f"test/graph_const/graph_lit_{i}.json", "w", encoding="utf-8") as f:
                    json.dump(literature_union, f, indent=2, ensure_ascii=False)
            
            self.kg_handler.build(
                p1_result, 
                p2_result, 
                topic_name=topic_name, 
                course_name=course_name,
                hard_ref=hard_ref[i] if hard_ref else None, 
                soft_refs=soft_refs[i] if soft_refs else None
            )
            print(f"Finish topic {topic_name} in {time() - start} seconds")
        if save:
            self.kg_handler.save_json(name=save)
            #self.kg_handler.visualize_kg()

        return self.kg_handler.kg

    def link_textbook_to_anchors(self, text: str, candidates: List[Dict]) -> List[Dict]:
        formatted_candidates = "\n".join(
            [f"- ID: {c['id']} | Name: {c.get('name', 'N/A')}" for c in candidates]
        )
        
        result: AnchorLinkStructure = self.llm_engine.invoke_with_retry(
            prompt_template=TEXTBOOK_EXTRACTION_PROMPT,
            parser=self.parser_links,
            input_data={
                "text": text,
                "candidates": formatted_candidates,
                "format_instructions": self.parser_links.get_format_instructions()
            },
            profile_name="graph"
        )
        
        if not result or not result.links:
            return []

        valid_ids = {c['id'] for c in candidates}
        return [
            link.model_dump() for link in result.links 
            if link.anchor_id in valid_ids
        ]
