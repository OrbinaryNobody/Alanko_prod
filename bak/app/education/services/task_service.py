from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import CategoryAlreadyExists, CategoryNotFound, NoStudentsFound, TaskNotFound
from education.repositories.task_repository import task_repository
from models.domains.auth import User
from models.domains.student import Category, Task
from models.domains.auth import Role
from shared.unit_of_work import UnitOfWork


class TaskService:
    def create_category(self, db: Session, *, name: str, description: str | None = None):
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            raise CategoryAlreadyExists("Category with this name already exists")

        with UnitOfWork(db):
            return task_repository.create_category(db, name=name, description=description)

    def get_categories(self, db: Session):
        return task_repository.list_categories(db)

    def create_task(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, category_id: int, difficulty: int, max_score: int):
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise CategoryNotFound("There is no such category")

        with UnitOfWork(db):
            task = task_repository.create_task(
                db,
                title=title,
                description=description,
                category_id=category_id,
                difficulty=difficulty,
                max_score=max_score,
            )

            students = (
                db.query(User)
                .join(User.roles)
                .join(Role)
                .filter(Role.name == "student")
                .all()
            )
            if not students:
                raise NoStudentsFound("No students found")

            task_repository.create_student_tasks(db, student_ids=[student.id for student in students], task_id=task.id)
            return task, len(students)

    def get_tasks(self, db: Session):
        return task_repository.list_tasks(db)

    def get_task(self, db: Session, *, task_id: int):
        task = task_repository.get_task_by_id(db, task_id=task_id)
        if not task:
            raise TaskNotFound("Task not found")
        return task

    def update_task(self, db: Session, *, task_id: int, task_data):
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise TaskNotFound("Task not found")

        with UnitOfWork(db):
            task.title = task_data.title
            task.description = task_data.description
            task.category_id = task_data.category_id
            task.difficulty = task_data.difficulty
            task.max_score = task_data.max_score
            db.refresh(task)
            return task


task_service = TaskService()
