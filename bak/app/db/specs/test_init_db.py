import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from db import init_db


class FakeRole:
    def __init__(self, name, id_=None):
        self.name = name
        self.id = id_


class FakeUser:
    def __init__(self, email, roles=None):
        self.email = email
        self.roles = roles or []
        self.id = 1


class FakeUserRole:
    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id


class FakeDB:
    def __init__(self, roles=None):
        self.roles = roles or []
        self.users = []
        self.user_roles = []
        self.added = []

    def query(self, model):
        if model.__name__ == "Role":
            return FakeRoleQuery(self.roles)
        if model.__name__ == "User":
            return FakeUserQuery(self.users)
        raise AssertionError(f"Unexpected model {model}")

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, FakeUser):
            self.users.append(obj)
        elif isinstance(obj, FakeUserRole):
            self.user_roles.append(obj)

    def flush(self):
        return None


class FakeRoleQuery:
    def __init__(self, roles):
        self.roles = roles

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.roles[0] if self.roles else None

    def one(self):
        return self.roles[0] if self.roles else None

    def all(self):
        return self.roles


class FakeUserQuery:
    def __init__(self, users):
        self.users = users

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.users[0] if self.users else None


def test_ensure_user_with_role_creates_secretary_when_missing():
    db = FakeDB(roles=[FakeRole("secretary", id_=7)])

    init_db.ensure_user_with_role(
        db,
        email="secretary@alanko.com",
        password="Secret123!",
        first_name="Секретарь",
        last_name="Служебный",
        middle_name="",
        role_name="secretary",
    )

    created_users = [item for item in db.added if isinstance(item, FakeUser)]
    created_roles = [item for item in db.added if isinstance(item, FakeUserRole)]
    assert len(created_users) == 1
    assert created_users[0].email == "secretary@alanko.com"
    assert len(created_roles) == 1
    assert created_roles[0].role_id == 7
