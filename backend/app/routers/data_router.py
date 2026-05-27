from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/data", tags=["Data Collection"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/submit", response_model=schemas.SubmissionResponse)
async def submit_data(
    full_name: str = Form(...),
    address: str = Form(...),
    emergency_contact: str = Form(...),
    document: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Employee submits their data collection form with optional document upload."""

    # Check if already submitted
    existing = db.query(models.EmployeeSubmission).filter(
        models.EmployeeSubmission.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already submitted your details.")

    # Handle file upload
    document_url = None
    if document and document.filename:
        file_path = os.path.join(UPLOAD_DIR, document.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)
        document_url = f"/static/uploads/{document.filename}"

    # Save submission
    submission = models.EmployeeSubmission(
        user_id=current_user.id,
        full_name=full_name,
        address=address,
        emergency_contact=emergency_contact,
        document_url=document_url,
        status=models.SubmissionStatus.pending,
        submitted_at=datetime.now().isoformat()
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/submissions", response_model=list[schemas.SubmissionResponse])
def get_all_submissions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    """HR views all employee submissions."""
    return db.query(models.EmployeeSubmission).all()


@router.get("/my-submission", response_model=schemas.SubmissionResponse)
def get_my_submission(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Employee checks their own submission status."""
    submission = db.query(models.EmployeeSubmission).filter(
        models.EmployeeSubmission.user_id == current_user.id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="No submission found.")
    return submission


@router.put("/submissions/{submission_id}/status", response_model=schemas.SubmissionResponse)
def update_submission_status(
    submission_id: int,
    data: schemas.SubmissionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    """HR approves or rejects a submission with optional remark."""
    submission = db.query(models.EmployeeSubmission).filter(
        models.EmployeeSubmission.id == submission_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    submission.status = data.status
    submission.hr_remark = data.hr_remark
    db.commit()
    db.refresh(submission)
    return submission