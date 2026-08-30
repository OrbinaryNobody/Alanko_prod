from core.access import AccessContext
from models.domains.education import Program


class ProgramPolicy:
    @staticmethod
    def _has_group_teacher_access(ctx: AccessContext, program: Program) -> bool:
        if not hasattr(program, "groups"):
            return False

        for group in program.groups or []:
            for member in getattr(group, "members", []) or []:
                if getattr(member, "user_id", None) == ctx.user_id and getattr(member, "role", None) == "teacher":
                    return True
        return False

    @staticmethod
    def require_edit_program(ctx: AccessContext, program: Program) -> None:
        if ctx.is_admin or ctx.can_manage(program.created_by):
            return
        if ProgramPolicy._has_group_teacher_access(ctx, program):
            return
        raise PermissionError("Access denied: edit program")

    @staticmethod
    def require_view_program(ctx: AccessContext, program: Program) -> None:
        if ctx.is_admin or ctx.can_manage(program.created_by):
            return
        if ProgramPolicy._has_group_teacher_access(ctx, program):
            return
        raise PermissionError("Access denied: view program")
