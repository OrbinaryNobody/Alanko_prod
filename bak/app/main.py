from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)
from api import auth
from db.init_db import init_db
from core.minio_init import init_minio
from api.teacher import router as teacher_router
from api.admin import router as admin_router
from api.user import router as user_router
from api.assessment import router as assessment_router
from api.public import router as public_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
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

app.include_router(auth.router, prefix="/auth")

app.include_router(teacher_router)
app.include_router(assessment_router)

app.include_router(admin_router)
app.include_router(user_router)
app.include_router(public_router)



