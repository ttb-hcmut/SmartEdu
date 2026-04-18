# Util package
import hashlib
from time import time
from typing import List
import os
# Core Package
from docling import document_converter
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
# Project Modules
from core.schema.graph.type import Ref
import re
from core.config import PAGE_PER_PDF

def extract_pdf(file_path: str, pages_per_batch: int = PAGE_PER_PDF, step: int = int(PAGE_PER_PDF/3*2+1)) -> List[dict]:
    start = time()
    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document
    
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    doc_name = os.path.splitext(os.path.basename(file_path))[0]

    raw_pages = {} 
    for item, _ in doc.iterate_items():
        if hasattr(item, 'text') and item.text:
            text = item.text.strip()
            if "GLYPH" in text or len(text) < 5: continue
            if re.search(r'Lecturer|Contact|PhD|University|Faculty', text, re.I): continue
            
            page_no = item.prov[0].page_no if item.prov else 1
            if page_no not in raw_pages:
                raw_pages[page_no] = []
            raw_pages[page_no].append(text)

    sorted_page_nos = sorted(raw_pages.keys())
    if not sorted_page_nos: return []
    
    max_page = max(sorted_page_nos)
    page_contents = {p: f"==== PAGE {p} ====\n" + "\n".join(raw_pages.get(p, [])) 
                     for p in range(1, max_page + 1) if raw_pages.get(p)}

    chunks = []
    for idx, start_page in enumerate(range(1, max_page + 1, step)):
        end_page: int = min(start_page + pages_per_batch - 1, max_page)
        
        window_text_list = []
        for p in range(start_page, end_page + 1):
            if page_contents.get(p):
                window_text_list.append(page_contents[p])

        combined_text = "\n".join(window_text_list)
        if not combined_text.strip(): continue

        chuk = {
            "doc_id": file_hash,
            "doc_name": doc_name,
            "chunk_id": f"{file_hash}_slide{idx}",
            "heading": f"{doc_name} - Part {idx+1}",
            "content": combined_text, 
            "page_num": (start_page, end_page)
        }
        chunks.append(chuk)
        #print(f"Heading: {chuk["heading"]} \n Content: {combined_text}")

        #print("==========================================================================================")


    print("==========================================================================================")
    print(f"Extraction completed in {time() - start:.2f}s. Created {len(chunks)} batch chunks.")
    return chunks

def create_refs(chunks: List[dict], storage_type: str = "minio") -> List[Ref]:
    return [
        Ref(
            db=storage_type,
            id=c["chunk_id"],
            name=c["doc_name"],
            summary=c["content"][:200],
            p_num=(c["page_num"], c["page_num"])
        )
        for c in chunks
    ]