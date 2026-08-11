from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .. import models, auth
from ..database import get_db
router = APIRouter(prefix="/api/settings", tags=["Settings"])

class EmailSettingsUpdate(BaseModel):
    cc_emails: Optional[str] = None

class TestEmailRequest(BaseModel):
    to_email: Optional[str] = None  # if omitted, falls back to current_user.email

@router.get("/email")
def get_email_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    settings = db.query(models.EmailSettings).first()
    if not settings:
        return {"cc_emails": ""}
    return {
        "cc_emails": settings.cc_emails or "",
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
    if data.cc_emails is not None:
        settings.cc_emails = data.cc_emails
    settings.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Email settings updated successfully"}

@router.post("/email/test")
async def test_email_settings(
    data: TestEmailRequest = TestEmailRequest(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    """Send a test email using the fixed backend-configured sender, including current CC list."""
    from ..utils.email_utils import EmailService
    settings = db.query(models.EmailSettings).first()
    cc_list = None
    if settings and settings.cc_emails:
        cc_list = [e.strip() for e in settings.cc_emails.split(",") if e.strip()]

    target = data.to_email or current_user.email
    try:
        result = EmailService.send_email(
            to_email=target,
            subject="Test Email — Accops HR Portal",
            html_content="<h2>Test Email</h2><p>Your email settings are working correctly!</p>",
            cc_emails=cc_list
        )
        return {"success": result, "message": f"Test email sent to {target}!" if result else "Failed to send"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))