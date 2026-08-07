import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from core.exceptions import ConflictError, NotFoundError, PermissionDenied, to_http_exception
from core.events import DomainEvent, EventBus
from shared.unit_of_work import UnitOfWork


class ExampleEvent(DomainEvent):
    pass


def test_to_http_exception_maps_permission_denied_to_403():
    with pytest.raises(HTTPException) as exc_info:
        to_http_exception(PermissionDenied("forbidden"))
    assert exc_info.value.status_code == 403


def test_to_http_exception_maps_not_found_to_404():
    with pytest.raises(HTTPException) as exc_info:
        to_http_exception(NotFoundError("missing"))
    assert exc_info.value.status_code == 404


def test_to_http_exception_maps_conflict_to_409():
    with pytest.raises(HTTPException) as exc_info:
        to_http_exception(ConflictError("already exists"))
    assert exc_info.value.status_code == 409


def test_event_bus_publishes_events_to_subscribers():
    bus = EventBus()
    received = []
    bus.subscribe(lambda event: received.append(event))

    bus.publish(ExampleEvent())

    assert len(received) == 1


def test_unit_of_work_commits_on_success_and_rolls_back_on_error():
    class FakeSession:
        def __init__(self):
            self.committed = False
            self.rolled_back = False

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    session = FakeSession()

    with UnitOfWork(session):
        pass

    assert session.committed is True
    assert session.rolled_back is False

    session = FakeSession()
    with pytest.raises(RuntimeError):
        with UnitOfWork(session):
            raise RuntimeError("boom")

    assert session.committed is False
    assert session.rolled_back is True


def test_group_creation_service_uses_unit_of_work(monkeypatch):
    from education.services import group_management_service as group_management_module

    class FakeSession:
        def __init__(self):
            self.committed = False
            self.rolled_back = False
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            return None

        def refresh(self, obj):
            return None

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    class FakeRepo:
        def __init__(self):
            self.created_groups = []
            self.created_members = []

        def get_program_by_id(self, db, program_id):
            return None

        def create(self, db, group):
            db.add(group)
            db.flush()
            self.created_groups.append(group)
            return group

        def create_member(self, db, member):
            db.add(member)
            db.flush()
            self.created_members.append(member)
            return member

    fake_repo = FakeRepo()
    monkeypatch.setattr(group_management_module, "group_repository", fake_repo)

    service = group_management_module.GroupManagementService()
    ctx = AccessContext.from_parts(user_id=7, roles=["teacher"], permissions=[], is_admin=False)
    session = FakeSession()

    service.create_group(session, ctx=ctx, title="New group", description=None, program_id=None)

    assert session.committed is True
    assert session.rolled_back is False
    assert len(fake_repo.created_groups) == 1
    assert len(fake_repo.created_members) == 1
