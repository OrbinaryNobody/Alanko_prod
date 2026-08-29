from datetime import date, time

from sqlalchemy.orm import Session

from core.access import AccessContext
from education.exceptions.domain_exceptions import PermissionDenied
from education.policies.group_policy import GroupPolicy
from education.repositories.group_repository import group_repository
from education.services.group_management_service import group_management_service
from models.domains.auth import Role, User
from models.domains.education import GroupSchedule, GroupStudentTask
from models.domains.student import RatingsHistory, StudentProfile, TaskMedia
from db.minio_client import BUCKET_NAMES
from infrastructure.storage.file_service import file_service
from shared.unit_of_work import UnitOfWork


class GroupService:
    def ensure_group_access(self, db: Session, *, ctx: AccessContext, group_id: int):
        group = group_repository.get_by_id(db, group_id)
        if not group:
            raise PermissionDenied("Group not found")
        try:
            GroupPolicy.require_view_group(ctx, group)
        except PermissionError as exc:
            raise PermissionDenied("Access denied to this group") from exc
        return group

    def create_group(self, db: Session, *, ctx: AccessContext, title: str, description: str | None, program_id: int | None):
        return group_management_service.create_group(db, ctx=ctx, title=title, description=description, program_id=program_id)

    def update_group(self, db: Session, *, ctx: AccessContext, group_id: int, title: str, description: str | None, leaderboard_enabled: bool):
        with UnitOfWork(db):
            group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
            group.title = title
            group.description = description
            group.leaderboard_enabled = leaderboard_enabled
            db.flush()
            db.refresh(group)
            return group

    def delete_group(self, db: Session, *, ctx: AccessContext, group_id: int):
        with UnitOfWork(db):
            group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
            group_repository.delete(db, group)

    def get_groups_for_user(self, db: Session, *, ctx: AccessContext):
        return group_repository.list_for_user(db, user_id=ctx.user_id, is_admin=ctx.is_admin)

    def add_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int, role: str):
        return group_management_service.add_member(db, ctx=ctx, group_id=group_id, user_id=user_id, role=role)

    def add_teacher_member(self, db: Session, *, ctx: AccessContext, group_id: int, user_id: int):
        return group_management_service.add_teacher_member(db, ctx=ctx, group_id=group_id, user_id=user_id)

    def enroll_student(self, db: Session, *, ctx: AccessContext, group_id: int, student_id: int):
        return group_management_service.enroll_student(db, ctx=ctx, group_id=group_id, student_id=student_id)

    def delete_enrollment(self, db: Session, *, ctx: AccessContext, group_id: int, enrollment_id: int):
        with UnitOfWork(db):
            enrollment = group_repository.get_enrollment_by_id(db, enrollment_id)
            if not enrollment or enrollment.group_id != group_id:
                raise PermissionDenied("Enrollment not found")
            self.ensure_group_access(db, ctx=ctx, group_id=group_id)
            group_repository.delete_enrollment(db, enrollment)

    def get_group_students(self, db: Session, *, ctx: AccessContext, group_id: int):
        from education.dtos.student_dto import GroupStudentPayload

        self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        enrollments = group_repository.list_enrollments(db, group_id=group_id)
        return [
            GroupStudentPayload(
                id=enrollment.id,
                student_id=enrollment.student_id,
                status=enrollment.status,
                current_block_id=enrollment.current_block_id,
                completion_percent=enrollment.completion_percent,
            ).to_dict()
            for enrollment in enrollments
        ]

    def get_group_journal(self, db: Session, *, ctx: AccessContext, group_id: int):
        group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        students = []
        for enrollment in group.enrollments:
            student = db.query(User).filter(User.id == enrollment.student_id).first()
            students.append({
                "enrollment_id": enrollment.id,
                "student_id": enrollment.student_id,
                "name": f"{student.first_name} {student.last_name or ''}".strip() if student else f"Ученик #{enrollment.student_id}",
                "email": student.email if student else None,
                "image_url": None,
                "status": enrollment.status,
                "tasks": [{
                    "student_task_id": task.id,
                    "task_id": task.program_task_id,
                    "title": task.program_task.title,
                    "description": task.program_task.description,
                    "max_score": task.program_task.max_score,
                    "grade": task.grade,
                    "feedback": task.feedback,
                    "status": task.status,
                    "videos": [{"media_id": media.id, "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"])} for media in task.media],
                } for task in enrollment.tasks if task.program_task],
            })
        return {
            "group": {"id": group.id, "title": group.title, "description": group.description, "program_id": group.program_id},
            "program": {
                "id": group.program.id if group.program else None,
                "title": group.program.title if group.program else None,
                "description": group.program.description if group.program else None,
                "blocks": [{
                    "id": block.id,
                    "title": block.title,
                    "description": block.description,
                    "order": block.order,
                    "topics": [{
                        "id": topic.id,
                        "title": topic.title,
                        "description": topic.description,
                        "order": topic.order,
                        "tasks": [{"id": task.id, "title": task.title, "description": task.description, "max_score": task.max_score, "order": task.order} for task in topic.tasks],
                    } for topic in block.topics],
                } for block in group.program.blocks] if group.program else [],
            },
            "students": students,
        }

    def grade_group_task(self, db: Session, *, ctx: AccessContext, group_id: int, student_task_id: int, grade: int, feedback: str | None):
        with UnitOfWork(db):
            task = db.query(GroupStudentTask).join(GroupStudentTask.enrollment).filter(
                GroupStudentTask.id == student_task_id,
                GroupStudentTask.enrollment.has(group_id=group_id),
            ).first()
            if not task:
                raise PermissionDenied("Group task not found")
            self.ensure_group_access(db, ctx=ctx, group_id=group_id)
            if task.program_task and grade > task.program_task.max_score:
                raise PermissionDenied("Grade exceeds maximum score")
            previous_grade = task.grade or 0
            task.grade = grade
            task.feedback = feedback
            task.status = "completed"
            score_delta = grade - previous_grade
            if score_delta:
                student_profile = db.query(StudentProfile).filter(
                    StudentProfile.user_id == task.enrollment.student_id,
                ).first()
                if student_profile:
                    student_profile.rating_points = (student_profile.rating_points or 0) + score_delta
                db.add(RatingsHistory(
                    student_id=task.enrollment.student_id,
                    points_change=score_delta,
                    reason=(
                        f"Задание «{task.program_task.title}» в группе "
                        f"«{task.enrollment.group.title}»"
                    ),
                ))
            db.flush()
            return task

    def upload_group_task_video(self, db: Session, *, ctx: AccessContext, group_id: int, student_task_id: int, video_url: str):
        with UnitOfWork(db):
            group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
            task = (
                db.query(GroupStudentTask)
                .join(GroupStudentTask.enrollment)
                .filter(
                    GroupStudentTask.id == student_task_id,
                    GroupStudentTask.enrollment.has(group_id=group.id),
                )
                .first()
            )
            if not task:
                raise PermissionDenied("Student task not found in this group")
            media = TaskMedia(group_student_task_id=task.id, uploaded_by=ctx.user_id, video_url=video_url)
            db.add(media)
            db.flush()
            db.refresh(media)
            return media

    def delete_group_task_video(self, db: Session, *, ctx: AccessContext, group_id: int, student_task_id: int, media_id: int):
        group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        task = (
            db.query(GroupStudentTask)
            .join(GroupStudentTask.enrollment)
            .filter(
                GroupStudentTask.id == student_task_id,
                GroupStudentTask.enrollment.has(group_id=group.id),
            )
            .first()
        )
        if not task:
            raise PermissionDenied("Student task not found in this group")
        media = next((item for item in task.media if item.id == media_id), None)
        if not media:
            raise PermissionDenied("Video does not belong to this student task")
        file_service.delete_file(media.video_url, BUCKET_NAMES["videos"])
        db.delete(media)
        db.flush()

    def list_schedules(self, db: Session, *, ctx: AccessContext, group_id: int):
        self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        return group_repository.list_schedules(db, group_id=group_id)

    def create_schedule(
        self,
        db: Session,
        *,
        ctx: AccessContext,
        group_id: int,
        teacher_id: int,
        weekday: int,
        start_time: time,
        end_time: time,
        valid_from: date,
        valid_until: date | None,
    ):
        group = self.ensure_group_access(db, ctx=ctx, group_id=group_id)
        teacher = db.query(User).join(User.roles).join(Role).filter(
            User.id == teacher_id,
            Role.name == "teacher",
        ).first()
        if not teacher:
            raise PermissionDenied("Teacher not found")

        schedules = group_repository.list_schedules(db, group_id=group_id)
        for schedule in schedules:
            if schedule.status != "ACTIVE" or schedule.weekday != weekday:
                continue
            periods_overlap = (
                schedule.valid_from <= (valid_until or date.max)
                and (schedule.valid_until is None or schedule.valid_until >= valid_from)
            )
            times_overlap = schedule.start_time < end_time and schedule.end_time > start_time
            if periods_overlap and times_overlap:
                raise PermissionDenied("Schedule overlaps with an existing group lesson")

        return group_repository.create_schedule(db, GroupSchedule(
            group_id=group.id,
            teacher_id=teacher_id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            valid_from=valid_from,
            valid_until=valid_until,
        ))

    def delete_schedule(self, db: Session, *, ctx: AccessContext, schedule_id: int):
        schedule = group_repository.get_schedule(db, schedule_id=schedule_id)
        if not schedule:
            raise PermissionDenied("Schedule not found")
        self.ensure_group_access(db, ctx=ctx, group_id=schedule.group_id)
        group_repository.delete_schedule(db, schedule)

    def list_calendar_schedules(self, db: Session, *, date_from: date, date_to: date):
        return group_repository.list_active_schedules(db, date_from=date_from, date_to=date_to)


group_service = GroupService()
