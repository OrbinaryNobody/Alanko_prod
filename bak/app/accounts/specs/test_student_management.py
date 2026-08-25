import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from accounts.services import auth_service as auth_service_module
from accounts.schemas.auth import TeacherAddStudentSchema, StudentUpdateSchema


class FakeRoleQuery:
    def __init__(self, role):
        self.role = role

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.role


class FakeDB:
    def __init__(self):
        self.added = []
        self.committed = False
        self.rolled_back = False

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

    def query(self, model):
        return FakeRoleQuery(object())


class FakeUserRepository:
    def __init__(self):
        self.created_user = None

    def get_by_email(self, db, email):
        return None

    def get_by_id(self, db, user_id):
        return None

    def create(self, db, data):
        class FakeUser:
            def __init__(self):
                self.id = 42
                self.email = data["email"]
                self.first_name = data["first_name"]
                self.last_name = data["last_name"]
                self.middle_name = data["middle_name"]
                self.plain_password = data["plain_password"]

        user = FakeUser()
        self.created_user = user
        return user


def test_add_student_by_teacher_stores_birth_year(monkeypatch):
    fake_repo = FakeUserRepository()
    monkeypatch.setattr(auth_service_module, "user_repository", fake_repo)

    db = FakeDB()
    service = auth_service_module.AuthService()

    user, password = service.add_student_by_teacher(
        db,
        data=TeacherAddStudentSchema(
            email="new.student@example.com",
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
            birth_year=2008,
        ),
        image_url="student.png",
    )

    assert user.id == 42
    assert password
    assert db.added[-1].birth_year == 2008


def test_update_student_profile_updates_personal_fields(monkeypatch):
    service = auth_service_module.AuthService()

    class FakeUserProfile:
        def __init__(self):
            self.birth_year = 2005

    class FakeUser:
        def __init__(self):
            self.id = 7
            self.email = "old@example.com"
            self.first_name = "Old"
            self.last_name = "Name"
            self.middle_name = "Middle"
            self.student_profile = FakeUserProfile()

    class FakeRepo:
        def get_by_id(self, db, user_id):
            return FakeUser()

    monkeypatch.setattr(auth_service_module, "user_repository", FakeRepo())

    updated = service.update_student(
        db=object(),
        student_id=7,
        data=StudentUpdateSchema(
            first_name="Новый",
            last_name="Фамилия",
            email="new@example.com",
            birth_year=2010,
        ),
    )

    assert updated.email == "new@example.com"
    assert updated.first_name == "Новый"
    assert updated.last_name == "Фамилия"
    assert updated.student_profile.birth_year == 2010
