# -*- coding: utf-8 -*-
from celery import Celery  # type: ignore[import]
try:
    from celery.schedules import crontab  # type: ignore[import]
except ImportError:
    from celery.beat import crontab  # type: ignore[import]
from datetime import datetime, timedelta
import os
from .database import SessionLocal
from .models import User, EmailLog, EmailStatus, EmailSettings, OnboardingProgress, ModuleProgress, Content, RoleEnum
from .utils.email_utils import EmailService
import secrets
import string
from . import auth

def _generate_temp_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "onboarding_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Prevent Celery from blocking FastAPI startup if Redis is slow
celery_app.conf.update(
    broker_connection_retry_on_startup=False,
    broker_transport_options={"socket_timeout": 5, "socket_connect_timeout": 5},
    result_backend_transport_options={"socket_timeout": 5, "socket_connect_timeout": 5},
)

# Run every day at 9:00 AM IST (3:30 UTC)
celery_app.conf.beat_schedule = {
    'daily-onboarding-check': {
        'task': 'app.worker.daily_onboarding_check',
        'schedule': crontab(hour=3, minute=30),
    },
}
celery_app.conf.timezone = 'UTC'


def _get_module_info(db, user_id):
    """Helper: returns (completed_titles, remaining_titles, total_count, completed_count)."""
    all_content = db.query(Content).order_by(Content.order).all()
    completed_ids = {
        r.content_id
        for r in db.query(ModuleProgress).filter(
            ModuleProgress.user_id == user_id,
            ModuleProgress.completed == True
        ).all()
    }
    completed_titles = [c.title for c in all_content if c.id in completed_ids]
    remaining_titles = [c.title for c in all_content if c.id not in completed_ids]
    return completed_titles, remaining_titles, len(all_content), len(completed_ids)


