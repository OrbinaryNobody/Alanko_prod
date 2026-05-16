from db.minio_client import minio_client, BUCKET_NAMES
from services.file_service import file_service

def init_minio():
    """Initialize all MinIO buckets with public policy"""
    file_service.init_buckets()
    # Also set public policy for existing buckets
    for bucket_name in BUCKET_NAMES.values():
        if minio_client.bucket_exists(bucket_name):
            file_service.set_public_policy(bucket_name)
            file_service.get_bucket_policy(bucket_name)
            print(f"Set public policy for bucket: {bucket_name}")
    print("All buckets initialized with public read policy")