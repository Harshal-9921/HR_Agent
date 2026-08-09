from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .. import models, auth
from ..database import get_db

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class EmailSettingsUpdate(BaseModel):
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

@router.get("/email")
def get_email_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    settings = db.query(models.EmailSettings).first()
    if not settings:
        return {
            "sender_name": "Accops HR Onboarding",
            "sender_email": "",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password_set": False
        }
    return {
        "sender_name": settings.sender_name,
        "sender_email": settings.sender_email,
        "smtp_server": settings.smtp_server,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user,
        "smtp_password_set": bool(settings.smtp_password),
        "updated_at": settings.updated_at
    }

@router.put("/email")
def update_email_settings(
    data: EmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    settings = db.query(models.EmailSettings).first()
    if not settings:
        settings = models.EmailSettings()
        db.add(settings)
    if data.sender_name: settings.sender_name = data.sender_name
    if data.sender_email: settings.sender_email = data.sender_email
    if data.smtp_server: settings.smtp_server = data.smtp_server
    if data.smtp_port: settings.smtp_port = data.smtp_port
    if data.smtp_user: settings.smtp_user = data.smtp_user
    if data.smtp_password: settings.smtp_password = data.smtp_password
    settings.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Email settings updated successfully"}

@router.post("/email/test")
async def test_email_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    """Send a test email using current settings."""
    from ..utils.email_utils import EmailService
    settings = db.query(models.EmailSettings).first()
    try:
        es = EmailService(settings=settings)
        result = es.send_email(
            to_email=current_user.email,
            subject="Test Email — Accops HR Portal",
            html_content="<h2>Test Email</h2><p>Your email settings are working correctly!</p>"
        )
        return {"success": result, "message": "Test email sent!" if result else "Failed to send"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))