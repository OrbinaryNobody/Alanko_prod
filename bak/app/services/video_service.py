from fastapi import UploadFile
from db.minio_client import minio_client, BUCKET_NAMES, MINIO_INTERNAL_URL
import uuid


async def upload_video_to_minio(file: UploadFile):
    file_id = f"{uuid.uuid4()}.mp4"
    bucket_name = BUCKET_NAMES["videos"]

    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    minio_client.put_object(
        bucket_name,
        file_id,
        file.file,
        length=-1,
        part_size=10 * 1024 * 1024
    )

    return file_id