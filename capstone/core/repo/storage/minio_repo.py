import io
from minio import Minio
from minio.error import S3Error
from core.config import Minio_conf
class MinioDB:
    def __init__(self, config: Minio_conf = Minio_conf()):
        self.client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure
        )
        self.bucket_name = "textbooks"
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"MinIO error: {e}")

    def upload_chunk(self, chunk_id: str, content: str) -> str:
        content_bytes = content.encode('utf-8')
        content_stream = io.BytesIO(content_bytes)
        
        object_name = f"{chunk_id}.txt"
        
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=content_stream,
            length=len(content_bytes),
            content_type="text/plain"
        )
        
        return f"minio://{self.bucket_name}/{object_name}"