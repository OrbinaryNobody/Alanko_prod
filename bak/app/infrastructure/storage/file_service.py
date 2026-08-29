from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from datetime import timedelta

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from core.exceptions import ConflictError
from db.minio_client import BUCKET_NAMES, MINIO_PUBLIC_URL, PRIVATE_BUCKETS, minio_client, public_minio_client


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

    def set_private_policy(self, bucket_name: str):
        self._ensure_bucket(bucket_name)
        try:
            minio_client.delete_bucket_policy(bucket_name)
        except Exception as exc:
            self.logger.warning("Failed to remove public policy for bucket %s: %s", bucket_name, exc)

    async def upload_certificate(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["application/pdf"], extension="pdf", bucket_name=BUCKET_NAMES["certificates"])

    async def upload_image(self, file: UploadFile) -> str:
        content_type = file.content_type or ""
        if not content_type and file.filename:
            content_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(os.path.splitext(file.filename)[1].lower(), "")
        extension = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/webp": "webp",
        }.get(content_type)
        if not extension:
            raise ConflictError(f"Invalid image type: {content_type or file.filename}")
        return await self._upload_file(
            file,
            allowed_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
            extension=extension,
            bucket_name=BUCKET_NAMES["student_photos"],
            content_type=content_type,
        )

    async def upload_news_image(self, file: UploadFile) -> str:
        extension = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }.get(file.content_type)
        if not extension:
            raise ConflictError(f"Invalid file type: {file.content_type}")
        return await self._upload_file(
            file,
            allowed_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
            extension=extension,
            bucket_name=BUCKET_NAMES["news"],
        )

    async def upload_video(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["video/mp4", "video/mpeg"], extension="mp4", bucket_name=BUCKET_NAMES["videos"])

    async def upload_achievement_video(self, file: UploadFile) -> str:
        return await self._upload_file(
            file,
            allowed_types=["video/mp4", "video/mpeg"],
            extension="mp4",
            bucket_name=BUCKET_NAMES["achievement_videos"],
        )

    async def upload_document(self, file: UploadFile) -> str:
        return await self._upload_file(file, allowed_types=["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"], extension="pdf", bucket_name=BUCKET_NAMES["documents"])

    async def upload_material(self, file: UploadFile) -> str:
        content_type = file.content_type or "application/octet-stream"
        extensions = {
            "application/pdf": "pdf",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/vnd.ms-excel": "xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
            "application/vnd.ms-powerpoint": "ppt",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
            "text/plain": "txt",
            "audio/mpeg": "mp3",
            "audio/wav": "wav",
            "video/mp4": "mp4",
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }
        extension = extensions.get(content_type)
        if not extension:
            raise ConflictError(f"Invalid material type: {content_type}")
        return await self._upload_file(
            file,
            allowed_types=[content_type],
            extension=extension,
            bucket_name=BUCKET_NAMES["documents"],
            content_type=content_type,
        )

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

    async def _upload_file(
        self,
        file: UploadFile,
        allowed_types: list[str],
        extension: str,
        bucket_name: str,
        content_type: str | None = None,
    ) -> str:
        effective_content_type = content_type or file.content_type
        if effective_content_type not in allowed_types:
            raise ConflictError(f"Invalid file type: {effective_content_type}")

        max_size = 512 * 1024 * 1024
        file_id = f"{uuid.uuid4()}.{extension}"
        file_size = 0
        with tempfile.NamedTemporaryFile(mode="w+b") as temporary_file:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > max_size:
                    raise ConflictError("File too large")
                temporary_file.write(chunk)

            temporary_file.flush()
            temporary_file.seek(0)
            await run_in_threadpool(self._ensure_bucket, bucket_name)
            try:
                await run_in_threadpool(
                    self._put_object,
                    bucket_name,
                    file_id,
                    temporary_file,
                    file_size,
                    effective_content_type,
                )
            except Exception:
                self.logger.exception("Failed to upload file to MinIO")
                raise

        return file_id

    @staticmethod
    def _put_object(bucket_name: str, file_id: str, file_object, file_size: int, content_type: str | None):
        minio_client.put_object(
            bucket_name,
            file_id,
            file_object,
            length=file_size,
            part_size=10 * 1024 * 1024,
            content_type=content_type,
        )

    def get_signed_file_url(self, file_id: str, bucket_name: str, expires: int = 3600) -> str:
        return public_minio_client.presigned_get_object(bucket_name, file_id, expires=timedelta(seconds=expires))

    def get_file_url(self, file_id: str, bucket_name: str = BUCKET_NAMES["videos"], expires: int = 3600) -> str:
        if bucket_name in PRIVATE_BUCKETS:
            return self.get_signed_file_url(file_id, bucket_name, expires=expires)
        return f"{MINIO_PUBLIC_URL}/{bucket_name}/{file_id}"

    def delete_file(self, file_id: str, bucket_name: str) -> None:
        try:
            minio_client.remove_object(bucket_name, file_id)
        except Exception:
            self.logger.exception("Failed to delete file %s from %s", file_id, bucket_name)


file_service = FileService()
