import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
from education.services.program_change_service import ProgramChangeService
from models.base import Base
from models.domains.education import Program, ProgramBlock, ProgramTask, ProgramTopic


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _teacher_context(user_id=7):
    return AccessContext.from_parts(user_id=user_id, roles=["teacher"], permissions=["view_programs"], is_admin=False)


def test_teacher_submission_keeps_program_unchanged():
    db = _session()
    program = Program(id=1, title="Admin title", description="Description", created_by=7)
    block = ProgramBlock(id=2, program=program, title="Old block", order=0)
    block.tasks.append(ProgramTask(id=3, title="Old task", max_score=5))
    db.add(program)
    db.commit()

    proposal = ProgramChangeService().create_proposal(
        db,
        ctx=_teacher_context(),
        program_id=1,
        blocks=[{"id": 2, "title": "New block", "description": None, "order": 0, "tasks": []}],
        comment="Please review",
    )

    db.refresh(block)
    assert proposal.status == "PENDING"
    assert block.title == "Old block"
    assert block.tasks[0].title == "Old task"
    assert proposal.proposed_snapshot["blocks"][0]["title"] == "New block"


def test_teacher_with_edit_permission_can_submit_proposal():
    db = _session()
    program = Program(id=1, title="Program", description="Description", created_by=7)
    db.add(program)
    db.commit()

    ctx = AccessContext.from_parts(
        user_id=7,
        roles=["teacher"],
        permissions=["view_programs", "edit_programs"],
        is_admin=False,
    )

    proposal = ProgramChangeService().create_proposal(
        db,
        ctx=ctx,
        program_id=1,
        blocks=[{"id": None, "title": "Proposed block", "description": None, "order": 0, "topics": []}],
        comment="Please review",
    )

    assert proposal.status == "PENDING"
    assert proposal.proposed_snapshot["blocks"][0]["title"] == "Proposed block"


def test_admin_approval_applies_structure_but_not_program_title():
    db = _session()
    program = Program(id=1, title="Admin title", created_by=7)
    block = ProgramBlock(id=2, program=program, title="Old block", order=0)
    db.add(program)
    db.commit()
    service = ProgramChangeService()
    proposal = service.create_proposal(
        db,
        ctx=_teacher_context(),
        program_id=1,
        blocks=[{"id": 2, "title": "New block", "description": None, "order": 0, "tasks": [{"id": None, "title": "New task", "description": None, "max_score": 20, "is_manual": False}]}],
        comment=None,
    )

    admin = AccessContext.from_parts(user_id=1, roles=["admin"], permissions=[], is_admin=True)
    service.decide(db, ctx=admin, proposal_id=proposal.id, approved=True, comment="Approved")

    db.refresh(program)
    assert proposal.status == "APPROVED"
    assert program.title == "Admin title"
    assert program.blocks[0].title == "New block"
    assert program.blocks[0].tasks[0].max_score == 20


def test_teacher_cannot_approve_proposal():
    db = _session()
    program = Program(id=1, title="Admin title", created_by=7)
    db.add(program)
    db.commit()
    service = ProgramChangeService()
    proposal = service.create_proposal(db, ctx=_teacher_context(), program_id=1, blocks=[], comment=None)

    try:
        service.decide(db, ctx=_teacher_context(), proposal_id=proposal.id, approved=True, comment=None)
    except PermissionDenied:
        pass
    else:
        raise AssertionError("Expected PermissionDenied")


def test_topic_is_preserved_in_program_change_snapshot():
    db = _session()
    program = Program(id=1, title="Program", created_by=7)
    block = ProgramBlock(id=2, program=program, title="Block", order=0)
    topic = ProgramTopic(id=4, block=block, title="Topic", order=0)
    topic.tasks.append(ProgramTask(id=5, title="Task", max_score=10, order=0))
    db.add(program)
    db.commit()

    snapshot = ProgramChangeService()._snapshot(db, 1)

    assert snapshot["blocks"][0]["topics"][0]["title"] == "Topic"
    assert snapshot["blocks"][0]["topics"][0]["tasks"][0]["title"] == "Task"