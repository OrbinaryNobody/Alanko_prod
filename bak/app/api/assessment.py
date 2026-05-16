from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Task, StudentTask
from db.database import get_db
from core.security import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/teacher", tags=["teacher"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# =========================
# Оценка студента для задачи (Assessment)
# =========================
@router.get("/student/{student_id}/task/{task_id}/assessment")
def get_task_assessment(
    student_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Возвращает информацию об оценке выполнения студентом задачи:
    - История оценок студента по похожим задачам
    - Средняя оценка всех студентов по этой задаче
    - Рекомендация сложности (визуальный индикатор)
    """
    
    # Проверка существования студента
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Проверка существования задачи
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Получение всех оценок студента по задачам похожей сложности
    # (сложность ±1 от текущей задачи)
    min_difficulty = max(1, task.difficulty - 1)
    max_difficulty = task.difficulty + 1
    
    student_similar_tasks = (
        db.query(StudentTask)
        .join(Task, StudentTask.task_id == Task.id)
        .filter(
            StudentTask.student_id == student_id,
            Task.difficulty.between(min_difficulty, max_difficulty),
            StudentTask.score > 0  # Только выполненные задания
        )
        .all()
    )
    
    student_scores = [st.score for st in student_similar_tasks]
    student_avg_score = sum(student_scores) / len(student_scores) if student_scores else 0
    
    # Получение средней оценки всех студентов по этой конкретной задаче
    all_task_scores = (
        db.query(StudentTask)
        .filter(
            StudentTask.task_id == task_id,
            StudentTask.score > 0  # Только выполненные задания
        )
        .all()
    )
    
    all_scores = [st.score for st in all_task_scores]
    class_avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Определение уровня подготовки студента
    # Зелёный: student_avg >= class_avg (хорошо подготовлен)
    # Жёлтый: class_avg * 0.7 <= student_avg < class_avg (средне подготовлен)
    # Красный: student_avg < class_avg * 0.7 (слабо подготовлен)
    
    if class_avg_score == 0:
        readiness_level = "unknown"  # Нет данных
        indicator_color = "gray"
    elif student_avg_score >= class_avg_score:
        readiness_level = "good"
        indicator_color = "green"
    elif student_avg_score >= class_avg_score * 0.7:
        readiness_level = "medium"
        indicator_color = "yellow"
    else:
        readiness_level = "poor"
        indicator_color = "red"
    
    # Получение текущего статуса студента по этой задаче
    current_student_task = (
        db.query(StudentTask)
        .filter(
            StudentTask.student_id == student_id,
            StudentTask.task_id == task_id
        )
        .first()
    )
    
    recommendation = _get_recommendation_text(readiness_level)
    
    return {
        "student_id": student_id,
        "task_id": task_id,
        "task": {
            "title": task.title,
            "difficulty": task.difficulty,
            "max_score": task.max_score
        },
        "student_performance": {
            "average_score_similar": round(student_avg_score, 2),
            "tasks_completed_similar": len(student_scores),
            "best_score": max(student_scores) if student_scores else 0,
            "worst_score": min(student_scores) if student_scores else 0
        },
        "class_average": round(class_avg_score, 2),
        "students_completed_task": len(all_scores),
        "assessment": {
            "readiness_level": readiness_level,
            "indicator_color": indicator_color,
            "recommendation": recommendation
        },
        "current_status": {
            "status": current_student_task.status if current_student_task else "not_assigned",
            "score": current_student_task.score if current_student_task else None,
            "comment": current_student_task.comment if current_student_task else None
        }
    }


def _get_recommendation_text(readiness_level: str) -> str:
    """Получить рекомендацию в зависимости от уровня подготовки"""
    recommendations = {
        "good": "✓ Студент хорошо подготовлен к этой задаче",
        "medium": "○ Студент средне подготовлен, может потребоваться помощь",
        "poor": "! Студент слабо подготовлен, рекомендуется дополнительная поддержка",
        "unknown": "? Недостаточно данных для оценки"
    }
    return recommendations.get(readiness_level, "?")
