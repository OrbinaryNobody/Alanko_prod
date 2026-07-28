from core.access import AccessContext
from models import Group
from typing import Any


class GroupPolicy:
    @staticmethod
    def require_manage_group(ctx: AccessContext, group: Group) -> None:
        if ctx.is_admin:
            return
        if group.created_by == ctx.user_id:
            return
        if any(member.user_id == ctx.user_id for member in group.members):
            return
        raise PermissionError("Access denied: manage group")

    @staticmethod
    def require_view_group(ctx: AccessContext, group: Group) -> None:
        if ctx.is_admin:
            return
        if group.created_by == ctx.user_id:
            return
        if any(member.user_id == ctx.user_id for member in group.members):
            return
        raise PermissionError("Access denied: view group")
