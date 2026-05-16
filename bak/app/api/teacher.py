from datetime import datetime
import logging

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from models.all_models import Achievement, User, UserAchievement, UserRole
from schemas.achievment import AchievementCreate, AssignAchievement
from schemas.auth import TeacherAddStudentSchema
from core.security import verify_token
from db.database import get_db
from db.minio_client import BUCKET_NAMES
from services.file_service import file_service
from services.auth_service import auth_service

from models import TaskMedia, Task, StudentTask, StudentProfile, RatingsHistory, Category

from schemas.task import TaskCreate, TaskUpdate, StudentTaskUpdate, CategoryCreate

from repositories.user_repository import UserRepository

router = APIRouter(prefix="/teacher", tags=["teacher"])
security = HTTPBearer()

logger = logging.getLogger("alanko.teacher")


# =========================
# Зависимость для получения текущего пользователя из токена
# =========================
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# =========================
# Зависимость для проверки роли учителя или админа
# =========================
def get_current_teacher_or_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.id == current_user["user_id"])
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role_names = [
        ur.role.name
        for ur in user.roles
    ]

    if not any(role in ["teacher", "admin"] for role in role_names):
        raise HTTPException(
            status_code=403,
            detail="Teacher or admin required"
        )

    return user.id


# =========================
# Добавление студента учителем с фото и автопаролем
# =========================
@router.post("/add-student")
async def add_student(
    first_name: str = Form(...),
    last_name: str = Form(None),
    middle_name: str = Form(...),
    email: str = Form(...),
    image: UploadFile = File(...),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    try:
        # Загружаем фото
        image_url = await file_service.upload_image(image)

        # Создаём схему данных студента
        student_data = TeacherAddStudentSchema(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name
        )

        # Добавляем студента с автогенерируемым паролем
        user, generated_password = auth_service.add_student_by_teacher(
            db, student_data, image_url
        )

        # Прикрепляем все существующие задания к новому студенту
        tasks = db.query(Task).all()
        if tasks:
            student_tasks = [
                StudentTask(
                    student_id=user.id,
                    task_id=task.id,
                    status="not_started"
                )
                for task in tasks
            ]
            db.bulk_save_objects(student_tasks)
            db.commit()

        return {
            "message": "Student added successfully",
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "password": generated_password,
            "image_url": file_service.get_file_url(image_url, BUCKET_NAMES["student_photos"])
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error: {str(exc)}")


# =========================
# Загрузка видео
# =========================
@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    student_task_id: int = Form(...),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):

    # =========================
    # Проверка задания студента
    # =========================
    student_task = (
        db.query(StudentTask)
        .filter(StudentTask.id == student_task_id)
        .first()
    )

    if not student_task:
        raise HTTPException(
            status_code=404,
            detail="Student task not found"
        )

    # =========================
    # Проверка ученика
    # =========================
    student = db.query(User).filter(
        User.id == student_task.student_id
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    # =========================
    # Upload файла
    # =========================
    file_id = await file_service.upload_video(file)

    # =========================
    # Создание media
    # =========================
    media = TaskMedia(
        student_task_id=student_task.id,
        uploaded_by=teacher_id,
        video_url=file_id
    )

    student_task.status = "completed"
    student_task.reviewed_at = func.now()
    student_task.completed_at = func.now()
    db.add(media)
    db.commit()
    db.refresh(media)

    return {
        "message": "video uploaded",
        "media_id": media.id,
        "student_id": student.id,
        "student_task_id": student_task.id,
        "video_id": file_id,
        "video_url": file_service.get_file_url(file_id, BUCKET_NAMES["videos"]),
        "status": student_task.status,
        "has_video": True
    }


# =========================
# Создание задания
# =========================
@router.post("/create-task")
def create_task(
    data: TaskCreate,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    # Проверяем существование категории
    category = db.query(Category).filter(Category.id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="There is no such category")

    # 1. создаём задание
    task = Task(
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        difficulty=data.difficulty,
        max_score=data.max_score
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 2. получаем студентов (через repository)
    students = UserRepository.get_students(db)

    if not students:
        raise HTTPException(status_code=400, detail="No students found")

    # 3. создаём задания студентам
    student_tasks = [
        StudentTask(
            student_id=student.id,
            task_id=task.id,
            status="not_started"
        )
        for student in students
    ]

    # ⚡ bulk insert (эффективно)
    db.bulk_save_objects(student_tasks)
    db.commit()

    return {
        "message": "task created and assigned",
        "task_id": task.id,
        "students_count": len(student_tasks)
    }



# =========================
# Создание категории
# =========================
@router.post("/create-category")
def create_category(
    data: CategoryCreate,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    # Проверяем, существует ли категория с таким именем
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    # Создаём новую категорию
    category = Category(
        name=data.name,
        description=data.description
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "message": "Category created successfully",
        "category_id": category.id,
        "name": category.name
    }


# =========================
# Получить список заданий
@router.get("/tasks")
def get_tasks(
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    tasks = (
        db.query(Task)
        .options(joinedload(Task.category))
        .all()
    )

    return {
        "data": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "category_id": task.category_id,
                "category_name": task.category.name if task.category else None,
                "difficulty": task.difficulty,
                "max_score": task.max_score,
                "deadline": None
            }
            for task in tasks
        ]
    }


# =========================
# Обновить задание
@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = task_data.title
    task.description = task_data.description
    task.category_id = task_data.category_id
    task.difficulty = task_data.difficulty
    task.max_score = task_data.max_score

    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated successfully",
        "data": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category_id": task.category_id,
            "category_name": task.category.name if task.category else None,
            "difficulty": task.difficulty,
            "max_score": task.max_score,
            "deadline": None
        }
    }


# =========================
# Обновить статус и оценку задания студента
@router.put("/student-tasks/{student_task_id}")
def update_student_task(
    student_task_id: int,
    student_task_data: StudentTaskUpdate,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    student_task = db.query(StudentTask).filter(StudentTask.id == student_task_id).first()
    if not student_task:
        raise HTTPException(status_code=404, detail="Student task not found")

    original_score = student_task.score or 0

    if student_task_data.score is not None:
        if student_task_data.score < 0:
            raise HTTPException(status_code=400, detail="Score cannot be negative")
        if student_task.task and student_task.task.max_score is not None and student_task_data.score > student_task.task.max_score:
            raise HTTPException(status_code=400, detail=f"Score cannot exceed max_score of {student_task.task.max_score}")
        student_task.score = student_task_data.score

    if student_task_data.status is not None:
        student_task.status = student_task_data.status
        if student_task.status == "completed":
            student_task.reviewed_at = func.now()
            student_task.completed_at = func.now()

    if student_task_data.comment is not None:
        student_task.comment = student_task_data.comment

    new_score = student_task.score or 0
    score_delta = new_score - original_score

    if score_delta != 0:
        student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_task.student_id).first()
        if student_profile:
            student_profile.rating_points = (student_profile.rating_points or 0) + score_delta
            history_reason = f"Обновлена оценка задания: {student_task.task.title or student_task.task_id}"
            db.add(RatingsHistory(
                student_id=student_task.student_id,
                points_change=score_delta,
                reason=history_reason
            ))

    db.commit()
    db.refresh(student_task)

    return {
        "message": "Student task updated successfully",
        "data": {
            "student_task_id": student_task.id,
            "status": student_task.status,
            "score": student_task.score,
            "comment": student_task.comment,
            "max_score": student_task.task.max_score if student_task.task else None
        }
    }


# =========================
# Получить список студентов
@router.get("/students")
def get_students(
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    students = UserRepository.get_students(db)
    result = []

    for student in students:
        profile = student.student_profile
        image_url = None

        if profile and profile.image_url:
            image_url = file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"])

        result.append({
            "id": student.id,
            "email": student.email,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "middle_name": student.middle_name,
            "full_name": f"{student.first_name} {student.last_name or ''}".strip(),
            "image_url": image_url,
            "password": student.plain_password or ""
        })

    return {"data": result}


# =========================
# Получить категории
@router.get("/categories")
def get_categories(
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    categories = db.query(Category).all()
    return {
        "data": [
            {"id": category.id, "name": category.name, "description": category.description}
            for category in categories
        ]
    }


# =========================
# Получить достижения
@router.get("/achievements")
def get_achievements(
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    achievements = db.query(Achievement).all()
    result = []

    for achievement in achievements:
        file_url = None
        if achievement.certificate_url:
            file_url = file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])

        video_url = None
        if achievement.video_url:
            video_url = file_service.get_file_url(achievement.video_url, BUCKET_NAMES["videos"])

        result.append({
            "id": achievement.id,
            "title": achievement.title,
            "description": achievement.description,
            "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
            "place": achievement.place,
            "is_collective": achievement.is_collective,
            "file_url": file_url,
            "video_url": video_url
        })

    return {"data": result}


# =========================
# Получение достижений ученика
# =========================
@router.get("/student-achievements/{student_id}")
def get_student_achievements(
    student_id: int,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    # Проверить, что ученик существует
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Получить индивидуальные достижения ученика через UserAchievement
    user_achievements = (
        db.query(UserAchievement)
        .options(joinedload(UserAchievement.achievement))
        .filter(UserAchievement.user_id == student_id)
        .all()
    )

    # Получить все коллективные достижения
    collective_achievements = db.query(Achievement).filter(Achievement.is_collective == True).all()

    # Объединить результаты
    all_achievements = []
    seen_ids = set()

    # Добавить индивидуальные
    for ua in user_achievements:
        achievement = ua.achievement
        seen_ids.add(achievement.id)
        file_url = None
        if achievement.certificate_url:
            file_url = file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])

        all_achievements.append({
            "id": achievement.id,
            "title": achievement.title,
            "description": achievement.description,
            "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
            "place": achievement.place,
            "is_collective": False,
            "file_url": file_url,
            "video_url": file_service.get_file_url(achievement.video_url, BUCKET_NAMES["videos"]) if achievement.video_url else None,
            "awarded_at": ua.awarded_at.isoformat() if ua.awarded_at else None
        })

    # Добавить коллективные, если не дублируются
    for achievement in collective_achievements:
        if achievement.id not in seen_ids:
            file_url = None
            if achievement.certificate_url:
                file_url = file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"])

            all_achievements.append({
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
                "place": achievement.place,
                "is_collective": True,
                "file_url": file_url,
                "video_url": file_service.get_file_url(achievement.video_url, BUCKET_NAMES["videos"]) if achievement.video_url else None,
                "awarded_at": None
            })

    return {"data": all_achievements}


# =========================
# Обновление файла достижения
# =========================
@router.post("/achievements/{achievement_id}/upload-media")
async def upload_achievement_media(
    achievement_id: int,
    file: UploadFile = File(...),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    logger.info("upload_achievement_media called for achievement_id=%s content_type=%s uploaded_by=%s", achievement_id, file.content_type, teacher_id)

    if file.content_type in ["video/mp4", "video/mpeg"]:
        file_id = await file_service.upload_video(file)
        achievement.video_url = file_id
        response_url = file_service.get_file_url(file_id, BUCKET_NAMES["videos"])
        result = {
            "message": "achievement video updated",
            "achievement_id": achievement.id,
            "video_url": response_url
        }
        logger.info("Saved video for achievement %s as %s", achievement_id, file_id)
    else:
        file_id = await file_service.upload_achievement_media(file)
        achievement.certificate_url = file_id
        response_url = file_service.get_file_url(file_id, BUCKET_NAMES["certificates"])
        result = {
            "message": "achievement media updated",
            "achievement_id": achievement.id,
            "file_url": response_url
        }
        logger.info("Saved media for achievement %s as %s", achievement_id, file_id)

    db.commit()
    logger.debug("DB commit complete for achievement %s", achievement_id)
    return result


# =========================
# Загрузка видео для достижения
# =========================
@router.post("/achievements/{achievement_id}/upload-video")
async def upload_achievement_video(
    achievement_id: int,
    file: UploadFile = File(...),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    file_id = await file_service.upload_video(file)
    achievement.video_url = file_id
    db.commit()

    return {
        "message": "achievement video uploaded",
        "achievement_id": achievement.id,
        "video_url": file_service.get_file_url(file_id, BUCKET_NAMES["videos"])
    }


# =========================
# Создание нового достижения
@router.post("/achievements/create")
async def create_achievement(
    title: str = Form(...),
    description: str = Form(None),
    event_date: str = Form(None),
    place: str = Form(None),
    assignment_type: str = Form(...),  # "collective" or "individual"
    student_id: int = Form(None),
    file: UploadFile = File(None),
    teacher_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    parsed_date = None
    if event_date:
        try:
            parsed_date = datetime.fromisoformat(event_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    if description is None:
        description = ""

    if place:
        description = f"{description}\nРезультат: {place}".strip()

    if assignment_type not in ["collective", "individual"]:
        raise HTTPException(status_code=400, detail="Invalid assignment_type")

    if assignment_type == "individual" and student_id is None:
        raise HTTPException(status_code=400, detail="student_id required for individual assignment")

    if assignment_type == "collective" and student_id is not None:
        raise HTTPException(status_code=400, detail="student_id should not be provided for collective assignment")

    file_id = None
    file_url = None
    if file:
        logger.info("Received file for new achievement: filename=%s content_type=%s", getattr(file, 'filename', None), getattr(file, 'content_type', None))
        # If it's a video, store in videos bucket and set video_url
        if getattr(file, 'content_type', '') in ["video/mp4", "video/mpeg"]:
            file_id = await file_service.upload_video(file)
            file_url = file_service.get_file_url(file_id, BUCKET_NAMES["videos"])
            achievement = Achievement(
                title=title.strip(),
                description=description,
                event_date=parsed_date,
                place=place,
                is_collective=(assignment_type == "collective"),
                video_url=file_id
            )
        else:
            file_id = await file_service.upload_achievement_media(file)
            file_url = file_service.get_file_url(file_id, BUCKET_NAMES["certificates"])
            achievement = Achievement(
                title=title.strip(),
                description=description,
                event_date=parsed_date,
                place=place,
                is_collective=(assignment_type == "collective"),
                certificate_url=file_id
            )
    else:
        achievement = Achievement(
            title=title.strip(),
            description=description,
            event_date=parsed_date,
            place=place,
            is_collective=(assignment_type == "collective"),
        )

    db.add(achievement)
    db.commit()
    db.refresh(achievement)

    if assignment_type == "individual":
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        user_achievement = UserAchievement(
            user_id=student_id,
            achievement_id=achievement.id
        )
        db.add(user_achievement)
        db.commit()

    result = {
        "message": "achievement created",
        "achievement_id": achievement.id,
        "student_id": student_id,
    }
    if file_id:
        result["file_id"] = file_id
    if file_url:
        result["file_url"] = file_url

    logger.info("Created achievement %s (student=%s) file_id=%s url=%s", achievement.id, student_id, file_id, file_url)
    return result



# =========================
# Назначение достижения пользователю
# =========================
@router.post("/achievements/assign")
def assign_achievement(
    data: AssignAchievement,
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):

    achievement = db.query(Achievement).filter(
        Achievement.id == data.achievement_id
    ).first()

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    exists = db.query(UserAchievement).filter(
        UserAchievement.user_id == data.user_id,
        UserAchievement.achievement_id == data.achievement_id
    ).first()

    if exists:
        raise HTTPException(status_code=400, detail="Already assigned")

    db.add(UserAchievement(**data.dict()))
    db.commit()

    return {
        "message": "assigned",
        "assigned_by": user_id
    }

# ========================
# Получение заданий студентов (для учителя)
# =========================

@router.get("/students-tasks")
def get_students_tasks(
    user_id: int = Depends(get_current_teacher_or_admin),
    db: Session = Depends(get_db)
):
    # Получаем всех студентов (у которых есть StudentProfile)
    students = (
        db.query(User)
        .filter(User.student_profile.has())  # Только пользователи со студ. профилем
        .options(
            joinedload(User.student_profile),
            joinedload(User.student_tasks)
            .joinedload(StudentTask.task)
            .joinedload(Task.category),
            joinedload(User.student_tasks)
            .joinedload(StudentTask.media)
        )
        .all()
    )

    students_map = {}

    # Обрабатываем каждого студента
    for student in students:
        student_id = student.id
        last_history = db.query(RatingsHistory).filter(
            RatingsHistory.student_id == student_id
        ).order_by(RatingsHistory.created_at.desc()).first()

        movement = "same"
        if last_history:
            if last_history.points_change > 0:
                movement = "up"
            elif last_history.points_change < 0:
                movement = "down"

        categories = {}
        for student_task in student.student_tasks:
            if not student_task.task:
                continue

            category_name = student_task.task.category.name if student_task.task.category else "Без категории"
            if category_name not in categories:
                categories[category_name] = {
                    "category_name": category_name,
                    "tasks": []
                }

            categories[category_name]["tasks"].append({
                "student_task_id": student_task.id,
                "task_id": student_task.task.id,
                "title": student_task.task.title,
                "description": student_task.task.description,
                "category_name": category_name,
                "status": student_task.status or "not_started",
                "score": student_task.score,
                "max_score": student_task.task.max_score,
                "has_video": len(student_task.media) > 0,
                "videos": [
                    {
                        "media_id": media.id,
                        "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"])
                    }
                    for media in student_task.media
                ]
            })

        students_map[student_id] = {
            "student_id": student_id,
            "student_name": f"{student.first_name} {student.last_name}",
            "email": student.email,
            "password": student.plain_password or "",
            "rating_points": student.student_profile.rating_points if student.student_profile else 0,
            "last_rank": student.student_profile.last_rank if student.student_profile else None,
            "movement": movement,
            "image_url": file_service.get_file_url(student.student_profile.image_url, BUCKET_NAMES["student_photos"]) if student.student_profile and student.student_profile.image_url else None,
            "tasks_count": len(student.student_tasks),
            "categories": list(categories.values())
        }

        print(f"  ✓ Студент {student_id}: {student.first_name} {student.last_name} - задач: {len(student.student_tasks)}")

        # Обрабатываем его задачи

    # Сортируем студентов по текущему рейтингу и рассчитываем движение
    ordered_student_ids = sorted(
        students_map.keys(),
        key=lambda sid: (
            -(students_map[sid]["rating_points"] or 0),
            students_map[sid]["student_name"]
        )
    )

    result = []

    previous_rating = None
    previous_rank = 0

    for index, student_id in enumerate(ordered_student_ids, start=1):
        student_data = students_map[student_id]


        
        current_rank = previous_rank if student_data["rating_points"] == previous_rating else index

        if student_data["rating_points"] != previous_rating:
            previous_rating = student_data["rating_points"]
            previous_rank = current_rank

        last_rank = student_data.get("last_rank")

        if last_rank is None:
            movement = "same"
        elif current_rank < last_rank:
            movement = "up"
        elif current_rank > last_rank:
            movement = "down"
        else:
            movement = "same"

        student_data["rank"] = current_rank
        student_data["movement"] = movement
        student_data["rank_delta"] = abs(current_rank - last_rank) if last_rank is not None else 0

        result.append(student_data)

    print(f"📌 DEBUG: Возвращаем {len(result)} студентов")
    return {
        "data": result
    }