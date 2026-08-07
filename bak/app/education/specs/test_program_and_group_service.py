import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from education.dtos.program_dto import BlockPayload, ProgramPayload
from education.services.group_management_service import GroupManagementService
from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied


class FakeDB:
    pass


def test_program_payload_serializes_expected_fields():
    payload = ProgramPayload(id=1, title="Test", description="Desc", status="draft")
    assert payload.to_dict()["title"] == "Test"


def test_block_payload_serializes_expected_fields():
    payload = BlockPayload(id=2, title="Block", order=1, status="draft")
    assert payload.to_dict()["order"] == 1


def test_group_management_service_rejects_unknown_program():
    service = GroupManagementService()
    ctx = AccessContext.from_parts(user_id=1, roles=["teacher"], permissions=[], is_admin=False)

    class FakeRepo:
        def get_program_by_id(self, db, program_id):
            return None

    service.__dict__["repo"] = FakeRepo()
    try:
        service.create_group(FakeDB(), ctx=ctx, title="Group", description=None, program_id=99)
    except PermissionDenied:
        pass
    else:
        raise AssertionError("Expected PermissionDenied")
