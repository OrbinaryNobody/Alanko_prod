from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.http import translate_domain_error
from core.permissions import (
    require_manage_enrollments,
    require_manage_groups,
    require_view_groups,
    require_view_students,
)
from db.database import get_db
from education.dtos.program_dto import GroupPayload, GroupMemberPayload, StudentEnrollmentPayload
from education.exceptions.domain_exceptions import EducationError
from education.facade import education_facade
from education.schemas.education import EnrollmentCreate, GroupCreate, GroupMemberCreate, GroupScheduleCreate, GroupStudentCreate, GroupTeacherCreate

router = APIRouter(prefix="/groups", tags=["education-groups"])


@router.post("", status_code=201)
def create_group(
    data: GroupCreate,
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db),
):
    try:
        group = education_facade.create_group(
            db,
            ctx=ctx,
            title=data.title,
            description=data.description,
            program_id=data.program_id,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Group created", "data": GroupPayload(id=group.id, title=group.title).to_dict()}


@router.get("")
def list_groups(
    ctx: AccessContext = Depends(require_view_groups),
    db: Session = Depends(get_db),
):
    try:
        groups = education_facade.get_groups_for_user(db, ctx=ctx)
    except EducationError as exc:
        translate_domain_error(exc)

    return {"data": [GroupPayload(id=g.id, title=g.title, program_id=g.program_id, status=g.status).to_dict() for g in groups]}


@router.post("/{group_id}/members", status_code=201)
def add_member(
    group_id: int,
    data: GroupMemberCreate,
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db),
):
    try:
        member = education_facade.add_member(
            db,
            ctx=ctx,
            group_id=group_id,
            user_id=data.user_id,
            role=data.role,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Member added", "data": GroupMemberPayload(group_id=group_id, user_id=member.user_id, role=member.role).to_dict()}


@router.post("/{group_id}/teachers", status_code=201)
def add_teacher_to_group(
    group_id: int,
    data: GroupTeacherCreate,
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db),
):
    try:
        member = education_facade.add_teacher_member(
            db,
            ctx=ctx,
            group_id=group_id,
            user_id=data.user_id,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Teacher added to group", "data": GroupMemberPayload(group_id=group_id, user_id=member.user_id, role=member.role).to_dict()}


@router.post("/{group_id}/students", status_code=201)
def add_student_to_group(
    group_id: int,
    data: GroupStudentCreate,
    ctx: AccessContext = Depends(require_manage_enrollments),
    db: Session = Depends(get_db),
):
    try:
        enrollment = education_facade.enroll_student(
            db,
            ctx=ctx,
            group_id=group_id,
            student_id=data.student_id,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Student enrolled", "data": StudentEnrollmentPayload(id=enrollment.id, student_id=enrollment.student_id).to_dict()}


@router.get("/{group_id}/students")
def get_group_students(
    group_id: int,
    ctx: AccessContext = Depends(require_view_students),
    db: Session = Depends(get_db),
):
    students = education_facade.get_group_students(db, ctx=ctx, group_id=group_id)
    return {"data": students}


@router.get("/{group_id}/schedule")
def list_group_schedule(
    group_id: int,
    ctx: AccessContext = Depends(require_view_groups),
    db: Session = Depends(get_db),
):
    schedules = education_facade.list_group_schedules(db, ctx=ctx, group_id=group_id)
    return {"data": [_schedule_payload(schedule) for schedule in schedules]}


@router.post("/{group_id}/schedule", status_code=201)
def create_group_schedule(
    group_id: int,
    data: GroupScheduleCreate,
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db),
):
    schedule = education_facade.create_group_schedule(
        db,
        ctx=ctx,
        group_id=group_id,
        teacher_id=data.teacher_id,
        weekday=data.weekday,
        start_time=data.start_time,
        end_time=data.end_time,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
    )
    return {"data": _schedule_payload(schedule)}


@router.delete("/schedule/{schedule_id}", status_code=204)
def delete_group_schedule(
    schedule_id: int,
    ctx: AccessContext = Depends(require_manage_groups),
    db: Session = Depends(get_db),
):
    education_facade.delete_group_schedule(db, ctx=ctx, schedule_id=schedule_id)


def _schedule_payload(schedule):
    return {
        "id": schedule.id,
        "group_id": schedule.group_id,
        "teacher_id": schedule.teacher_id,
        "weekday": schedule.weekday,
        "start_time": schedule.start_time.isoformat(),
        "end_time": schedule.end_time.isoformat(),
        "valid_from": schedule.valid_from.isoformat(),
        "valid_until": schedule.valid_until.isoformat() if schedule.valid_until else None,
        "status": schedule.status,
    }


@router.post("/{group_id}/enrollments", status_code=201)
def enroll_student(
    group_id: int,
    data: EnrollmentCreate,
    ctx: AccessContext = Depends(require_manage_enrollments),
    db: Session = Depends(get_db),
):
    try:
        enrollment = education_facade.enroll_student(
            db,
            ctx=ctx,
            group_id=group_id,
            student_id=data.student_id,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {"message": "Student enrolled", "data": StudentEnrollmentPayload(id=enrollment.id, student_id=enrollment.student_id).to_dict()}
