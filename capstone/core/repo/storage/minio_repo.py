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
        self.bucket_name = "courses"
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"MinIO error: {e}")

    def upload_slide(self, name: str, course_name: str, file_data: bytes) -> str:
        name = name.split('.')[0]
        try:
            object_name = f"{course_name}/{name}/{name}.pdf"
            data_stream = io.BytesIO(file_data)
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=len(file_data),
                content_type="application/pdf"
            )
            return f"minio://{self.bucket_name}/{object_name}"
        except S3Error as e:
            logging.error(f"Upload slide error: {e}")
            return None

    def upload_chunk(self,chunk_id: str, content: str, name: str, course_name: str) -> str:
        name = name.split('.')[0]
        try:
            content_bytes = content.encode('utf-8')
            content_stream = io.BytesIO(content_bytes)
            object_name = f"{course_name}/{name}/chunks/{chunk_id}.txt"
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=content_stream,
                length=len(content_bytes),
                content_type="text/plain"
            )
            return f"minio://{self.bucket_name}/{object_name}"
        except S3Error as e:
            logging.error(f"Upload chunk error: {e}")
            return None