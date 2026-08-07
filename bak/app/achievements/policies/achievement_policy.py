from core.access import AccessContext


class AchievementPolicy:
    @staticmethod
    def require_manage_achievements(ctx: AccessContext) -> None:
        if ctx.is_admin or ctx.can("manage_achievements"):
            return
        raise PermissionError("Access denied: manage achievements")

    @staticmethod
    def require_view_achievements(ctx: AccessContext) -> None:
        if ctx.is_admin or ctx.can("view_achievements"):
            return
        raise PermissionError("Access denied: view achievements")
