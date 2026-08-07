from db.minio_client import PUBLIC_BUCKETS
from services.file_service import file_service

def init_minio():
    """Initialize all MinIO buckets and apply public policy only to public buckets."""
    file_service.init_buckets()
    for bucket_name in PUBLIC_BUCKETS:
        file_service.set_public_policy(bucket_name)
        file_service.get_bucket_policy(bucket_name)
        print(f"Set public policy for public bucket: {bucket_name}")
    print("All MinIO buckets initialized. Public buckets are publicly readable; private buckets remain private.")