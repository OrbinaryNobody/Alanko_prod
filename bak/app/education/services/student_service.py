from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.minio_client import BUCKET_NAMES
from education.exceptions.domain_exceptions import StudentNotFound, StudentTaskNotFound
from education.repositories.student_repository import student_repository
from models.domains.student import StudentProfile
from infrastructure.storage.file_service import file_service
from education.dtos.student_dto import StudentPayload, StudentSummaryPayload, StudentTaskPayload
from education.exceptions.domain_exceptions import InvalidStudentTaskScore
from education.policies.student_task_policy import StudentTaskPolicy
from models.domains.education import GroupEnrollment, GroupStudentTask, ProgramTask
from core.exceptions import PermissionDenied
from core.events import event_bus
from education.events import StudentScoreUpdatedEvent
from shared.unit_of_work import UnitOfWork
from attendance.facade import attendance_facade


class StudentService:
    def _get_group_task(self, db: Session, student_task):
        return (
            db.query(GroupStudentTask)
            .join(GroupEnrollment, GroupEnrollment.id == GroupStudentTask.enrollment_id)
            .join(ProgramTask, ProgramTask.id == GroupStudentTask.program_task_id)
            .filter(
                GroupEnrollment.student_id == student_task.student_id,
                ProgramTask.task_id == student_task.task_id,
            )
            .first()
        )

    def _require_task_access(self, db: Session, *, ctx, student_task, allow_student: bool):
        if ctx.is_admin:
            return
        if allow_student and ctx.user_id == student_task.student_id:
            return
        group_task = self._get_group_task(db, student_task)
        if not group_task:
            raise PermissionDenied("Access denied to this student task")
        try:
            StudentTaskPolicy.require_grade(ctx, group_task, db)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to this student task") from exc

    def upload_student_task_video(self, db: Session, *, ctx, student_task_id: int, uploaded_by: int, video_url: str):
        student_task = student_repository.get_student_task_by_id(db, student_task_id=student_task_id)
        if not student_task:
            raise StudentTaskNotFound("Student task not found")
        self._require_task_access(db, ctx=ctx, student_task=student_task, allow_student=True)

        student_task.status = "completed"
        student_task.submitted_at = func.now()
        student_task.reviewed_at = func.now()

        media = student_repository.create_media(db, student_task_id=student_task.id, uploaded_by=uploaded_by, video_url=video_url)
        return student_task, media

    def ensure_student_task_video_access(self, db: Session, *, ctx, student_task_id: int):
        student_task = student_repository.get_student_task_by_id(db, student_task_id=student_task_id)
        if not student_task:
            raise StudentTaskNotFound("Student task not found")
        self._require_task_access(db, ctx=ctx, student_task=student_task, allow_student=True)
        return student_task

    def update_student_task(self, db: Session, *, ctx, student_task_id: int, student_task_data):
        with UnitOfWork(db, event_bus=event_bus) as uow:
            student_task = student_repository.get_student_task_by_id(db, student_task_id=student_task_id)
            if not student_task:
                raise StudentTaskNotFound("Student task not found")
            self._require_task_access(db, ctx=ctx, student_task=student_task, allow_student=False)

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

    def get_students_payload(
        self,
        db: Session,
        *,
        attendance_date: date | None = None,
        search: str | None = None,
        group_id: int | None = None,
        payment_status: str | None = None,
        remaining_visits_lte: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        attendance_date = attendance_date or date.today()
        students = attendance_facade.list_students(db, search=search, group_id=group_id, limit=limit, offset=offset)
        result = []
        active_enrollments = db.query(GroupEnrollment).filter(GroupEnrollment.status == "active").all()
        group_points = {}
        for enrollment in active_enrollments:
            points = sum((task.grade or 0) for task in enrollment.tasks)
            group_points.setdefault(enrollment.group_id, {})[enrollment.student_id] = points
        group_ranks = {
            group_id: {
                student_id: index + 1
                for index, (student_id, _) in enumerate(sorted(points.items(), key=lambda item: (-item[1], item[0])))
            }
            for group_id, points in group_points.items()
        }

        for student in students:
            profile = student.student_profile
            image_url = None
            if profile and profile.image_url:
                image_url = file_service.get_file_url(profile.image_url, BUCKET_NAMES["student_photos"])

            context = attendance_facade.get_student_context(db, student_id=student.id, attendance_date=attendance_date)
            subscription = context["subscription"]
            if payment_status and (not subscription or subscription.payment_status != payment_status):
                continue
            if remaining_visits_lte is not None and (not subscription or subscription.remaining_visits > remaining_visits_lte):
                continue

            student_groups = [
                {
                    "id": group.id,
                    "title": group.title,
                    "points": group_points.get(group.id, {}).get(student.id, 0),
                    "rank": group_ranks.get(group.id, {}).get(student.id),
                }
                for group in context["groups"]
            ]
            program_points = sum(group["points"] for group in student_groups)
            student_payload = StudentPayload(
                    id=student.id,
                    email=student.email,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    middle_name=student.middle_name,
                    full_name=f"{student.first_name} {student.last_name or ''}".strip(),
                    image_url=image_url,
                    password=None,
                    birth_year=profile.birth_year if profile else None,
                    rating_points=program_points,
                ).to_dict()
            student_payload.update({
                "groups": student_groups,
                "parent": self._parent_payload(context["parent"]),
                "current_subscription": self._subscription_payload(subscription),
                "payment_status": subscription.payment_status if subscription else "NO_SUBSCRIPTION",
                "attendance": self._attendance_payload(context["attendance"], attendance_date),
            })
            result.append(student_payload)

        return result

    @staticmethod
    def _parent_payload(parent):
        if not parent:
            return None
        return {
            "id": parent.id,
            "first_name": parent.first_name,
            "last_name": parent.last_name,
            "middle_name": parent.middle_name,
            "full_name": " ".join(part for part in [parent.first_name, parent.last_name, parent.middle_name] if part),
            "phone": parent.phone,
            "email": parent.email,
        }

    @staticmethod
    def _subscription_payload(subscription):
        if not subscription:
            return None
        return {
            "id": subscription.id,
            "plan_name": subscription.plan_name,
            "total_visits": subscription.total_visits,
            "remaining_visits": subscription.remaining_visits,
            "valid_from": subscription.valid_from.isoformat(),
            "valid_until": subscription.valid_until.isoformat(),
            "status": subscription.status,
            "payment_status": subscription.payment_status,
            "amount": subscription.amount,
            "currency": subscription.currency,
            "paid_at": subscription.paid_at.isoformat() if subscription.paid_at else None,
        }

    @staticmethod
    def _attendance_payload(attendance, attendance_date):
        return {
            "date": attendance_date.isoformat(),
            "checked": bool(attendance and attendance.status == "PRESENT"),
            "status": attendance.status if attendance else "NOT_MARKED",
            "check_in_time": attendance.checked_in_at.isoformat() if attendance and attendance.checked_in_at else None,
        }

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
                            for media in student_task.media[:20]
                        ],
                    ).to_dict()
                )

            students_map[student_id] = {
                "student_id": student_id,
                "student_name": f"{student.first_name} {student.last_name}",
                "email": student.email,
                "password": None,
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
