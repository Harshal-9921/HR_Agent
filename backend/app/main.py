from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from . import models, database
from .routers import auth_router, employee_router, content_router, data_router, logs_router, chat_router, settings_router

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="HR Onboarding Portal", version="1.0.0")

# Mount static files for uploads
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(employee_router.router)
app.include_router(content_router.router)
app.include_router(data_router.router)
app.include_router(logs_router.router)
app.include_router(chat_router.router)
app.include_router(settings_router.router)

def _ensure_keka_content():
    from .database import SessionLocal
    from . import models
    db = SessionLocal()
    try:
        existing = db.query(models.Content).filter(models.Content.is_keka == True).first()
        if not existing:
            keka = models.Content(
                title="Keka Acknowledgement",
                description="Please confirm you have reviewed and accepted your Keka onboarding documents.",
                content_type=models.ContentType.pdf,
                order=-1,  # sorts before everything else by default
                is_intro=False,
                is_enabled=True,
                is_keka=True,
                role_visibility=None,  # None = visible to all roles initially
            )
            db.add(keka)
            db.commit()
    finally:
        db.close()

_ensure_keka_content()

@app.get("/")
def root():
    return {"message": "Employee Portal Backend Running"}