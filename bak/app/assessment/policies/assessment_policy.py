from core.access import AccessContext


class AssessmentPolicy:
    @staticmethod
    def require_view_assessment(ctx: AccessContext) -> None:
        if ctx.is_admin or ctx.can("view_assessment"):
            return
        raise PermissionError("Access denied: view assessment")
