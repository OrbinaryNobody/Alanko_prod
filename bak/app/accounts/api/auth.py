from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from accounts.services.auth_service import auth_service
from core.exceptions import DomainError, to_http_exception
from db.database import get_db
from schemas.auth import LoginSchema

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
