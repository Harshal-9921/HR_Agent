from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import csv
import io
import string
import random

from .. import schemas, models, auth, database

router = APIRouter(prefix="/api/employees", tags=["employees"])

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

@router.get("/", response_model=List[schemas.UserResponse])
def get_employees(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    return db.query(models.User).filter(models.User.role != models.RoleEnum.admin).all()

@router.get("/with-progress")
def get_employees_with_progress(
    include_archived: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    """Returns employees with their live module completion stats."""
    query = db.query(models.User).filter(models.User.role != models.RoleEnum.admin)
    if not include_archived:
        query = query.filter(models.User.is_archived == False)
    employees = query.all()

    result = []
    for emp in employees:
        applicable_contents = db.query(models.Content).filter(
            models.Content.is_enabled == True
        ).all()
        total_content = len(applicable_contents)
        applicable_ids = {c.id for c in applicable_contents}
        completed = db.query(models.ModuleProgress).filter(
            models.ModuleProgress.user_id == emp.id,
            models.ModuleProgress.completed == True,
            models.ModuleProgress.content_id.in_(applicable_ids)
        ).count()
        pct = int((completed / total_content) * 100) if total_content > 0 else 0
        result.append({
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "department": emp.department,
            "doj": emp.doj,
            "role": emp.role.value,
            "is_active": emp.is_active,
            "modules_completed": completed,
            "total_modules": total_content,
            "completion_pct": pct,
            "is_archived": emp.is_archived,
        })
    return result

@router.post("/", response_model=schemas.UserResponse)
def create_employee(
    data: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        (models.User.email == (data.email or data.personal_email)) | (models.User.personal_email == data.personal_email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Generate a temporary password
    temp_password = generate_random_password() 
    new_user = models.User(
        name=data.name,
        email=data.email or data.personal_email,  # Use personal_email if company email not provided
        personal_email=data.personal_email,
        hashed_password=auth.get_password_hash(temp_password),
        role=data.role,
        department=data.department,
        doj=data.doj,
        is_first_login=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize Onboarding Progress
    progress = models.OnboardingProgress(
        user_id=new_user.id,
        current_step=1,
        last_activity_at=datetime.now().isoformat()
    )
    db.add(progress)
    db.commit()
    
    try:
        from ..worker import send_onboarding_email, daily_onboarding_check
        import logging

        today = datetime.now().date()
        try:
            doj = datetime.strptime(str(new_user.doj), "%Y-%m-%d").date() if new_user.doj else None
        except Exception:
            doj = None

        if doj:
            if doj <= today:
                # Day 0 or past DOJ — send immediately
                send_onboarding_email.delay(new_user.id, "Day 0", {"password": temp_password})
                logging.info(f"Day 0 email queued for {new_user.email}, DOJ: {doj}")
            elif doj == today + timedelta(days=2):
                # T-2 email
                send_onboarding_email.delay(new_user.id, "T-2", {"password": temp_password})
                logging.info(f"T-2 email queued for {new_user.email}, DOJ: {doj}")
            else:
                logging.info(f"No immediate email for {new_user.email} - DOJ {doj} is in future")
        else:
            logging.warning(f"Could not parse DOJ for {new_user.email}: {new_user.doj}")

        daily_onboarding_check.delay()
    except Exception as e:
        import logging
        logging.warning(f"Celery task could not be queued (Redis may not be running): {e}")
@router.post("/{user_id}/control")
def control_employee_progress(
    user_id: int,
    action: str,
    content_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    """HR controls employee onboarding progress."""
    if action == "reset_all":
        db.query(models.ModuleProgress).filter(
            models.ModuleProgress.user_id == user_id
        ).delete()
        db.query(models.EmployeeSubmission).filter(
            models.EmployeeSubmission.user_id == user_id
        ).delete()
        onboarding = db.query(models.OnboardingProgress).filter(
            models.OnboardingProgress.user_id == user_id
        ).first()
        if onboarding:
            onboarding.current_step = 1
            onboarding.completion_percentage = 0
        db.commit()
        return {"message": "Onboarding reset successfully."}

    elif action == "reset_module":
        if not content_id:
            raise HTTPException(status_code=400, detail="content_id required for reset_module")
        db.query(models.ModuleProgress).filter(
            models.ModuleProgress.user_id == user_id,
            models.ModuleProgress.content_id == content_id
        ).delete()
        db.commit()
        return {"message": "Module reset successfully."}

    elif action in ["next", "prev"]:
        all_contents = db.query(models.Content).filter(
            models.Content.is_enabled == True
        ).order_by(models.Content.order).all()

        completed = db.query(models.ModuleProgress).filter(
            models.ModuleProgress.user_id == user_id,
            models.ModuleProgress.completed == True
        ).all()
        completed_ids = {p.content_id for p in completed}

        if action == "next":
            for content in all_contents:
                if content.id not in completed_ids:
                    new_progress = models.ModuleProgress(
                        user_id=user_id,
                        content_id=content.id,
                        completed=True,
                        score=0,
                        total_questions=0,
                        attempt_count=0,
                        completed_at=datetime.now().isoformat()
                    )
                    db.add(new_progress)
                    db.commit()
                    return {"message": "Employee moved to next module."}
            return {"message": "Employee has already completed all modules."}

        elif action == "prev":
            completed_contents = [c for c in all_contents if c.id in completed_ids]
            if not completed_contents:
                return {"message": "No completed modules to revert."}
            last = completed_contents[-1]
            db.query(models.ModuleProgress).filter(
                models.ModuleProgress.user_id == user_id,
                models.ModuleProgress.content_id == last.id
            ).delete()
            db.commit()
            return {"message": "Employee moved back to previous module."}

    raise HTTPException(status_code=400, detail="Invalid action.")


@router.get("/{user_id}/report")
def get_employee_report(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    """HR gets detailed report for a specific employee."""
    employee = db.query(models.User).filter(models.User.id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    contents = db.query(models.Content).filter(
        models.Content.is_enabled == True
    ).order_by(models.Content.order).all()

    progress_records = db.query(models.ModuleProgress).filter(
        models.ModuleProgress.user_id == user_id
    ).all()
    progress_map = {p.content_id: p for p in progress_records}

    total_score = 0
    max_score = 0
    modules_data = []

    for content in contents:
        p = progress_map.get(content.id)
        if p and p.completed:
            module_score_pct = 100 if p.attempt_count <= 1 else 75
            total_score += module_score_pct
        else:
            module_score_pct = 0
        max_score += 100

        modules_data.append({
            "module_id": content.id,
            "module_title": content.title,
            "is_intro": content.is_intro,
            "completed": p.completed if p else False,
            "score": p.score if p else 0,
            "total_questions": p.total_questions if p else 0,
            "attempt_count": p.attempt_count if p else 0,
            "module_score_pct": module_score_pct,
            "completed_at": p.completed_at if p else None,
            "time_spent_seconds": p.time_spent_seconds if p else 0,
        })

    overall_pct = round((total_score / max_score) * 100) if max_score > 0 else 0

    if overall_pct >= 90:
        rating = "Excellent"
    elif overall_pct >= 75:
        rating = "Good"
    elif overall_pct >= 50:
        rating = "Needs Improvement"
    else:
        rating = "Incomplete"

    acknowledgement = db.query(models.EmployeeSubmission).filter(
        models.EmployeeSubmission.user_id == user_id
    ).first()

    return {
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "doj": employee.doj,
            "role": employee.role.value,
        },
        "modules": modules_data,
        "summary": {
            "total_modules": len(contents),
            "completed_modules": sum(1 for m in modules_data if m["completed"]),
            "overall_score_pct": overall_pct,
            "rating": rating,
            "acknowledged_at": acknowledgement.submitted_at if acknowledgement else None,
            "completion_date": max(
                (m["completed_at"] for m in modules_data if m["completed_at"]),
                default=None
            ),
        }
    }


@router.get("/my-report")
def get_my_report(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Employee gets their own completion report."""
    contents = db.query(models.Content).filter(
        models.Content.is_enabled == True
    ).order_by(models.Content.order).all()

    progress_records = db.query(models.ModuleProgress).filter(
        models.ModuleProgress.user_id == current_user.id
    ).all()
    progress_map = {p.content_id: p for p in progress_records}

    total_score = 0
    max_score = 0
    modules_data = []

    for content in contents:
        p = progress_map.get(content.id)
        if p and p.completed:
            module_score_pct = 100 if p.attempt_count <= 1 else 75
            total_score += module_score_pct
        else:
            module_score_pct = 0
        max_score += 100

        modules_data.append({
            "module_title": content.title,
            "is_intro": content.is_intro,
            "completed": p.completed if p else False,
            "score": p.score if p else 0,
            "total_questions": p.total_questions if p else 0,
            "attempt_count": p.attempt_count if p else 0,
            "module_score_pct": module_score_pct,
            "completed_at": p.completed_at if p else None,
            "time_spent_seconds": p.time_spent_seconds if p else 0,
        })

    overall_pct = round((total_score / max_score) * 100) if max_score > 0 else 0

    if overall_pct >= 90:
        rating = "Excellent"
    elif overall_pct >= 75:
        rating = "Good"
    elif overall_pct >= 50:
        rating = "Needs Improvement"
    else:
        rating = "Incomplete"

    return {
        "modules": modules_data,
        "summary": {
            "total_modules": len(contents),
            "completed_modules": sum(1 for m in modules_data if m["completed"]),
            "overall_score_pct": overall_pct,
            "rating": rating,
        }
    }
@router.get("/{user_id}/report/csv")
def download_employee_report_csv(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    report = get_employee_report(user_id, db, current_user)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee Name", report["employee"]["name"]])
    writer.writerow(["Email", report["employee"]["email"]])
    writer.writerow(["Department", report["employee"]["department"]])
    writer.writerow(["Overall Score %", report["summary"]["overall_score_pct"]])
    writer.writerow(["Rating", report["summary"]["rating"]])
    writer.writerow([])
    writer.writerow(["Module", "Completed", "Score", "Total Questions", "Attempts", "Module Score %", "Completed At"])
    for m in report["modules"]:
        writer.writerow([m["module_title"], m["completed"], m["score"], m["total_questions"], m["attempt_count"], m["module_score_pct"], m["completed_at"]])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{report['employee']['name'].replace(' ', '_')}.csv"}
    )


@router.get("/reports/csv/all")
def download_all_reports_csv(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    employees = db.query(models.User).filter(models.User.role != models.RoleEnum.admin).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Department", "DOJ", "Overall Score %", "Rating", "Modules Completed", "Total Modules"])
    for emp in employees:
        report = get_employee_report(emp.id, db, current_user)
        writer.writerow([
            emp.name, emp.email, emp.department, emp.doj,
            report["summary"]["overall_score_pct"], report["summary"]["rating"],
            report["summary"]["completed_modules"], report["summary"]["total_modules"]
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_employee_reports.csv"}
    )

@router.put("/{user_id}/archive")
def toggle_archive(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_archived = not user.is_archived
    db.commit()
    return {"message": f"User {'archived' if user.is_archived else 'unarchived'} successfully.", "is_archived": user.is_archived}

@router.get("/with-progress")
def get_employees_with_progress(
    include_archived: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.admin, models.RoleEnum.hr]))
):
    query = db.query(models.User).filter(models.User.role != models.RoleEnum.admin)
    if not include_archived:
        query = query.filter(models.User.is_archived == False)
    employees = query.all()

class UpdateEmployeeRequest(BaseModel):
    name: Optional[str] = None
    personal_email: Optional[str] = None
    department: Optional[str] = None
    doj: Optional[str] = None
    role: Optional[str] = None

@router.put("/{user_id}")
def update_employee(
    user_id: int,
    data: UpdateEmployeeRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role([models.RoleEnum.hr, models.RoleEnum.admin]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    if data.name: user.name = data.name
    if data.personal_email: user.personal_email = data.personal_email
    if data.department: user.department = data.department
    if data.doj: user.doj = data.doj
    if data.role: user.role = data.role
    db.commit()
    db.refresh(user)
    return {"message": "Employee updated successfully"}