import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied, ProgramNotFound
from education.services.program_creation_service import ProgramCreationService
from education.services.program_read_service import ProgramReadService


class FakeRepo:
    def __init__(self):
        self.created = []
        self.programs = {}

    def create(self, db, *, title, description, created_by):
        program = SimpleNamespace(id=1, title=title, description=description, created_by=created_by)
        self.created.append(program)
        return program

    def get_by_id(self, db, program_id):
        return self.programs.get(program_id)

    def get_block_by_id(self, db, block_id):
        return None

    def create_block(self, db, **kwargs):
        return SimpleNamespace(id=10, **kwargs)

    def create_task(self, db, **kwargs):
        return SimpleNamespace(id=11, **kwargs)


class FakeDB:
    pass


def test_program_creation_service_requires_permission():
    service = ProgramCreationService()
    ctx = AccessContext.from_parts(user_id=1, roles=["teacher"], permissions=[], is_admin=False)

    try:
        service.create_program(FakeDB(), ctx=ctx, title="Test", description=None)
    except PermissionDenied:
        pass
    else:
        raise AssertionError("Expected PermissionDenied")


def test_program_read_service_raises_not_found_for_missing_program():
    service = ProgramReadService()
    ctx = AccessContext.from_parts(user_id=1, roles=["teacher"], permissions=["view_programs"], is_admin=False)

    try:
        service.get_program_by_id(FakeDB(), ctx=ctx, program_id=999)
    except ProgramNotFound:
        pass
    else:
        raise AssertionError("Expected ProgramNotFound")
