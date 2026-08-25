from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from accounts.facade import accounts_facade
from accounts.services.auth_service import auth_service
from attendance.facade import attendance_facade
from core.access import AccessContext
from core.exceptions import DomainError, to_http_exception
from core.permissions import require_manage_users
from db.database import get_db
from accounts.schemas.auth import AdminAddUserSchema, LoginSchema, StudentUpdateSchema, TeacherAddStudentSchema
from infrastructure.storage.file_service import file_service
from db.minio_client import BUCKET_NAMES

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "accounts"}


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, data=data)
    except DomainError as exc:
        to_http_exception(exc)

    return {"access_token": token, "token_type": "bearer"}


@router.post("/users", status_code=201)
def add_user(
    data: AdminAddUserSchema,
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    try:
        user = accounts_facade.add_user_by_admin(db, data=data)
    except DomainError as exc:
        to_http_exception(exc)

    return {
        "message": f"User added successfully with role '{data.role}'",
        "data": {
            "user_id": user.id,
            "email": user.email,
        },
    }


@router.post("/students", status_code=201)
async def add_student(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str | None = Form(None),
    middle_name: str = Form(...),
    birth_year: int | None = Form(None),
    parent_name: str | None = Form(None),
    parent_first_name: str | None = Form(None),
    parent_last_name: str | None = Form(None),
    parent_middle_name: str | None = Form(None),
    parent_phone: str | None = Form(None),
    parent_email: str | None = Form(None),
    image: UploadFile = File(...),
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    data = TeacherAddStudentSchema(
        email=email,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        birth_year=birth_year,
    )

    image_key = None
    try:
        image_key = await file_service.upload_image(image)
        parent = None
        if parent_phone and (parent_first_name or parent_name):
            if parent_first_name:
                resolved_first_name = parent_first_name
                resolved_last_name = parent_last_name or "Не указана"
                resolved_middle_name = parent_middle_name
            else:
                parent_parts = parent_name.split()
                resolved_first_name = parent_parts[0]
                resolved_last_name = parent_parts[1] if len(parent_parts) > 1 else "Не указана"
                resolved_middle_name = " ".join(parent_parts[2:]) or None
            parent = {
                "first_name": resolved_first_name,
                "last_name": resolved_last_name,
                "middle_name": resolved_middle_name,
                "phone": parent_phone,
                "email": parent_email,
            }
        user = accounts_facade.add_student_by_teacher(db, data=data, image_url=image_key, parent=parent)
    except DomainError as exc:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        to_http_exception(exc)
    except Exception:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        raise

    return {
        "user_id": user.id,
        "email": user.email,
    }


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    try:
        user = accounts_facade.delete_student(db, student_id=student_id)
    except DomainError as exc:
        to_http_exception(exc)

    return {
        "message": "Student deleted successfully",
        "student_id": user.id,
    }


@router.patch("/students/{student_id}")
def update_student(
    student_id: int,
    data: StudentUpdateSchema,
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    try:
        user = accounts_facade.update_student(db, student_id=student_id, data=data)
    except DomainError as exc:
        to_http_exception(exc)

    return {
        "message": "Student updated successfully",
        "data": {
            "student_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "birth_year": user.student_profile.birth_year if user.student_profile else None,
        },
    }
