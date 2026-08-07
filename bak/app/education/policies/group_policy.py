from typing import Any

from core.access import AccessContext
from models.domains.education import Group


class GroupPolicy:
    @staticmethod
    def require_manage_group(ctx: AccessContext, group: Group) -> None:
        if ctx.is_admin or ctx.can_manage(group.created_by):
            return
        if any(member.user_id == ctx.user_id for member in group.members):
            return
        raise PermissionError("Access denied: manage group")

    @staticmethod
    def require_view_group(ctx: AccessContext, group: Group) -> None:
        if ctx.is_admin or ctx.can_manage(group.created_by):
            return
        if any(member.user_id == ctx.user_id for member in group.members):
            return
        raise PermissionError("Access denied: view group")
