from __future__ import annotations

import json
import logging
import uuid
from datetime import timedelta
from io import BytesIO

from fastapi import UploadFile

from core.exceptions import ConflictError
from db.minio_client import BUCKET_NAMES, MINIO_PUBLIC_URL, PRIVATE_BUCKETS, minio_client


class FileService:
    logger = logging.getLogger("alanko.file_service")

    def _ensure_bucket(self, bucket_name: str):
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                self.logger.info("Created bucket: %s", bucket_name)
        except Exception as exc:
            self.logger.warning("Could not ensure bucket %s: %s", bucket_name, exc)

    def init_buckets(self):
        for bucket_name in BUCKET_NAMES.values():
            self._ensure_bucket(bucket_name)

    def set_public_policy(self, bucket_name: str):
        self._ensure_bucket(bucket_name)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                }
            ],
        }
        try:
            minio_client.set_bucket_policy(bucket_name, json.dumps(policy))
        except Exception as exc:
            self.logger.warning("Failed to set policy for bucket %s: %s", bucket_name, exc)

    def get_bucket_policy(self, bucket_name: str):
        try:
            return minio_client.get_bucket_policy(bucket_name)
        except Exception as exc:
            self.logger.warning("Failed to get policy for %s: %s", bucket_name, exc)
            return None

    async def upload_certificate(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["application/pdf"], extension="pdf", bucket_name=BUCKET_NAMES["certificates"])

    async def upload_image(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["image/jpeg", "image/png", "image/gif", "image/webp"], extension="jpg", bucket_name=BUCKET_NAMES["student_photos"])

    async def upload_video(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["video/mp4", "video/mpeg"], extension="mp4", bucket_name=BUCKET_NAMES["videos"])

    async def upload_document(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"], extension="pdf", bucket_name=BUCKET_NAMES["documents"])

    async def upload_achievement_media(self, file: UploadFile) -> str:
        content_type = file.content_type
        if content_type == "application/pdf":
            extension = "pdf"
        elif content_type in ["image/jpeg", "image/jpg"]:
            extension = "jpg"
        elif content_type == "image/png":
            extension = "png"
        elif content_type == "image/webp":
            extension = "webp"
        elif content_type == "image/gif":
            extension = "gif"
        elif content_type in ["video/mp4", "video/mpeg"]:
            extension = "mp4"
        else:
            raise ConflictError(f"Invalid achievement media type: {content_type}")

        return await self._upload_file(file, allowed_types=["application/pdf", "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif", "video/mp4", "video/mpeg"], extension=extension, bucket_name=BUCKET_NAMES["certificates"])

    async def _upload_file(self, file: UploadFile, allowed_types: list[str], extension: str, bucket_name: str) -> str:
        if file.content_type not in allowed_types:
            raise ConflictError(f"Invalid file type: {file.content_type}")

        contents = await file.read()
        MAX_SIZE = 10 * 1024 * 1024
        if len(contents) > MAX_SIZE:
            raise ConflictError("File too large")

        file.file = BytesIO(contents)
        self._ensure_bucket(bucket_name)

        file_id = f"{uuid.uuid4()}.{extension}"
        try:
            minio_client.put_object(bucket_name, file_id, file.file, length=-1, part_size=10 * 1024 * 1024, content_type=file.content_type)
        except Exception as exc:
            self.logger.exception("Failed to upload file to MinIO: %s", exc)
            raise

        return file_id

    def get_signed_file_url(self, file_id: str, bucket_name: str, expires: int = 3600) -> str:
        return minio_client.presigned_get_object(bucket_name, file_id, expires=timedelta(seconds=expires))

    def get_file_url(self, file_id: str, bucket_name: str = BUCKET_NAMES["videos"], expires: int = 3600) -> str:
        if bucket_name in PRIVATE_BUCKETS:
            return self.get_signed_file_url(file_id, bucket_name, expires=expires)
        return f"{MINIO_PUBLIC_URL}/{bucket_name}/{file_id}"


file_service = FileService()
