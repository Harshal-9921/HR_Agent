import json
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
    default_sop_path: Optional[str] = None

class TestEmailRequest(BaseModel):
    to_email: Optional[str] = None

@router.get("/email")
def get_email_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    settings = db.query(models.EmailSettings).first()
    if not settings:
        return {"cc_emails": "", "default_sop_path": ""}
    return {
        "cc_emails": settings.cc_emails or "",
        "default_sop_path": settings.default_sop_path or "",
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
    if data.default_sop_path is not None:
        settings.default_sop_path = data.default_sop_path
    settings.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Email settings updated successfully"}

@router.post("/email/test")
def test_email_settings(
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

@router.get("/templates")
def list_templates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    templates = db.query(models.EmailTemplate).all()
    return [
        {"template_key": t.template_key, "subject": t.subject, "updated_at": t.updated_at}
        for t in templates
    ]

@router.get("/templates/{template_key}")
def get_template(
    template_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    template = db.query(models.EmailTemplate).filter(
        models.EmailTemplate.template_key == template_key
    ).first()
    if not template:
        return {"template_key": template_key, "subject": "", "html_body": "", "sections": {}}
    sections = {}
    if template.sections:
        try:
            sections = json.loads(template.sections)
        except Exception:
            sections = {}
    return {
        "template_key": template.template_key,
        "subject": template.subject,
        "html_body": template.html_body,
        "sections": sections,
        "updated_at": template.updated_at
    }

class EmailTemplateUpdate(BaseModel):
    subject: Optional[str] = None
    html_body: Optional[str] = None

@router.put("/templates/{template_key}")
def update_template(
    template_key: str,
    data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    template = db.query(models.EmailTemplate).filter(
        models.EmailTemplate.template_key == template_key
    ).first()
    if not template:
        template = models.EmailTemplate(template_key=template_key)
        db.add(template)
    if data.subject is not None:
        template.subject = data.subject
    if data.html_body is not None:
        template.html_body = data.html_body
    if data.sections is not None:
        template.sections = json.dumps(data.sections)
    template.updated_at = datetime.now().isoformat()
    template.updated_by = current_user.id
    db.commit()
    return {"message": "Template updated successfully"}

class EmailTemplateUpdate(BaseModel):
    subject: Optional[str] = None
    html_body: Optional[str] = None
    sections: Optional[dict] = None
