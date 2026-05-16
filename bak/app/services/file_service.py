from datetime import timedelta
import uuid
import json
import logging
from fastapi import UploadFile, HTTPException
from db.minio_client import minio_client, BUCKET_NAMES, MINIO_INTERNAL_URL, MINIO_PUBLIC_URL, MINIO_PUBLIC_HOST


class FileService:

    logger = logging.getLogger("alanko.file_service")

    # =========================
    # INIT BUCKETS
    # =========================
    def _ensure_bucket(self, bucket_name: str):
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"✅ Created bucket: {bucket_name}")
        
        # Always set public read policy for images and certificates
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        try:
            minio_client.set_bucket_policy(bucket_name, json.dumps(policy))
            print(f"✅ Set public policy for bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ Failed to set policy for bucket {bucket_name}: {e}")

    # =========================
    # INIT ALL BUCKETS WITH PUBLIC POLICY
    # =========================
    def init_buckets(self):
        """Initialize all buckets with public read policy"""
        for bucket_name in BUCKET_NAMES.values():
            self._ensure_bucket(bucket_name)

    # =========================
    # SET PUBLIC POLICY FOR EXISTING BUCKETS
    # =========================
    def set_public_policy(self, bucket_name: str):
        """Set public read policy for an existing bucket"""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        try:
            minio_client.set_bucket_policy(bucket_name, json.dumps(policy))
            print(f"✅ Set public policy for bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ Failed to set policy for bucket {bucket_name}: {e}")

    # =========================
    # GET CURRENT BUCKET POLICY
    # =========================
    def get_bucket_policy(self, bucket_name: str):
        """Get current bucket policy"""
        try:
            policy = minio_client.get_bucket_policy(bucket_name)
            print(f"📋 Current policy for {bucket_name}: {policy}")
            return policy
        except Exception as e:
            print(f"❌ Failed to get policy for bucket {bucket_name}: {e}")
            return None

    # =========================
    # UPLOAD PDF (certificates)
    # =========================
    async def upload_certificate(self, file: UploadFile) -> str:
        return await self._upload_file(
            file,
            allowed_types=["application/pdf"],
            extension="pdf",
            bucket_name=BUCKET_NAMES["certificates"]
        )

    # =========================
    # UPLOAD IMAGE (student photos)
    # =========================
    async def upload_image(self, file: UploadFile) -> str:
        return await self._upload_file(
            file,
            allowed_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
            extension="jpg",
            bucket_name=BUCKET_NAMES["student_photos"]
        )

    # =========================
    # UPLOAD VIDEO
    # =========================
    async def upload_video(self, file: UploadFile) -> str:
        return await self._upload_file(
            file,
            allowed_types=["video/mp4", "video/mpeg"],
            extension="mp4",
            bucket_name=BUCKET_NAMES["videos"]
        )

    # =========================
    # UPLOAD DOCUMENT (site documents)
    # =========================
    async def upload_document(self, file: UploadFile) -> str:
        return await self._upload_file(
            file,
            allowed_types=["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            extension="pdf",
            bucket_name=BUCKET_NAMES["documents"]
        )

    # =========================
    # UPLOAD ACHIEVEMENT MEDIA
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
            raise HTTPException(status_code=400, detail=f"Invalid achievement media type: {content_type}")

        return await self._upload_file(
            file,
            allowed_types=[
                "application/pdf",
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp",
                "image/gif",
                "video/mp4",
                "video/mpeg"
            ],
            extension=extension,
            bucket_name=BUCKET_NAMES["certificates"]
        )

    # =========================
    # CORE UPLOAD METHOD
    # =========================
    async def _upload_file(
        self,
        file: UploadFile,
        allowed_types: list[str],
        extension: str,
        bucket_name: str
    ) -> str:

        # 1. content type check
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

        # 2. read file
        contents = await file.read()

        # 3. size limit (10MB default)
        MAX_SIZE = 10 * 1024 * 1024
        if len(contents) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File too large")

        # reset pointer
        from io import BytesIO
        file.file = BytesIO(contents)

        # 4. ensure bucket
        self._ensure_bucket(bucket_name)

        # 5. generate file id
        file_id = f"{uuid.uuid4()}.{extension}"

        # 6. upload
        try:
            self.logger.info("Uploading file to bucket=%s id=%s size=%d content_type=%s", bucket_name, file_id, len(contents), file.content_type)
            minio_client.put_object(
                bucket_name,
                file_id,
                file.file,
                length=-1,
                part_size=10 * 1024 * 1024,
                content_type=file.content_type
            )
        except Exception as e:
            self.logger.exception("Failed to upload file to MinIO: %s", e)
            raise

        self.logger.info("Upload complete: %s/%s", bucket_name, file_id)
        return file_id

    # =========================
    # GET SIGNED URL
    # =========================
    def get_file_url(self, file_id: str, bucket_name: str = BUCKET_NAMES["videos"], expires: int = 3600) -> str:
        """Generate public URL for files in public buckets"""
        # For public buckets, use direct URL without presigned
        # Format: http://host:port/bucket/file
        public_url = f"{MINIO_PUBLIC_URL}/{bucket_name}/{file_id}"
        self.logger.info("Generated public URL: %s", public_url)
        return public_url


file_service = FileService()