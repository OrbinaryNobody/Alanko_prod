from minio import Minio

from core.config import settings

# Internal address for MinIO within Docker
MINIO_INTERNAL_URL = settings.minio_internal_url or "minio:9000"
# Public URL for accessing MinIO from browser/external clients
MINIO_PUBLIC_URL = settings.minio_public_url or "http://localhost:9000"
# Extract host:port from public URL for replacement (without http://)
MINIO_PUBLIC_HOST = MINIO_PUBLIC_URL.replace("http://", "").replace("https://", "")

minio_client = Minio(
    MINIO_INTERNAL_URL,
    access_key=settings.minio_access_key or "minioadmin",
    secret_key=settings.minio_secret_key or "minioadmin",
    secure=False,
)

# Bucket names for different file types
BUCKET_NAMES = {
    "videos": "alanko-videos",
    "certificates": "alanko-certificates",
    "student_photos": "alanko-student-photos",
    "documents": "alanko-documents"
}

PUBLIC_BUCKETS = {
    BUCKET_NAMES["videos"],
    BUCKET_NAMES["student_photos"],
}

PRIVATE_BUCKETS = {
    BUCKET_NAMES["certificates"],
    BUCKET_NAMES["documents"],
}
