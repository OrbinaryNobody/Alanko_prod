from core.access import AccessContext
from models.domains.education import Program


class ProgramPolicy:
    @staticmethod
    def require_edit_program(ctx: AccessContext, program: Program) -> None:
        if ctx.is_admin or ctx.can_manage(program.created_by):
            return
        raise PermissionError("Access denied: edit program")

    @staticmethod
    def require_view_program(ctx: AccessContext, program: Program) -> None:
        if ctx.is_admin or ctx.can_manage(program.created_by):
            return
        raise PermissionError("Access denied: view program")
