from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied, ProgramNotFound
from education.policies.program_policy import ProgramPolicy
from education.repositories.program_repository import program_repository


class ProgramReadService:
    def ensure_program_access(self, db: Session, *, ctx: AccessContext, program_id: int):
        program = program_repository.get_by_id(db, program_id)
        if not program:
            raise ProgramNotFound("Program not found")

        if ctx.is_admin or ctx.can_manage(program.created_by):
            return program

        if program_repository.has_teacher_access(db, user_id=ctx.user_id, program_id=program.id):
            return program

        try:
            ProgramPolicy.require_view_program(ctx, program)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to program") from exc

        return program

    def get_programs_for_user(self, db: Session, *, ctx: AccessContext):
        return program_repository.list_for_user(db, user_id=ctx.user_id, is_admin=ctx.is_admin)

    def get_program_by_id(self, db: Session, *, ctx: AccessContext, program_id: int):
        return self.ensure_program_access(db, ctx=ctx, program_id=program_id)


program_read_service = ProgramReadService()
