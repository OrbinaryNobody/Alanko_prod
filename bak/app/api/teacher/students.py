from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.access import AccessContext
from db.database import get_db
from schemas.task import StudentTaskUpdate
from services.file_service import file_service
from services.data_access import student_service

from core.permissions import (
    require_grade_tasks,
    require_manage_enrollments,
    require_upload_media,
    require_view_students,
)

router = APIRouter(prefix="/teacher", tags=["teacher"])


# @router.post("/add-student")
# async def add_student(
#     first_name: str = Form(...),
#     last_name: str = Form(None),
#     middle_name: str = Form(...),
#     email: str = Form(...),
#     image: UploadFile = File(...),
#     current_user: dict = Depends(require_manage_enrollments),
#     db: Session = Depends(get_db)
# ):
#     try:
#         image_url = await file_service.upload_image(image)
#         user, generated_password = student_service.add_student_from_teacher(
#             db,
#             email=email,
#             first_name=first_name,
#             last_name=last_name,
#             middle_name=middle_name,
#             image_url=image_url,
#         )

#         return {
#             "message": "Student added successfully",
#             "user_id": user.id,
#             "email": user.email,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "middle_name": user.middle_name,
#             "password": generated_password,
#             "image_url": file_service.get_file_url(image_url, "student_photos")
#         }
#     except ValueError as exc:
#         raise HTTPException(status_code=400, detail=str(exc))
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=f"Error: {str(exc)}")


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    student_task_id: int = Form(...),
    ctx: AccessContext = Depends(require_upload_media),
    db: Session = Depends(get_db)
):
    try:
        student_task, media = student_service.upload_student_task_video(
            db,
            student_task_id=student_task_id,
            uploaded_by=ctx.user_id,
            video_url=await file_service.upload_video(file),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    student = student_service.get_student_by_id(db, student_task.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    file_id = media.video_url

    return {
        "message": "video uploaded",
        "media_id": media.id,
        "student_id": student.id,
        "student_task_id": student_task.id,
        "video_id": file_id,
        "video_url": file_service.get_file_url(file_id, "videos"),
        "status": student_task.status,
        "has_video": True
    }


@router.put("/student-tasks/{student_task_id}")
def update_student_task(
    student_task_id: int,
    student_task_data: StudentTaskUpdate,
    ctx: AccessContext = Depends(require_grade_tasks),
    db: Session = Depends(get_db)
):
    try:
        student_task = student_service.update_student_task(
            db,
            student_task_id=student_task_id,
            student_task_data=student_task_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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


@router.get("/students")
def get_students(
    ctx: AccessContext = Depends(require_view_students),
    db: Session = Depends(get_db)
):
    return {"data": student_service.get_students_payload(db)}


@router.get("/students-tasks")
def get_students_tasks(
    ctx: AccessContext = Depends(require_view_students),
    db: Session = Depends(get_db)
):
    return {"data": student_service.get_students_tasks_payload(db)}
