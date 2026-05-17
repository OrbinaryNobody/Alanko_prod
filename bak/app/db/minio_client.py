from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv()

# Internal address for MinIO within Docker
MINIO_INTERNAL_URL = os.getenv("MINIO_INTERNAL_URL", "minio:9000")
# Public URL for accessing MinIO from browser/external clients
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
# Extract host:port from public URL for replacement (without http://)
MINIO_PUBLIC_HOST = MINIO_PUBLIC_URL.replace("http://", "").replace("https://", "")

minio_client = Minio(
    MINIO_INTERNAL_URL,
    access_key="minioadmin",
    secret_key="rGTVTyi3GYs6f667Ng9F25vB5ReB73GQ",
    secure=False
)

# Bucket names for different file types
BUCKET_NAMES = {
    "videos": "alanko-videos",
    "certificates": "alanko-certificates",
    "student_photos": "alanko-student-photos",
    "documents": "alanko-documents"
}
