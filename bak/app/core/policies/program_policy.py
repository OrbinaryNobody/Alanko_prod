from core.access import AccessContext
from models import Program


class ProgramPolicy:
    @staticmethod
    def require_edit_program(ctx: AccessContext, program: Program) -> None:
        if ctx.is_admin:
            return
        if program.created_by == ctx.user_id:
            return
        raise PermissionError("Access denied: edit program")

    @staticmethod
    def require_view_program(ctx: AccessContext, program: Program) -> None:
        if ctx.is_admin:
            return
        if program.created_by == ctx.user_id:
            return
        raise PermissionError("Access denied: view program")