# ─── Task: send 2 emails ────────────────────────────────────────────────
@celery_app.task(bind=True, max_retries=3)
def send_onboarding_email(self, user_id: int, email_type: str, context: dict = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        from .database import SessionLocal as _SessionLocal
        from .models import EmailSettings as _EmailSettings
        _db = _SessionLocal()
        try:
                _settings = _db.query(_EmailSettings).first()
                email_service = EmailService()
        finally:
            _db.close()
        first_name = user.name.split()[0] if user.name else "New Joiner"
        personal_email = user.personal_email or user.email
        company_email = user.email
        password = context.get("password", "") if context else ""
        portal_url = "http://10.130.37.2"

        if email_type == "Day 0":
            # EMAIL 1 — Welcome Email 
            subject = "Welcome to Accops Systems! 🎉"
            html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
    <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Accops! 🚀</h1>
  </div>

  <p style="font-size: 16px;">Dear <strong>{first_name}</strong>,</p>

  <p style="font-size: 15px; line-height: 1.6;">
    Welcome to Accops! We're excited to have you onboard as an <strong>Accopsian</strong>.
  </p>

  <p style="font-size: 15px; line-height: 1.6;">
    To begin your onboarding journey, you will shortly receive a separate email with your 
    <strong>login credentials</strong> for the HR Onboarding Portal. Once you receive them, 
    you can log in and get started at:
  </p>

  <div style="text-align: center; margin: 25px 0;">
    <a href="{portal_url}" style="background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-size: 16px; font-weight: bold;">
      Access Onboarding Portal
    </a>
  </div>

  <p style="font-size: 15px; line-height: 1.6;">Below is the onboarding flow you will go through:</p>

  <ul style="font-size: 15px; line-height: 2;">
    <li>🏢 <strong>Company Introduction</strong></li>
    <li>📋 <strong>Policy Introduction</strong></li>
    <li>💡 <strong>Product Trainings</strong></li>
    <li>📚 <strong>Keep Learning</strong></li>
  </ul>

  <p style="font-size: 15px; line-height: 1.6;">
    Once you complete the above modules, the next set of trainings will be automatically 
    available on the portal based on your department.
  </p>

  <p style="font-size: 15px; line-height: 1.6;">
    Wishing you a great start and a successful journey with us. 
    <strong>Congratulations once again on being a part of Accops!</strong>
  </p>

  <p style="font-size: 15px;">Warm regards,<br><strong>HR Team</strong><br>Accops Systems Pvt. Ltd.</p>

  <div style="border-top: 1px solid #eee; margin-top: 25px; padding-top: 15px; font-size: 12px; color: #999; text-align: center;">
    This is an automated email from the Accops HR Onboarding System.
  </div>
</body>
</html>
"""
            # Send welcome email
            # Get CC emails from settings
            cc_list = []
            if _settings and _settings.cc_emails:
              cc_list = [e.strip() for e in _settings.cc_emails.split(',') if e.strip()]

            result = email_service.send_email(
              to_email=personal_email,
              subject=subject,
              html_content=html_content,
              cc_emails=cc_list if cc_list else None
            )

            # Log the Day 0 email
            log_entry = EmailLog(
              user_id=user_id,
              email_type="Day 0",
              status=EmailStatus.sent if result else EmailStatus.failed,
              sent_at=datetime.now().isoformat()
            )
            db.add(log_entry)
            db.commit()

            # Queue credentials email after 15 minutes
            send_credentials_email.apply_async(
              args=[user_id, password],
              countdown=900  # 15 minutes
            )

        elif email_type == "T-2":
            subject = "You're joining Accops in 2 days! 🎉"
            html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
    <h1 style="color: white; margin: 0;">See You Soon, {first_name}! 👋</h1>
  </div>
  <p>Dear <strong>{first_name}</strong>,</p>
  <p style="line-height: 1.6;">We're looking forward to welcoming you to Accops in <strong>2 days</strong>! 
  Get ready for an exciting journey ahead.</p>
  <p style="line-height: 1.6;">On your joining day, you will receive your login credentials for the 
  HR Onboarding Portal via email. Please keep an eye on your inbox.</p>
  <p>See you soon!<br><strong>HR Team</strong><br>Accops Systems Pvt. Ltd.</p>
</body>
</html>
"""
            email_service.send_email(
            to_email=personal_email,
            subject=subject,
            html_content=html_content,
            cc_emails=cc_list if cc_list else None
            )
            log = EmailLog(
                user_id=user_id,
                email_type="T-2",
                status=EmailStatus.sent,
                sent_at=datetime.now().isoformat()
            )
            db.add(log)
            db.commit()

        elif email_type == "Reminder":
            subject = "Reminder: Complete Your Onboarding"
            html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <p>Dear <strong>{first_name}</strong>,</p>
  <p>This is a friendly reminder to complete your onboarding on the Accops HR Portal.</p>
  <div style="text-align: center; margin: 20px 0;">
    <a href="{portal_url}" style="background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">
      Continue Onboarding
    </a>
  </div>
  <p>Regards,<br><strong>HR Team</strong><br>Accops Systems Pvt. Ltd.</p>
</body>
</html>
"""
            email_service.send_email(
                to_email=company_email,
                subject=subject,
                html_content=html_content
            )
            log = EmailLog(
                user_id=user_id,
                email_type="Reminder",
                status=EmailStatus.sent,
                sent_at=datetime.now().isoformat()
            )
            db.add(log)
            db.commit()

    except Exception as e:
        db.rollback()
        countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=Exception("Email send failed, retrying..."), countdown=countdown)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_credentials_email(self, user_id: int, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        settings = db.query(EmailSettings).first()
        cc_list = []
        if settings and settings.cc_emails:
            cc_list = [e.strip() for e in settings.cc_emails.split(',') if e.strip()]

        email_service = EmailService()
        first_name = user.name.split()[0] if user.name else "New Joiner"
        personal_email = user.personal_email or user.email
        portal_url = "http://10.130.37.2"

        subject = "Your Accops Onboarding Portal Credentials"
        html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
    <h1 style="color: white; margin: 0;">Your Login Credentials 🔐</h1>
  </div>

  <p>Dear <strong>{first_name}</strong>,</p>

  <p style="line-height: 1.6;">
    As mentioned in our earlier email, here are your login credentials for the 
    <strong>Accops HR Onboarding Portal</strong>:
  </p>

  <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0;">
    <table style="width: 100%; font-size: 15px;">
      <tr>
        <td style="padding: 8px 0; color: #666; width: 40%;">🌐 Portal URL:</td>
        <td style="padding: 8px 0;"><a href="{portal_url}" style="color: #6366f1;">{portal_url}</a></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #666;">📧 Email:</td>
        <td style="padding: 8px 0;"><strong>{user.email}</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #666;">🔑 Password:</td>
        <td style="padding: 8px 0;"><strong>{password}</strong></td>
      </tr>
    </table>
  </div>

  <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 15px; margin: 15px 0;">
    <p style="margin: 0; font-size: 14px;">
      ⚠️ <strong>Important:</strong> You will be asked to reset your password on first login. 
      Please choose a strong password and keep it secure.
    </p>
  </div>

  <div style="text-align: center; margin: 25px 0;">
    <a href="{portal_url}" style="background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-size: 16px; font-weight: bold;">
      Login to Portal
    </a>
  </div>

  <p style="line-height: 1.6;">
    If you face any issues logging in, please reach out to hr@accops.com.
  </p>

  <p>Warm regards,<br><strong>HR Team</strong><br>Accops Systems Pvt. Ltd.</p>

  <div style="border-top: 1px solid #eee; margin-top: 25px; padding-top: 15px; font-size: 12px; color: #999; text-align: center;">
    This is an automated email from the Accops HR Onboarding System.
  </div>
</body>
</html>
"""
        email_service.send_email(
            to_email=personal_email,
            subject=subject,
            html_content=html_content,
            cc_emails=cc_list if cc_list else None
        )
        log = EmailLog(
            user_id=user_id,
            email_type="Credentials",
            status=EmailStatus.sent,
            sent_at=datetime.now().isoformat()
        )
        db.add(log)
        db.commit()

    except Exception as e:
        db.rollback()
        countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=Exception("Credentials email failed, retrying..."), countdown=countdown)
    finally:
        db.close()
