from fastapi import UploadFile

from core.access import AccessContext
from media.services.media_service import media_service


class MediaFacade:
    async def upload_media(self, file: UploadFile, ctx: AccessContext | None = None):
        return await media_service.upload_media(file, ctx=ctx)


media_facade = MediaFacade()
