from db.minio_client import PRIVATE_BUCKETS, PUBLIC_BUCKETS
from infrastructure.storage.file_service import file_service

def init_minio():
    """Initialize all MinIO buckets and apply public policy only to public buckets."""
    file_service.init_buckets()
    for bucket_name in PUBLIC_BUCKETS:
        file_service.set_public_policy(bucket_name)
        file_service.get_bucket_policy(bucket_name)
        print(f"Set public policy for public bucket: {bucket_name}")
    for bucket_name in PRIVATE_BUCKETS:
        file_service.set_private_policy(bucket_name)
        print(f"Set private policy for private bucket: {bucket_name}")
    print("All MinIO buckets initialized with explicit public/private policies.")