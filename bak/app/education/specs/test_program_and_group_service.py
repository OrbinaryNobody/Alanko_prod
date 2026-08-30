import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from education.dtos.program_dto import BlockPayload, ProgramPayload
from education.services.group_management_service import GroupManagementService
from education.services.group_service import GroupService
from education.services.program_creation_service import ProgramCreationService
from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
import education.services.program_creation_service as program_creation_service_module


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


def test_group_journal_task_payload_includes_student_task_id_and_program_task_id():
    task = SimpleNamespace(
        id=12,
        grade=8,
        feedback="good",
        status="completed",
        program_task_id=7,
        media=[],
        program_task=SimpleNamespace(
            id=7,
            title="Сделать видео",
            description="Нужно прислать ролик",
            max_score=10,
        ),
    )

    payload = GroupService._group_journal_task_payload(task)

    assert payload["student_task_id"] == 12
    assert payload["task_id"] == 7
    assert payload["title"] == "Сделать видео"
    assert payload["grade"] == 8
    assert payload["feedback"] == "good"
    assert payload["videos"] == []


def test_group_journal_includes_block_and_topic_materials():
    topic_material = SimpleNamespace(id=11, file_name="topic-file.pdf", content_type="application/pdf", file_url="topic-file.pdf", created_at=None)
    block_material = SimpleNamespace(id=12, file_name="block-file.pdf", content_type="application/pdf", file_url="block-file.pdf", created_at=None)
    topic = SimpleNamespace(
        id=3,
        title="Тема",
        description="Описание темы",
        order=1,
        tasks=[],
        materials=[topic_material],
    )
    block = SimpleNamespace(
        id=5,
        title="Блок",
        description="Описание блока",
        order=1,
        topics=[topic],
        materials=[block_material],
    )
    group = SimpleNamespace(
        id=4,
        title="Группа 1",
        description="Описание группы",
        program_id=9,
        program=SimpleNamespace(
            id=9,
            title="Программа",
            description="Описание программы",
            blocks=[block],
        ),
        enrollments=[],
    )

    service = GroupService()
    service.ensure_group_access = lambda db, ctx, group_id: group

    payload = service.get_group_journal(FakeDB(), ctx=SimpleNamespace(user_id=1, is_admin=True), group_id=4)

    assert payload["program"]["blocks"][0]["materials"][0]["file_name"] == "block-file.pdf"
    assert payload["program"]["blocks"][0]["topics"][0]["materials"][0]["file_name"] == "topic-file.pdf"


def test_program_creation_service_assigns_new_task_to_program_students():
    class FakeQuery:
        def __init__(self, rows):
            self.rows = rows

        def join(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return self.rows

        def first(self):
            return self.rows[0] if self.rows else None

    class FakeDB:
        def __init__(self):
            self.added = []
            self.queries = {
                "GroupEnrollment": FakeQuery([SimpleNamespace(id=10), SimpleNamespace(id=11)]),
                "GroupStudentTask": FakeQuery([]),
            }

        def query(self, model):
            name = model.__name__
            return self.queries.get(name, FakeQuery([]))

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            return None

    service = ProgramCreationService()
    db = FakeDB()
    block = SimpleNamespace(id=5, program_id=7, topics=[])
    program = SimpleNamespace(id=7)
    created_task = SimpleNamespace(id=99)

    original_get_block_by_id = program_creation_service_module.program_repository.get_block_by_id
    original_get_by_id = program_creation_service_module.program_repository.get_by_id
    original_create_task = program_creation_service_module.program_repository.create_task

    try:
        program_creation_service_module.program_repository.get_block_by_id = lambda db_arg, block_id: block
        program_creation_service_module.program_repository.get_by_id = lambda db_arg, program_id: program
        program_creation_service_module.program_repository.create_task = lambda db_arg, **kwargs: created_task

        task = service.create_task(
            db,
            ctx=AccessContext.from_parts(user_id=1, roles=["teacher"], permissions=[], is_admin=False),
            block_id=5,
            topic_id=None,
            title="Новая задача",
            description="Описание",
            max_score=10,
            is_manual=False,
        )
    finally:
        program_creation_service_module.program_repository.get_block_by_id = original_get_block_by_id
        program_creation_service_module.program_repository.get_by_id = original_get_by_id
        program_creation_service_module.program_repository.create_task = original_create_task

    assert task is created_task
    assert len(db.added) == 2
    assert {obj.enrollment_id for obj in db.added} == {10, 11}
    assert all(obj.program_task_id == 99 for obj in db.added)
