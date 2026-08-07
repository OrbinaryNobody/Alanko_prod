from core.access import AccessContext
from core.exceptions import PermissionDenied


class MediaPolicy:
    @staticmethod
    def require_upload_media(ctx: AccessContext) -> None:
        if ctx.is_admin or ctx.can("upload_media"):
            return
        raise PermissionDenied("Access denied: upload media")
