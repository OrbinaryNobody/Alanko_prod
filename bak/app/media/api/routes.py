from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.permissions import require_upload_media
from db.database import get_db
from media.dtos.media_dto import UploadMediaPayload
from media.facade import media_facade

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    ctx: AccessContext = Depends(require_upload_media),
    db: Session = Depends(get_db),
):
    file_url = await media_facade.upload_media(file, ctx=ctx)
    return UploadMediaPayload(
        message="uploaded",
        file_url=file_url,
        uploaded_by=ctx.user_id,
    ).to_dict()
