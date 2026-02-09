import logging
from minio import Minio
from minio.error import S3Error
from io import BytesIO

logger = logging.getLogger(__name__)

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "estate-mind-bronze"


class BronzeStorage:
    """
    MinIO Bronze Layer — stores raw HTML exactly as scraped.

    Rules (from architecture doc):
    - Never modify. Never delete. Append only.
    - Path format: YYYY/MM/DD/{url_hash}.html
    - This is your IMMUTABLE AUDIT TRAIL
    - You can re-process it anytime with a better LLM
    """

    def __init__(
        self,
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        self.bucket = bucket
        self._ensure_bucket()
        logger.info(f"BronzeStorage initialized | bucket={bucket}")

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            else:
                logger.info(f"Bucket exists: {self.bucket}")
        except S3Error as e:
            logger.error(f"MinIO bucket error: {e}")
            raise

    def store_raw_html(self, minio_key: str, raw_html: str) -> bool:
        """
        Store raw HTML in MinIO Bronze layer.

        Args:
            minio_key: Path like "2026/02/08/a36a0d1e51682613.html"
            raw_html: The complete raw HTML string

        Returns:
            True if stored successfully
        """
        try:
            data = raw_html.encode("utf-8")
            stream = BytesIO(data)

            self.client.put_object(
                bucket_name=self.bucket,
                object_name=minio_key,
                data=stream,
                length=len(data),
                content_type="text/html",
            )

            logger.info(f"✅ Bronze stored: {minio_key} ({len(data):,} bytes)")
            return True

        except S3Error as e:
            logger.error(f"❌ MinIO store failed: {e}")
            return False

    def get_raw_html(self, minio_key: str) -> str:
        """Retrieve raw HTML from Bronze layer."""
        try:
            response = self.client.get_object(self.bucket, minio_key)
            html = response.read().decode("utf-8")
            response.close()
            response.release_conn()
            logger.info(f"Retrieved: {minio_key} ({len(html):,} chars)")
            return html
        except S3Error as e:
            logger.error(f"MinIO get failed: {e}")
            return ""

    def list_objects(self, prefix: str = "") -> list:
        """List all objects in Bronze layer (or by date prefix)."""
        objects = []
        try:
            for obj in self.client.list_objects(self.bucket, prefix=prefix, recursive=True):
                objects.append({
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                })
        except S3Error as e:
            logger.error(f"MinIO list failed: {e}")
        return objects

    def exists(self, minio_key: str) -> bool:
        """Check if an object exists in Bronze."""
        try:
            self.client.stat_object(self.bucket, minio_key)
            return True
        except S3Error:
            return False