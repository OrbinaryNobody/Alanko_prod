from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from core.access import AccessContext
from core.http import translate_domain_error
from core.permissions import (
    require_grade_tasks,
    require_upload_media,
    require_view_students,
)
from db.database import get_db
from education.dtos.program_dto import StudentTaskUploadPayload, StudentTaskUpdatePayload
from education.exceptions.domain_exceptions import EducationError
from education.facade import education_facade
from schemas.task import StudentTaskUpdate
from services.file_service import file_service

router = APIRouter(prefix="/students", tags=["education-students"])


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    student_task_id: int = Form(...),
    ctx: AccessContext = Depends(require_upload_media),
    db: Session = Depends(get_db),
):
    try:
        student_task, media = education_facade.upload_student_task_video(
            db,
            student_task_id=student_task_id,
            uploaded_by=ctx.user_id,
            video_url=await file_service.upload_video(file),
        )
        student = education_facade.get_student_by_id(db, student_id=student_task.student_id)
    except EducationError as exc:
        translate_domain_error(exc)

    file_id = media.video_url
    return StudentTaskUploadPayload(
        media_id=media.id,
        student_id=student.id,
        student_task_id=student_task.id,
        video_id=file_id,
        video_url=file_service.get_file_url(file_id, "videos"),
        status=student_task.status,
        has_video=True,
    ).to_dict()


@router.put("/student-tasks/{student_task_id}")
def update_student_task(
    student_task_id: int,
    student_task_data: StudentTaskUpdate,
    ctx: AccessContext = Depends(require_grade_tasks),
    db: Session = Depends(get_db),
):
    try:
        student_task = education_facade.update_student_task(
            db,
            student_task_id=student_task_id,
            student_task_data=student_task_data,
        )
    except EducationError as exc:
        translate_domain_error(exc)

    return {
        "message": "Student task updated successfully",
        "data": StudentTaskUpdatePayload(
            student_task_id=student_task.id,
            status=student_task.status,
            score=student_task.score,
            comment=student_task.comment,
            max_score=student_task.task.max_score if student_task.task else None,
        ).to_dict(),
    }


@router.get("")
def get_students(
    ctx: AccessContext = Depends(require_view_students),
    db: Session = Depends(get_db),
):
    return {"data": education_facade.get_students_payload(db, ctx=ctx)}


@router.get("/tasks")
def get_students_tasks(
    ctx: AccessContext = Depends(require_view_students),
    db: Session = Depends(get_db),
):
    return {"data": education_facade.get_students_tasks_payload(db, ctx=ctx)}
