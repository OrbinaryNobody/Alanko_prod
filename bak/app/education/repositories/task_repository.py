from sqlalchemy.orm import Session, joinedload

from models.domains.student import Category, StudentTask, Task


class TaskRepository:
    def create_category(self, db: Session, *, name: str, description: str | None = None) -> Category:
        category = Category(name=name, description=description)
        db.add(category)
        db.flush()
        db.refresh(category)
        return category

    def list_categories(self, db: Session) -> list[Category]:
        return db.query(Category).all()

    def create_task(self, db: Session, *, title: str, description: str | None, category_id: int, difficulty: int, max_score: int) -> Task:
        task = Task(
            title=title,
            description=description,
            category_id=category_id,
            difficulty=difficulty,
            max_score=max_score,
        )
        db.add(task)
        db.flush()
        db.refresh(task)
        return task

    def create_student_tasks(self, db: Session, *, student_ids: list[int], task_id: int) -> list[StudentTask]:
        student_tasks = [
            StudentTask(student_id=student_id, task_id=task_id, status="not_started")
            for student_id in student_ids
        ]
        if student_tasks:
            db.bulk_save_objects(student_tasks)
            db.flush()
        return student_tasks

    def get_task_by_id(self, db: Session, *, task_id: int) -> Task | None:
        return db.query(Task).options(joinedload(Task.category)).filter(Task.id == task_id).first()

    def list_tasks(self, db: Session) -> list[Task]:
        return db.query(Task).options(joinedload(Task.category)).all()

    def get_student_task_by_id(self, db: Session, *, student_task_id: int) -> StudentTask | None:
        return db.query(StudentTask).filter(StudentTask.id == student_task_id).first()


task_repository = TaskRepository()
