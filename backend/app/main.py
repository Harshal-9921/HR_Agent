from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles 
from . import models, database
from .routers import auth_router, employee_router, content_router, data_router, logs_router, chat_router, policy_router, settings_router
from fastapi import APIRouter, HTTPException, status
from typing import Any, Dict

# Provide a local implementation for policy_router with implemented methods
class _PolicyRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/policies", tags=["policies"])
        # simple in-memory store: id -> policy dict
        self._store: Dict[int, Dict[str, Any]] = {}
        self._next_id = 1

        @self.router.get("/", summary="List policies")
        def list_policies():
            return list(self._store.values())

        @self.router.get("/{policy_id}", summary="Get policy by id")
        def get_policy(policy_id: int):
            policy = self._store.get(policy_id)
            if not policy:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
            return policy

        @self.router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a policy")
        def create_policy(payload: Dict[str, Any]):
            pid = self._next_id
            self._next_id += 1
            policy = {"id": pid, **payload}
            self._store[pid] = policy
            return policy

        @self.router.put("/{policy_id}", summary="Update a policy")
        def update_policy(policy_id: int, payload: Dict[str, Any]):
            if policy_id not in self._store:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
            policy = {"id": policy_id, **payload}
            self._store[policy_id] = policy
            return policy

        @self.router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a policy")
        def delete_policy(policy_id: int):
            if policy_id not in self._store:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
            del self._store[policy_id]
            return None


class _SettingsRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/settings", tags=["settings"])
        self._store: Dict[str, Any] = {
            "theme": "light",
            "notifications": True,
            "language": "en",
        }

        @self.router.get("/", summary="List all settings")
        def list_settings():
            return self._store

        @self.router.get("/{setting_key}", summary="Get setting by key")
        def get_setting(setting_key: str):
            if setting_key not in self._store:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
            return {setting_key: self._store[setting_key]}

        @self.router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a new setting")
        def create_setting(payload: Dict[str, Any]):
            if not payload or len(payload) != 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload must contain exactly one setting")
            key, value = next(iter(payload.items()))
            if key in self._store:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setting already exists")
            self._store[key] = value
            return {key: value}

        @self.router.put("/{setting_key}", summary="Update a setting")
        def update_setting(setting_key: str, payload: Dict[str, Any]):
            if setting_key not in self._store:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
            if not payload or len(payload) != 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload must contain exactly one setting value")
            value = next(iter(payload.values()))
            self._store[setting_key] = value
            return {setting_key: value}

        @self.router.delete("/{setting_key}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a setting")
        def delete_setting(setting_key: str):
            if setting_key not in self._store:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
            del self._store[setting_key]
            return None


# instantiate to match expected name
policy_router = _PolicyRouter()
settings_router = _SettingsRouter()
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="HR Onboarding Portal", version="1.0.0")

# Mount static files for uploads
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
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
app.include_router(policy_router.router)
app.include_router(settings_router.router)

@app.get("/")
def root():
    return {"message": "Employee Portal Backend Running"}
