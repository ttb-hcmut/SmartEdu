import json
import io
from typing import List, Union, Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

try:
    import fitz # PyMuPDF
except ImportError:
    fitz = None

from core.repo.graph.graphdb import GraphDB
from core.repo.storage.minio_repo import MinioDB

class ConceptInput(BaseModel):
    concept: str = Field(description="Tên khái niệm cần tìm kiếm trong tài liệu.")
    
class GetConcept(BaseTool):
    name: str = "get_concept_page"
    description: str = "Tìm kiếm số trang chứa khái niệm trong tài liệu một cách cực nhanh bằng Knowledge Graph."
    args_schema: Type[BaseModel] = ConceptInput
    engine: GraphDB
    
    def _run(self, concept: str) -> str:
        # Match (c:Concept)-[:HAS_REF]->(r)
        query = """
        MATCH (c:Concept)-[:HAS_REF]->(r)
        WHERE toLower(c.name) CONTAINS toLower($concept)
        RETURN c.name AS concept_name, r.p_num AS page, r.summary AS summary, r.storage_uri AS storage_uri
        LIMIT 5
        """
        res = self.engine.run_query("test", query, {"concept": concept})
        if not res:
            return json.dumps({"error": f"Không tìm thấy khái niệm '{concept}' trong tài liệu."})
        return json.dumps(res, ensure_ascii=False, indent=2)

class PagesInput(BaseModel):
    pages: List[int] = Field(description="Danh sách các trang cần đọc nội dung (vd: [5, 6]).")
    destination: str = Field(description="Đường dẫn file trên MinIO (từ active_resource).")

class GetPages(BaseTool):
    name: str = "get_pdf_pages"
    description: str = "Trích xuất nội dung text từ các trang cụ thể của file PDF đang mở."
    args_schema: Type[BaseModel] = PagesInput
    minio: MinioDB
    
    def _run(self, pages: List[int], destination: str) -> str:
        if fitz is None:
            return json.dumps({"error": "PyMuPDF (fitz) chưa được cài đặt."})
        try:
            # Parse destination: courses/ML/slide_1/slide_1.pdf
            obj_name = destination.replace(f"minio://{self.minio.bucket_name}/", "")
            if obj_name.startswith("minio://"):
                obj_name = obj_name.split("/", 3)[-1]
            
            response = self.minio.client.get_object(self.minio.bucket_name, obj_name)
            pdf_data = response.read()
            response.close()
            response.release_conn()
            
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            content = []
            for p in pages:
                if p > 0 and p <= len(doc):
                    page_obj = doc.load_page(p - 1)
                    content.append(f"--- PAGE {p} ---\n{page_obj.get_text()}")
                else:
                    content.append(f"--- PAGE {p} (KHÔNG TỒN TẠI) ---")
            
            return "\n\n".join(content)
        except Exception as e:
            return json.dumps({"error": f"Lỗi đọc file PDF từ MinIO: {str(e)}"})

class FEToolInput(BaseModel):
    page: int = Field(description="Số trang để Frontend lật tới.")
    destination: str = Field(description="Tài liệu đang xét (từ active_resource).")
    
class FEToPage(BaseTool):
    name: str = "navigate_frontend_page"
    description: str = "Phát tín hiệu điều khiển giao diện Frontend lật sang một trang cụ thể của tài liệu."
    args_schema: Type[BaseModel] = FEToolInput
    
    def _run(self, page: int, destination: str) -> str:
        # Tool này không thao tác hệ thống mà chỉ nhả JSON cho luồng LangGraph trả về FE
        res = {
            "action": "NAVIGATE_PDF",
            "destination": destination,
            "page": page
        }
        return json.dumps(res, ensure_ascii=False)
