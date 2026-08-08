from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from accounts.facade import accounts_facade
from accounts.services.auth_service import auth_service
from core.access import AccessContext
from core.exceptions import DomainError, to_http_exception
from core.permissions import require_manage_users
from db.database import get_db
from schemas.auth import LoginSchema, TeacherAddStudentSchema
from services.file_service import file_service

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


@router.post("/students", status_code=201)
async def add_student(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str | None = Form(None),
    middle_name: str = Form(...),
    image: UploadFile = File(...),
    ctx: AccessContext = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    data = TeacherAddStudentSchema(
        email=email,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
    )

    try:
        image_url = await file_service.upload_image(image)
        user, generated_password = accounts_facade.add_student_by_teacher(db, data=data, image_url=image_url)
    except DomainError as exc:
        to_http_exception(exc)

    return {
        "user_id": user.id,
        "password": generated_password,
        "email": user.email,
    }
