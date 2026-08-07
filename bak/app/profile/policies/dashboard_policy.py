from core.access import AccessContext
from core.exceptions import PermissionDenied


class DashboardPolicy:
    @staticmethod
    def require_view_own_dashboard(ctx: AccessContext) -> None:
        if ctx.is_admin or ctx.can("view_own_dashboard"):
            return
        raise PermissionDenied("Access denied: view own dashboard")

    @staticmethod
    def require_view_own_tasks(ctx: AccessContext) -> None:
        if ctx.is_admin or ctx.can("view_own_tasks"):
            return
        raise PermissionDenied("Access denied: view own tasks")
