from sqlalchemy.orm import Session 
from fastapi import APIRouter


router = APIRouter(prefix = "", tags = ["education"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "education"}