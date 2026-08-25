from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO)
from core.exceptions import DomainError, ConflictError, NotFoundError, PermissionDenied, ValidationError
from profile.api.dashboard import router as profile_dashboard_router
from profile.api.routes import router as profile_router
from accounts.api.auth import router as accounts_auth_router
from education.api.routes import router as education_router
from achievements.api.routes import router as achievements_router
from public.api.routes import router as public_router
from assessment.api.routes import router as assessment_router_context
from media.api.routes import router as media_router
from catalog.api.routes import router as catalog_router
from consultations.api.student import router as consultations_student_router
from consultations.api.admin import router as consultations_admin_router
from attendance.api.admin import router as attendance_admin_router, student_router as attendance_student_router
from schedule.api.routes import router as calendar_router
from news.api.admin import router as news_admin_router
from news.api.public import router as news_public_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Alanko API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError):
    status_code = 400
    if isinstance(exc, PermissionDenied):
        status_code = 403
    elif isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ConflictError):
        status_code = 409
    elif isinstance(exc, ValidationError):
        status_code = 422
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "alanko"}


@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}


app.include_router(accounts_auth_router, prefix="/api")
app.include_router(education_router, prefix="/api")
app.include_router(achievements_router, prefix="/api")
app.include_router(assessment_router_context, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(profile_dashboard_router, prefix="/api/profile")
app.include_router(profile_router, prefix="/api")
app.include_router(public_router, prefix="/api")
# Online payment API is intentionally disabled. The implementation remains in
# payments/api/routes.py, but none of these endpoints is registered:
# POST /api/payments/course
# POST /api/payments/special-offer
# GET  /api/payments/{payment_id}
# POST /api/payments/{payment_id}/confirm
# POST /api/payments/webhook
app.include_router(consultations_student_router, prefix="/api")
app.include_router(consultations_admin_router, prefix="/api")
app.include_router(attendance_admin_router, prefix="/api")
app.include_router(attendance_student_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(news_admin_router, prefix="/api")
app.include_router(news_public_router, prefix="/api")


