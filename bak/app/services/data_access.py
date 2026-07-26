from datetime import datetime
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from db.minio_client import BUCKET_NAMES
from models import (
    Achievement,
    Category,
    RatingsHistory,
    StudentProfile,
    StudentTask,
    Task,
    TaskMedia,
    User,
    UserAchievement,
)
from repositories.user_repository import UserRepository
from services.auth_service import auth_service
from services.file_service import file_service


class TeacherService:
    def create_category(self, db, *, name: str, description: str | None = None):
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")

        category = Category(name=name, description=description)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def get_categories(self, db):
        return db.query(Category).all()

    def create_task(self, db, *, data):
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="There is no such category")

        task = Task(
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            difficulty=data.difficulty,
            max_score=data.max_score,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        students = db.query(User).join(User.roles).join(__import__('models').Role).filter(__import__('models').Role.name == "student").all()
        if not students:
            raise HTTPException(status_code=400, detail="No students found")

        student_tasks = [
            StudentTask(student_id=student.id, task_id=task.id, status="not_started")
            for student in students
        ]
        db.bulk_save_objects(student_tasks)
        db.commit()
        return task, len(student_tasks)

    def get_tasks(self, db):
        return db.query(Task).options(joinedload(Task.category)).all()

    def update_task(self, db, *, task_id: int, task_data):
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
        return task


class StudentService:
    def add_student_from_teacher(self, db, *, email: str, first_name: str, last_name: str | None, middle_name: str, image_url: str):
        student_data = SimpleNamespace(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )
        user, generated_password = auth_service.add_student_by_teacher(db, student_data, image_url)
        self.assign_tasks_to_new_student(db, user.id)
        return user, generated_password

    def assign_tasks_to_new_student(self, db, user_id: int):
        tasks = db.query(Task).all()
        if tasks:
            student_tasks = [
                StudentTask(student_id=user_id, task_id=task.id, status="not_started")
                for task in tasks
            ]
            db.bulk_save_objects(student_tasks)
            db.commit()
        return []

    def upload_student_task_video(self, db, *, student_task_id: int, uploaded_by: int, video_url: str):
        student_task = db.query(StudentTask).filter(StudentTask.id == student_task_id).first()
        if not student_task:
            raise ValueError("Student task not found")

        student_task.status = "completed"
        student_task.submitted_at = func.now()
        student_task.reviewed_at = func.now()

        media = TaskMedia(
            student_task_id=student_task.id,
            uploaded_by=uploaded_by,
            video_url=video_url,
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        return student_task, media

    def update_student_task(self, db, *, student_task_id: int, student_task_data):
        student_task = db.query(StudentTask).filter(StudentTask.id == student_task_id).first()
        if not student_task:
            raise ValueError("Student task not found")

        original_score = student_task.score or 0

        if student_task_data.score is not None:
            if student_task_data.score < 0:
                raise ValueError("Score cannot be negative")
            if student_task.task and student_task.task.max_score is not None and student_task_data.score > student_task.task.max_score:
                raise ValueError(f"Score cannot exceed max_score of {student_task.task.max_score}")
            student_task.score = student_task_data.score

        if student_task_data.status is not None:
            student_task.status = student_task_data.status
            if student_task.status == "completed":
                student_task.submitted_at = func.now()
                student_task.reviewed_at = func.now()

        if student_task_data.comment is not None:
            student_task.comment = student_task_data.comment

        new_score = student_task.score or 0
        score_delta = new_score - original_score
        if score_delta != 0:
            student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_task.student_id).first()
            if student_profile:
                student_profile.rating_points = (student_profile.rating_points or 0) + score_delta
                db.add(RatingsHistory(
                    student_id=student_task.student_id,
                    points_change=score_delta,
                    reason=f"Обновлена оценка задания: {student_task.task.title or student_task.task_id}",
                ))

        db.commit()
        db.refresh(student_task)
        return student_task

    def get_students_payload(self, db):
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

        return result

    def get_students_for_teacher(self, db):
        return (
            db.query(User)
            .filter(User.student_profile.has())
            .options(
                joinedload(User.student_profile),
                joinedload(User.student_tasks).joinedload(StudentTask.task).joinedload(Task.category),
                joinedload(User.student_tasks).joinedload(StudentTask.media),
            )
            .all()
        )

    def get_last_rating_history(self, db, student_id: int):
        return (
            db.query(RatingsHistory)
            .filter(RatingsHistory.student_id == student_id)
            .order_by(RatingsHistory.created_at.desc())
            .first()
        )

    def get_student_by_id(self, db, student_id: int):
        return db.query(User).filter(User.id == student_id).first()

    def get_students_tasks_payload(self, db):
        students = self.get_students_for_teacher(db)
        students_map = {}

        for student in students:
            student_id = student.id
            last_history = self.get_last_rating_history(db, student_id)

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

        ordered_student_ids = sorted(
            students_map.keys(),
            key=lambda sid: (-(students_map[sid]["rating_points"] or 0), students_map[sid]["student_name"])
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

        return result


class AchievementService:
    def get_achievements(self, db):
        return db.query(Achievement).all()

    def get_achievements_payload(self, db):
        achievements = self.get_achievements(db)
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

        return result

    def get_student_achievements(self, db, student_id: int):
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        user_achievements = (
            db.query(UserAchievement)
            .options(joinedload(UserAchievement.achievement))
            .filter(UserAchievement.user_id == student_id)
            .all()
        )
        collective_achievements = db.query(Achievement).filter(Achievement.is_collective == True).all()
        return student, user_achievements, collective_achievements

    def get_student_achievements_payload(self, db, student_id: int):
        _, user_achievements, collective_achievements = self.get_student_achievements(db, student_id)

        all_achievements = []
        seen_ids = set()

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

        return all_achievements

    def get_achievement_by_id(self, db, achievement_id: int):
        return db.query(Achievement).filter(Achievement.id == achievement_id).first()

    async def upload_achievement_media(self, db, *, achievement_id: int, file, logger=None):
        achievement = self.get_achievement_by_id(db, achievement_id)
        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")
        if logger:
            logger.info("upload_achievement_media called for achievement_id=%s content_type=%s", achievement_id, file.content_type)

        if file.content_type in ["video/mp4", "video/mpeg"]:
            file_id = await file_service.upload_video(file)
            achievement.video_url = file_id
            response_url = file_service.get_file_url(file_id, BUCKET_NAMES["videos"])
            result = {
                "message": "achievement video updated",
                "achievement_id": achievement.id,
                "video_url": response_url
            }
            if logger:
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
            if logger:
                logger.info("Saved media for achievement %s as %s", achievement_id, file_id)

        db.commit()
        if logger:
            logger.debug("DB commit complete for achievement %s", achievement_id)
        return result

    async def upload_achievement_video(self, db, *, achievement_id: int, file):
        achievement = self.get_achievement_by_id(db, achievement_id)
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

    async def create_achievement_from_form(self, db, *, title: str, description: str | None, event_date: str | None, place: str | None, assignment_type: str, student_id: int | None, file, logger=None):
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
            if logger:
                logger.info("Received file for new achievement: filename=%s content_type=%s", getattr(file, 'filename', None), getattr(file, 'content_type', None))
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

        self.create_achievement(db, achievement)

        if assignment_type == "individual":
            student = self.get_student_by_id(db, student_id)
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")

            self.assign_user_achievement(db, user_id=student_id, achievement_id=achievement.id)

        result = {
            "message": "achievement created",
            "achievement_id": achievement.id,
            "student_id": student_id,
        }
        if file_id:
            result["file_id"] = file_id
        if file_url:
            result["file_url"] = file_url

        if logger:
            logger.info("Created achievement %s (student=%s) file_id=%s url=%s", achievement.id, student_id, file_id, file_url)
        return result

    def create_achievement(self, db, achievement):
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        return achievement

    def assign_achievement(self, db, *, achievement_id: int, user_id: int):
        achievement = self.get_achievement_by_id(db, achievement_id)
        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")

        existing = (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Already assigned")

        assignment = UserAchievement(user_id=user_id, achievement_id=achievement_id)
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def assign_user_achievement(self, db, *, user_id: int, achievement_id: int):
        return self.assign_achievement(db, achievement_id=achievement_id, user_id=user_id)

    def get_student_by_id(self, db, student_id: int):
        return db.query(User).filter(User.id == student_id).first()


teacher_service = TeacherService()
student_service = StudentService()
achievement_service = AchievementService()
