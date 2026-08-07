import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from core.access import AccessContext
from education.policies.program_policy import ProgramPolicy
from education.policies.student_task_policy import StudentTaskPolicy


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, result):
        self.result = result

    def query(self, model):
        return FakeQuery(self.result)


def test_program_policy_allows_owner_and_admin():
    owner_ctx = AccessContext.from_parts(user_id=10, roles=["teacher"], permissions=[], is_admin=False)
    admin_ctx = AccessContext.from_parts(user_id=11, roles=["admin"], permissions=[], is_admin=True)
    program = SimpleNamespace(created_by=10)

    ProgramPolicy.require_edit_program(owner_ctx, program)
    ProgramPolicy.require_view_program(admin_ctx, program)


def test_program_policy_denies_other_user():
    ctx = AccessContext.from_parts(user_id=42, roles=["teacher"], permissions=[], is_admin=False)
    program = SimpleNamespace(created_by=10)

    try:
        ProgramPolicy.require_edit_program(ctx, program)
    except PermissionError:
        pass
    else:
        raise AssertionError("Expected PermissionError for non-owner")


def test_student_task_policy_allows_group_manager():
    ctx = AccessContext.from_parts(user_id=5, roles=["teacher"], permissions=[], is_admin=False)
    enrollment = SimpleNamespace(
        group=SimpleNamespace(created_by=1, members=[SimpleNamespace(user_id=2)]),
        student_id=7,
    )
    student_task = SimpleNamespace(enrollment_id=1)
    db = FakeDB(enrollment)

    try:
        StudentTaskPolicy.require_create_manual_task(ctx, enrollment)
    except PermissionError:
        raise AssertionError("Expected manager to be allowed")

    try:
        StudentTaskPolicy.require_grade(ctx, student_task, db)
    except PermissionError:
        raise AssertionError("Expected manager to be allowed to grade")
