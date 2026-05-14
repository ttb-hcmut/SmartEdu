# Utis
from typing import List, Dict
import os
import uuid
from time import time
import re

# Logic
from core.schema.graph.graph import KG_Instance
from core.util.file_extractor import extract_pdf
from core.repo.graph.insert import serialize_kg_to_dict
from core.schema.graph.type import Ref
from knowledge.engine.extract import GraphExtractionService

#shared
from core.dependencies import * 
from core.config import *


def clean_content(text: str) -> str:
    pattern = r'==== PAGE \d+ ====\s*\n?'
    return re.sub(pattern, '', text).strip()


def clean_slide_name(name: str) -> str:
    if not name: return ""
        
    name = re.sub(r'\.[a-z0-9]+$', '', name, flags=re.IGNORECASE)
    

    name = re.sub(r'^(chapter|chap|ch|slide|lecture|bài|chương)\s*\d*\s*[:\-\.]?\s*', '', name, flags=re.IGNORECASE)
    
    name = re.sub(r'[^\w\s]', ' ', name).lower().strip()
    name = re.sub(r'\s+', ' ', name) 
    
    return name

class CourseIngestionService:
    def __init__(self, llm, graph_db, milvus_db, minio_repo, embedder):
        self.llm = llm
        self.graph_db : GraphDB = graph_db
        self.milvus_db : MilvusDB = milvus_db
        self.minio_repo : MinioDB= minio_repo
        self.extractor = GraphExtractionService(llm_engine=self.llm)
        self.embedder : Embedder = embedder
        self.db_name = DB_NAME

        self.config = Ingest_param()

    def _process_slide(self, name: str, course_name):

        file_path = self.config.path  + name
        
        chunks: List[Dict[str, str]] = extract_pdf(file_path,pages_per_batch= self.config.PAGE_PER_SLIDE)
        hard_refs = []
        texts = []

        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        pdf_uri = self.minio_repo.upload_slide(name=name, 
                                            course_name=course_name, 
                                            file_data=file_bytes)
        
        for c in chunks:
            content = c.get('content', None)
            if not content: continue 
            content: str = clean_content(text=content)
            
            heading = c.get('heading') or name
            texts.append((heading, content))
            
            storage_uri = self.minio_repo.upload_chunk(chunk_id=c.get("chunk_id"), content=c.get("content"), name=name, course_name=course_name)

            hard_refs.append(Ref(
                db="minio",
                id=storage_uri,
                name=clean_slide_name(heading),
                summary=f"{content[:100]} ......".replace("\n", " "), # Clean summary
                p_num=c["page_num"]
            ))

        if not texts:
            return

        kg_instance: KG_Instance = self.extractor.extract_and_build(texts=texts, course_name=course_name, hard_ref = hard_refs, soft_refs=None)
        nodes, edges, clusters = serialize_kg_to_dict(kg_instance)

        self.graph_db.import_data(db_name=self.db_name, nodes=nodes, edges=edges, clusters=clusters)
        self.milvus_db.insert_data(nodes=nodes, embedder=self.embedder)

        

    def _process_textbook(self,name: str, course_name):
        file_path = self.config.path  + name
        chunks = extract_pdf(file_path, pages_per_batch= self.config.PAGE_PER_TB)
        
        for chunk in chunks:
            text_content = chunk.get("content")
            chunk_id = chunk.get("chunk_id")
            heading = chunk.get("heading", "")
            
            if not text_content:
                continue
                
            storage_uri = self.minio_repo.upload_chunk(
                chunk_id=chunk_id, 
                content=text_content, 
                name=name, 
                course_name=course_name
            )
            search_query = f"{heading}: {text_content}"
            candidates = self.milvus_db.search(query=search_query, embedder=self.embedder, top_k=10)
            
            if not candidates:
                continue
                
            links = self.extractor.link_textbook_to_anchors(text=text_content, candidates=candidates)
            if not links:
                virtual_id = f"ref_{uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id).hex[:8]}"
                links = [{
                    "anchor_id": virtual_id,
                    "justification": f"Text book related directly to course {course_name} "
                }]
            if links:
                self.graph_db.update_links(chunk_id, heading, storage_uri, links, self.db_name)

    def reset_db(self):
        self.graph_db.reset(self.db_name)
        self.milvus_db.reset()
    def run(self, req):
        start = time()
        if req.reset:
            self.reset_db()
        for slide_file in req.slide_files:
            self._process_slide(slide_file, req.course_name)
            
        for textbook_file in req.textbook_files:
            self._process_textbook(textbook_file, req.course_name)
        print(f" ====>  All finished and takes {time()-start}")

    def validate_files(self, names: List[str]):
 
        if not names:
            raise HTTPException(status_code=400, detail="File list is empty.")

        for name in names:
            file_path = self.config.path  + name
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=404, 
                    detail=f"File not found: {file_path}"
                )
            
            # 2. Check extension
            if not file_path.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_path}. Only PDF is allowed."
                )
            
            # 3. Check file size (Optional - e.g., max 50MB)
            if os.path.getsize(file_path) > 50 * 1024 * 1024:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File too large: {file_path}. Max size is 50MB."
                )
        
        return True