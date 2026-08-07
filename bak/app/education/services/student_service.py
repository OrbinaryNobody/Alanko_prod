from sqlalchemy import func
from sqlalchemy.orm import Session

from db.minio_client import BUCKET_NAMES
from education.exceptions.domain_exceptions import StudentNotFound, StudentTaskNotFound
from education.repositories.student_repository import student_repository
from models.domains.student import StudentProfile
from services.file_service import file_service
from education.dtos.student_dto import StudentPayload, StudentSummaryPayload, StudentTaskPayload
from education.exceptions.domain_exceptions import InvalidStudentTaskScore
from core.events import event_bus
from education.events import StudentScoreUpdatedEvent
from shared.unit_of_work import UnitOfWork


class StudentService:
    def upload_student_task_video(self, db: Session, *, student_task_id: int, uploaded_by: int, video_url: str):
        student_task = student_repository.get_student_task_by_id(db, student_task_id=student_task_id)
        if not student_task:
            raise StudentTaskNotFound("Student task not found")

        student_task.status = "completed"
        student_task.submitted_at = func.now()
        student_task.reviewed_at = func.now()

        media = student_repository.create_media(db, student_task_id=student_task.id, uploaded_by=uploaded_by, video_url=video_url)
        return student_task, media

    def update_student_task(self, db: Session, *, student_task_id: int, student_task_data):
        with UnitOfWork(db, event_bus=event_bus) as uow:
            student_task = student_repository.get_student_task_by_id(db, student_task_id=student_task_id)
            if not student_task:
                raise StudentTaskNotFound("Student task not found")

            original_score = student_task.score or 0

            if student_task_data.score is not None:
                if student_task_data.score < 0:
                    raise InvalidStudentTaskScore("Score cannot be negative")
                if student_task.task and student_task.task.max_score is not None and student_task_data.score > student_task.task.max_score:
                    raise InvalidStudentTaskScore(f"Score cannot exceed max_score of {student_task.task.max_score}")
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
                    student_repository.create_rating_history(
                        db,
                        student_id=student_task.student_id,
                        points_change=score_delta,
                        reason=f"Обновлена оценка задания: {student_task.task.title or student_task.task_id}",
                    )

            uow.events.append(StudentScoreUpdatedEvent(student_task_id=student_task.id, student_id=student_task.student_id, score=student_task.score))
            db.refresh(student_task)
            return student_task

    def get_student_by_id(self, db: Session, student_id: int):
        student = student_repository.get_student_by_id(db, student_id=student_id)
        if not student:
            raise StudentNotFound("Student not found")
        return student

    def get_students_payload(self, db: Session):
        students = student_repository.get_students(db)
        result = []

        for student in students:
            profile = student.student_profile
            image_url = None
            if profile and profile.image_url:
                image_url = file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"])

            result.append(
                StudentPayload(
                    id=student.id,
                    email=student.email,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    middle_name=student.middle_name,
                    full_name=f"{student.first_name} {student.last_name or ''}".strip(),
                    image_url=image_url,
                    password=student.plain_password or "",
                ).to_dict()
            )

        return result

    def get_students_tasks_payload(self, db: Session):
        students = student_repository.get_students_for_teacher(db)
        students_map = {}

        for student in students:
            student_id = student.id
            last_history = student_repository.get_last_rating_history(db, student_id=student_id)

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
                    categories[category_name] = {"category_name": category_name, "tasks": []}

                categories[category_name]["tasks"].append(
                    StudentTaskPayload(
                        student_task_id=student_task.id,
                        task_id=student_task.task.id,
                        title=student_task.task.title,
                        description=student_task.task.description,
                        category_name=category_name,
                        status=student_task.status or "not_started",
                        score=student_task.score,
                        max_score=student_task.task.max_score,
                        has_video=len(student_task.media) > 0,
                        videos=[
                            {
                                "media_id": media.id,
                                "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"]),
                            }
                            for media in student_task.media
                        ],
                    ).to_dict()
                )

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
                "categories": list(categories.values()),
            }

        ordered_student_ids = sorted(
            students_map.keys(),
            key=lambda sid: (-(students_map[sid]["rating_points"] or 0), students_map[sid]["student_name"]),
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
            result.append(
                StudentSummaryPayload(
                    student_id=student_data["student_id"],
                    student_name=student_data["student_name"],
                    email=student_data["email"],
                    password=student_data["password"],
                    rating_points=student_data["rating_points"],
                    last_rank=student_data["last_rank"],
                    movement=student_data["movement"],
                    image_url=student_data["image_url"],
                    tasks_count=student_data["tasks_count"],
                    categories=student_data["categories"],
                    rank=student_data["rank"],
                    rank_delta=student_data["rank_delta"],
                ).to_dict()
            )

        return result


student_service = StudentService()
