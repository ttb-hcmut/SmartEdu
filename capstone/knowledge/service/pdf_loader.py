"""
knowledge/service/pdf_loader.py
───────────────────────────────
Load the correct PDF from MinIO for the frontend viewer.

Two ways to ask:
  • by (course, topic)        -> fetch courses/{course}/{topic}/page.pdf
  • by a chunk minio:// uri   -> derive the sibling page.pdf and fetch it
"""

import logging
from typing import Optional

from core.repo.storage.minio_repo import MinioDB

logger = logging.getLogger(__name__)


def topic_pdf_bytes(minio: MinioDB, course_name: str, topic: str) -> Optional[bytes]:
    # fetch a topic's small page pdf; None if missing
    object_name = minio.topic_pdf_object(course_name, topic)
    if not minio.object_exists(object_name):
        return None
    return minio.get_object_bytes(object_name)


def page_pdf_from_chunk_uri(minio: MinioDB, chunk_uri: str) -> Optional[bytes]:
    # chunk uri looks like minio://courses/{course}/{topic}/chunks/{id}.txt
    # walk back to the topic folder and grab its page.pdf
    obj = chunk_uri.replace(f"minio://{minio.bucket_name}/", "")
    if "/chunks/" in obj:
        topic_prefix = obj.split("/chunks/")[0]      # {course}/{topic}
        object_name = f"{topic_prefix}/page.pdf"
    elif obj.endswith("page.pdf"):
        object_name = obj
    else:
        object_name = f"{obj}/page.pdf"
    if not minio.object_exists(object_name):
        return None
    return minio.get_object_bytes(object_name)
