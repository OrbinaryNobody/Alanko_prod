import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from admin.dtos.admin_dto import (
    BlockCreatePayload,
    EnrollmentCreatePayload,
    GroupCreatePayload,
    MemberAddPayload,
    ProgramCreatePayload,
    TaskCreatePayload,
)


def test_program_payload_serializes_expected_fields():
    payload = ProgramCreatePayload(id=1, title="Program", status="draft", description="Desc")
    data = payload.to_dict()
    assert data["title"] == "Program"
    assert data["status"] == "draft"


def test_group_payload_serializes_expected_fields():
    payload = GroupCreatePayload(id=2, title="Group")
    assert payload.to_dict()["id"] == 2


def test_block_payload_serializes_expected_fields():
    payload = BlockCreatePayload(id=3, title="Block", order=1)
    assert payload.to_dict()["order"] == 1


def test_task_payload_serializes_expected_fields():
    payload = TaskCreatePayload(id=4, title="Task", max_score=10)
    assert payload.to_dict()["max_score"] == 10


def test_member_payload_serializes_expected_fields():
    payload = MemberAddPayload(group_id=5, user_id=6, role="student")
    assert payload.to_dict()["role"] == "student"


def test_enrollment_payload_serializes_expected_fields():
    payload = EnrollmentCreatePayload(id=7, student_id=8)
    assert payload.to_dict()["student_id"] == 8
