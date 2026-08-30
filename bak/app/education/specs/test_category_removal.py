import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from education.schemas.task import TaskCreate, TaskUpdate


def test_task_schema_no_longer_requires_category():
    task = TaskCreate(title="Task title", difficulty=3, max_score=80)

    assert task.title == "Task title"
    assert task.difficulty == 3
    assert task.max_score == 80
    assert "category_id" not in TaskCreate.model_fields
    assert "category_id" not in TaskUpdate.model_fields
