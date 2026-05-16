from models import Achievement, UserAchievement

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db.database import get_db
from services.auth_service import auth_service
from schemas.auth import AdminAddUserSchema
from core.security import verify_token

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()


# =========================
# Зависимость для получения текущего пользователя из токена
# =========================
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# =========================
# Зависимость для проверки роли админа
# =========================
def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Admin role required")
    return current_user["user_id"]


# =========================
# Добавление пользователя админом
# =========================
@router.post("/add-user")
def add_user(
    data: AdminAddUserSchema,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        user = auth_service.add_user_by_admin(db, data)
        return {
            "message": f"User added successfully with role '{data.role}'",
            "user_id": user.id,
            "email": user.email,
            "password": user.plain_password if getattr(user, 'plain_password', None) else None
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    


