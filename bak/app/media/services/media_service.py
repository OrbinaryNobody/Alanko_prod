from fastapi import UploadFile

from core.access import AccessContext
from core.exceptions import PermissionDenied
from media.policies.media_policy import MediaPolicy
from infrastructure.storage.file_service import file_service


class MediaService:
    async def upload_media(self, file: UploadFile, *, ctx: AccessContext):
        try:
            MediaPolicy.require_upload_media(ctx)
        except PermissionDenied as exc:
            raise PermissionDenied("Access denied to upload media") from exc
        return await file_service.upload_video(file)


media_service = MediaService()
