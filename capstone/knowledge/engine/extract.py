import json
import asyncio
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

    async def _extract_single_chunk(self, topic_hint: str, text: str, course_name: str, chunk_idx: int):
        topic_name: str = await self.llm_engine.ainvoke_with_retry(
            prompt_template=prompt_p0,
            parser=StrOutputParser(),
            input_data={
                "raw_name": topic_hint,
                "text_content": text[:100]
            },
            profile_name="worker"
        )
        if not topic_name:
            return None

        p1_result: SkeletonStructure = await self.llm_engine.ainvoke_with_retry(
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
            return None

        extracted_concepts: List[str] = [b.name for b in p1_result.tree]

        p2_result: RelationStructure = await self.llm_engine.ainvoke_with_retry(
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
            return None

        return (chunk_idx, topic_name, p1_result, p2_result)

    async def _llm_worker(self, worker_id: int, extract_queue: asyncio.Queue, 
                           build_queue: asyncio.Queue, course_name: str):
        while True:
            item = await extract_queue.get()
            if item is None:
                await build_queue.put(None)
                extract_queue.task_done()
                print(f"[Worker-{worker_id}] Poison pill received.")
                break

            chunk_idx, topic_hint, text, hard_ref = item
            try:
                start: float = time()
                result = await self._extract_single_chunk(
                    topic_hint=topic_hint, text=text, 
                    course_name=course_name, chunk_idx=chunk_idx
                )
                if result:
                    chunk_idx, topic_name, p1, p2 = result
                    await build_queue.put((chunk_idx, topic_name, p1, p2, hard_ref, text))
                    print(f"[Worker-{worker_id}] Chunk {chunk_idx} done in {time()-start:.1f}s")
            except Exception as e:
                print(f"[Worker-{worker_id}] Error chunk {chunk_idx}: {e}")
            finally:
                extract_queue.task_done()

    async def _db_builder(self, build_queue: asyncio.Queue, course_name: str, 
                           num_workers: int, save: str = None):
        poison_count = 0
        chunk_counter = 0
        
        while poison_count < num_workers:
            item = await build_queue.get()
            if item is None:
                poison_count += 1
                build_queue.task_done()
                continue

            chunk_idx, topic_name, p1_result, p2_result, hard_ref, text = item
            try:
                if save:
                    literature_union = {
                        "og": text,
                        "meta": {
                            "model": self.llm_engine.config.profiles["graph"].model_name,
                            "concept_count": len([b.name for b in p1_result.tree]),
                            "relation_count": len(p2_result.edges)
                        },
                        "skeleton_phase": p1_result.model_dump(),
                        "relation_phase": p2_result.model_dump()
                    }
                    with open(f"test/graph_const/graph_lit_{chunk_idx}.json", "w", encoding="utf-8") as f:
                        json.dump(literature_union, f, indent=2, ensure_ascii=False)

                self.kg_handler.build(
                    p1_result, p2_result, 
                    topic_name=topic_name, course_name=course_name,
                    hard_ref=hard_ref, soft_refs=None
                )
                chunk_counter += 1
                print(f"[Builder] Built chunk {chunk_idx} ({topic_name}), total: {chunk_counter}")
            except Exception as e:
                print(f"[Builder] Error chunk {chunk_idx}: {e}")
            finally:
                build_queue.task_done()

        if save:
            self.kg_handler.save_json(name=save)
        print(f"[Builder] Finished. Total: {chunk_counter}")

    async def extract_pipeline(self, extract_queue: asyncio.Queue,
                                course_name: str = "General Course",
                                save: str = "kg_new.json",
                                num_workers: int = 3):
        build_queue = asyncio.Queue(maxsize=20)

        worker_tasks = [
            asyncio.create_task(
                self._llm_worker(i, extract_queue, build_queue, course_name)
            )
            for i in range(num_workers)
        ]
        builder_task = asyncio.create_task(
            self._db_builder(build_queue, course_name, num_workers, save)
        )

        await asyncio.gather(*worker_tasks, builder_task)
        return self.kg_handler.kg

    async def link_textbook_chunk(self, text: str, candidates: List[Dict]) -> List[Dict]:
        formatted_candidates = "\n".join(
            [f"- ID: {c['id']} | Name: {c.get('name', 'N/A')}" for c in candidates]
        )
        
        result: AnchorLinkStructure = await self.llm_engine.ainvoke_with_retry(
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
