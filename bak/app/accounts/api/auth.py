from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from accounts.facade import accounts_facade
from accounts.services.auth_service import auth_service
from attendance.facade import attendance_facade
from core.access import AccessContext
from core.exceptions import ConflictError, DomainError, to_http_exception
from core.permissions import get_access_context, require_manage_users
from db.database import get_db
from accounts.schemas.auth import AdminAddUserSchema, LoginSchema, StudentUpdateSchema, TeacherAddStudentSchema, TeacherUpdateSchema
from infrastructure.storage.file_service import file_service
from db.minio_client import BUCKET_NAMES
from accounts.repositories.user_repository import user_repository

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, data=data)
    except DomainError as exc:
        to_http_exception(exc)

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_current_user_profile(
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db),
):
    user = user_repository.get_by_id(db, ctx.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "full_name": " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.email,
        "role": next((item.role.name for item in user.roles if item.role), None),
        "image_url": user.image_url,
    }


@router.post("/users", status_code=201)
def add_user(
    data: AdminAddUserSchema,
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    try:
        user, generated_password = accounts_facade.add_user_by_admin(db, data=data)
    except DomainError as exc:
        to_http_exception(exc)

    return {
        "message": f"User added successfully with role '{data.role}'",
        "data": {
            "user_id": user.id,
            "email": user.email,
            "password": generated_password,
        },
    }


@router.post("/teachers", status_code=201)
async def add_teacher(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str | None = Form(None),
    middle_name: str = Form(...),
    role: str = Form("teacher"),
    password: str | None = Form(None),
    image: UploadFile | None = File(None),
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    if role != "teacher":
        raise ConflictError("This endpoint only creates teachers")
    data = AdminAddUserSchema(email=email, password=password, first_name=first_name, last_name=last_name, middle_name=middle_name, role=role)
    image_key = None
    try:
        if image and image.filename:
            image_key = await file_service.upload_image(image)
        user, generated_password = accounts_facade.add_user_by_admin(db, data=data, image_url=image_key)
    except DomainError as exc:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        to_http_exception(exc)
    except Exception:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        raise
    return {
        "message": "Teacher added successfully",
        "data": {
            "user_id": user.id,
            "email": user.email,
            "password": generated_password,
            "avatar_url": file_service.get_file_url(image_key, BUCKET_NAMES["student_photos"]) if image_key else None,
        },
    }


@router.get("/teachers/{teacher_id}")
def get_teacher_details(teacher_id: int, ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    try:
        return {"data": accounts_facade.get_teacher_details(db, teacher_id=teacher_id)}
    except DomainError as exc:
        to_http_exception(exc)


@router.patch("/teachers/{teacher_id}")
def update_teacher(teacher_id: int, data: TeacherUpdateSchema, ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    try:
        return {"data": accounts_facade.update_teacher(db, teacher_id=teacher_id, data=data)}
    except DomainError as exc:
        to_http_exception(exc)


@router.patch("/teachers/{teacher_id}/photo")
async def update_teacher_photo(teacher_id: int, image: UploadFile = File(...), ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    image_key = None
    try:
        image_key = await file_service.upload_image(image)
        details = accounts_facade.update_teacher_photo(db, teacher_id=teacher_id, image_url=image_key)
    except DomainError as exc:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        to_http_exception(exc)
    except Exception:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        raise
    return {"data": details}


@router.post("/teachers/{teacher_id}/password/reset")
def reset_teacher_password(teacher_id: int, ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    try:
        password = accounts_facade.reset_teacher_password(db, teacher_id=teacher_id)
    except DomainError as exc:
        to_http_exception(exc)
    return {"data": {"teacher_id": teacher_id, "password": password}}


@router.delete("/teachers/{teacher_id}", status_code=204)
def delete_teacher(teacher_id: int, ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    try:
        accounts_facade.delete_teacher(db, teacher_id=teacher_id)
    except DomainError as exc:
        to_http_exception(exc)


@router.get("/users")
def list_users(
    role: str | None = Query(default=None),
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    return {"data": accounts_facade.list_users(db, role=role)}


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
        image: UploadFile | None = File(None),
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
        if image and image.filename:
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
        "image_url": (
            file_service.get_file_url(image_key, BUCKET_NAMES["student_photos"])
            if image_key
            else None
        ),
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


@router.get("/students/{student_id}")
def get_student_details(student_id: int, ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    try:
        return {"data": accounts_facade.get_student_details(db, student_id=student_id)}
    except DomainError as exc:
        to_http_exception(exc)


@router.post("/students/{student_id}/password/reset")
def reset_student_password(student_id: int, ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    try:
        password = accounts_facade.reset_student_password(db, student_id=student_id)
    except DomainError as exc:
        to_http_exception(exc)
    return {"data": {"student_id": student_id, "password": password}}


@router.patch("/students/{student_id}/photo")
async def update_student_photo(student_id: int, image: UploadFile = File(...), ctx: AccessContext = Depends(require_manage_users), db: Session = Depends(get_db)):
    image_key = None
    try:
        image_key = await file_service.upload_image(image)
        details = accounts_facade.update_student_photo(db, student_id=student_id, image_url=image_key)
    except DomainError as exc:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        to_http_exception(exc)
    except Exception:
        if image_key:
            file_service.delete_file(image_key, BUCKET_NAMES["student_photos"])
        raise
    return {"data": details}


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
