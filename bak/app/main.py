from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)
from db.init_db import init_db
from core.minio_init import init_minio
from admin.api.routes import router as admin_router
from profile.api.dashboard import router as profile_dashboard_router
from profile.api.routes import router as profile_router
from accounts.api.auth import router as accounts_auth_router
from education.api.routes import router as education_router
from achievements.api.routes import router as achievements_router
from public.api.routes import router as public_router
from assessment.api.routes import router as assessment_router_context
from media.api.routes import router as media_router
from catalog.api.routes import router as catalog_router
from payments.api.routes import router as payments_router
from consultations.api.student import router as consultations_student_router
from consultations.api.admin import router as consultations_admin_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Alanko API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    import sys
    print("=== ON_STARTUP CALLED ===", file=sys.stderr)
    try:
        print("=== CALLING init_db ===", file=sys.stderr)
        init_db()
        print("=== init_db COMPLETED ===", file=sys.stderr)
    except Exception as e:
        print(f"=== ERROR IN init_db: {e} ===", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    try:
        print("=== CALLING init_minio ===", file=sys.stderr)
        init_minio()
        print("=== init_minio COMPLETED ===", file=sys.stderr)
    except Exception as e:
        print(f"=== ERROR IN init_minio: {e} ===", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "alanko"}


app.include_router(accounts_auth_router, prefix="/api")
app.include_router(education_router, prefix="/api")
app.include_router(achievements_router, prefix="/api")
app.include_router(assessment_router_context, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(profile_dashboard_router, prefix="/api/profile")
app.include_router(profile_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(payments_router, prefix="/api", tags=["Payments"])
app.include_router(consultations_student_router, prefix="/api")
app.include_router(consultations_admin_router, prefix="/api")