@celery_app.task(bind=True, max_retries=3)
def send_completion_email_to_hr(self, user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        settings = db.query(EmailSettings).first()
        cc_list = []
        if settings and settings.cc_emails:
            cc_list = [e.strip() for e in settings.cc_emails.split(',') if e.strip()]

        # Recipient: whoever onboarded this employee, falling back to all HR/admin
        recipients = []
        if user.onboarded_by:
            hr = db.query(User).filter(User.id == user.onboarded_by).first()
            if hr:
                recipients = [hr.personal_email or hr.email]
        if not recipients:
            hr_users = db.query(User).filter(User.role.in_([RoleEnum.hr, RoleEnum.admin])).all()
            recipients = [h.personal_email or h.email for h in hr_users]
        if not recipients:
            return

        # Build module breakdown
        content_map = {c.id: c.title for c in db.query(Content).all()}
        progresses = db.query(ModuleProgress).filter(
            ModuleProgress.user_id == user_id,
            ModuleProgress.completed == True
        ).all()

        rows_html = ""
        total_score = 0
        total_questions = 0
        for p in progresses:
            title = content_map.get(p.content_id, f"Module {p.content_id}")
            pct = int((p.score / p.total_questions) * 100) if p.total_questions else 0
            total_score += p.score
            total_questions += p.total_questions
            rows_html += f"""
            <tr>
              <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{title}</td>
              <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:center;">{p.score}/{p.total_questions}</td>
              <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:center;">{pct}%</td>
            </tr>
            """

        overall_pct = int((total_score / total_questions) * 100) if total_questions else 0
        rating = ("Excellent" if overall_pct >= 90 else
                  "Good" if overall_pct >= 75 else
                  "Needs Improvement" if overall_pct >= 50 else "Poor")

        subject = f"Onboarding Completed: {user.name}"
        html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #22c55e, #16a34a); padding: 24px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0;">Onboarding Completed 🎉</h1>
  </div>
  <p><strong>{user.name}</strong> ({user.email}) has completed the full onboarding process.</p>
  <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">
    <thead>
      <tr style="background: #f9fafb;">
        <th style="padding: 8px; text-align: left;">Module</th>
        <th style="padding: 8px;">Score</th>
        <th style="padding: 8px;">%</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  <p><strong>Overall Score:</strong> {total_score}/{total_questions} ({overall_pct}%)<br>
  <strong>Rating:</strong> {rating}</p>
  <p>Regards,<br><strong>Accops HR Onboarding System</strong></p>
</body>
</html>
"""
        email_service = EmailService()
        email_service.send_email(
            to_email=recipients,
            subject=subject,
            html_content=html_content,
            cc_emails=cc_list if cc_list else None
        )

        log = EmailLog(
            user_id=user_id,
            email_type="Completion Report",
            status=EmailStatus.sent,
            sent_at=datetime.now().isoformat()
        )
        db.add(log)
        db.commit()

    except Exception as e:
        db.rollback()
        countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=Exception("Completion email failed, retrying..."), countdown=countdown)
    finally:
        db.close()

# ─── Task: daily check ───────────────────────────────────────────────────────
@celery_app.task
def daily_onboarding_check():
    db = SessionLocal()
    try:
        today = datetime.now().date()
        t_minus_2_date = today + timedelta(days=2)

        # 1. T-2 emails ── employees joining in 2 days
        t2_users = db.query(User).filter(
            User.doj == str(t_minus_2_date),
            User.role.in_([RoleEnum.full_time, RoleEnum.intern, RoleEnum.consultant])
        ).all()
        for user in t2_users:
            already = db.query(EmailLog).filter(
                EmailLog.user_id == user.id,
                EmailLog.email_type == "T-2",
                EmailLog.status == EmailStatus.sent
            ).first()
            if not already:
                send_onboarding_email.delay(user.id, "T-2")

        # 2. Day-0 emails ── employees joining today
        day0_users = db.query(User).filter(
            User.doj == str(today),
            User.role.in_([RoleEnum.full_time, RoleEnum.intern, RoleEnum.consultant])
        ).all()
        for user in day0_users:
            already = db.query(EmailLog).filter(
                EmailLog.user_id == user.id,
                EmailLog.email_type == "Day 0",
                EmailLog.status == EmailStatus.sent
            ).first()
            if not already:
                temp_password = _generate_temp_password()
                user.hashed_password = auth.get_password_hash(temp_password)
                db.commit()
                send_onboarding_email.delay(user.id, "Day 0", {"password": temp_password})

        # 3. Daily Reminder + Escalation for incomplete employees
        all_content_count = db.query(Content).count()
        if all_content_count == 0:
            print("No content modules yet — skipping reminder/escalation checks")
            db.close()
            return

        # Get all HR users to notify on escalation
        hr_users = db.query(User).filter(
            User.role.in_([RoleEnum.hr, RoleEnum.admin])
        ).all()

        # Find employees (non-HR) who have joined but not completed
        employee_users = db.query(User).filter(
            User.role.in_([RoleEnum.full_time, RoleEnum.intern, RoleEnum.consultant]),
            User.is_active == True
        ).all()

        for emp in employee_users:
            completed_count = db.query(ModuleProgress).filter(
                ModuleProgress.user_id == emp.id,
                ModuleProgress.completed == True
            ).count()

            # Skip if fully done
            if completed_count >= all_content_count:
                continue

            # Find last activity time
            onboarding = db.query(OnboardingProgress).filter(
                OnboardingProgress.user_id == emp.id
            ).first()

            if not onboarding or not onboarding.last_activity_at:
                # Never logged any activity — use DOJ as reference
                if not emp.doj:
                    continue
                try:
                    last_activity = datetime.fromisoformat(emp.doj)
                except:
                    continue
            else:
                last_activity = datetime.fromisoformat(onboarding.last_activity_at)

            days_inactive = (datetime.now() - last_activity).days
            hours_inactive = (datetime.now() - last_activity).total_seconds() / 3600

            print(f"[Check] {emp.email}: {completed_count}/{all_content_count} done, {days_inactive}d inactive")

            # ── Escalation: inactive ≥ 3 days ──────────────────────────────
            if days_inactive >= 3:
                # Only escalate once per day (check last escalation sent today)
                today_escalation = db.query(EmailLog).filter(
                    EmailLog.user_id == emp.id,
                    EmailLog.email_type == "Escalation",
                    EmailLog.status == EmailStatus.sent,
                    EmailLog.sent_at >= str(today)
                ).first()

                if not today_escalation:
                    print(f"ESCALATION: {emp.email} inactive {days_inactive}d → notifying HR")
                    if onboarding and not onboarding.is_escalated:
                        onboarding.is_escalated = True
                        db.commit()

                    for hr in hr_users:
                        hr_email = hr.personal_email or hr.email
                        send_onboarding_email.delay(
                            emp.id, "Escalation",
                            {
                                "hr_name": hr.name,
                                "hr_email": hr_email,
                                "days_inactive": days_inactive,
                            }
                        )

            # ── Daily Reminder: joined but hasn't finished ──────────────────
            # Send daily reminder (once per day, after at least 24h since last activity)
            elif hours_inactive >= 24:
                today_reminder = db.query(EmailLog).filter(
                    EmailLog.user_id == emp.id,
                    EmailLog.email_type == "Reminder",
                    EmailLog.status == EmailStatus.sent,
                    EmailLog.sent_at >= str(today)
                ).first()

                if not today_reminder:
                    print(f"REMINDER: sending to {emp.email}")
                    send_onboarding_email.delay(emp.id, "Reminder")

        db.commit()
        print("daily_onboarding_check complete")
    finally:
        db.close()
