from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.auth import LoginSchema
from db.database import get_db
from services.auth_service import auth_service

router = APIRouter()

@router.post("/")
async def state():
	return{"state": "work"}


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {"access_token": token, "token_type": "bearer"}
