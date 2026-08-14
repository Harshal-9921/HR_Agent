from app.database import SessionLocal
from app.models import EmailTemplate
from datetime import datetime

TEMPLATES = [
    {
        "template_key": "welcome",
        "subject": "Welcome to Accops Systems! 🎉",
        "html_body": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
    <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Accops! 🚀</h1>
  </div>
  <p style="font-size: 16px;">Dear <strong>{name}</strong>,</p>
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
    Wishing you a great start and a successful journey with us.
    <strong>Congratulations once again on being a part of Accops!</strong>
  </p>
  <p style="font-size: 15px;">Warm regards,<br><strong>HR Team</strong><br>Accops Systems Pvt. Ltd.</p>
</body>
</html>
"""
    },
    {
        "template_key": "credentials",
        "subject": "Your Accops Onboarding Portal Credentials",
        "html_body": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
    <h1 style="color: white; margin: 0;">Your Login Credentials 🔐</h1>
  </div>
  <p>Dear <strong>{name}</strong>,</p>
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
        <td style="padding: 8px 0;"><strong>{email}</strong></td>
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
    </p>
  </div>
  <div style="text-align: center; margin: 25px 0;">
    <a href="{portal_url}" style="background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-size: 16px; font-weight: bold;">
      Login to Portal
    </a>
  </div>
  <p style="line-height: 1.6;">If you face any issues logging in, please reach out to hr@accops.com.</p>
  <p>Warm regards,<br><strong>HR Team</strong><br>Accops Systems Pvt. Ltd.</p>
</body>
</html>
"""
    },
    {
        "template_key": "completion",
        "subject": "Onboarding Completed: {name}",
        "html_body": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #22c55e, #16a34a); padding: 24px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0;">Onboarding Completed 🎉</h1>
  </div>
  <p><strong>{name}</strong> ({email}) has completed the full onboarding process.</p>
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
    },
    {
        "template_key": "alert",
        "subject": "Reminder: Complete Your Onboarding",
        "html_body": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <p>Hi <strong>{name}</strong>,</p>
  <p>This is a reminder to complete your onboarding. You have {remaining_count} module(s) remaining:</p>
  <ul>{remaining_modules}</ul>
  <div style="text-align: center; margin: 20px 0;">
    <a href="{portal_url}" style="background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">Continue Onboarding</a>
  </div>
  <p>Regards,<br><strong>HR Team</strong></p>
</body>
</html>
"""
    },
]


def seed():
    db = SessionLocal()
    try:
        for t in TEMPLATES:
            existing = db.query(EmailTemplate).filter(
                EmailTemplate.template_key == t["template_key"]
            ).first()
            if existing:
                print(f"Skipping '{t['template_key']}' — already exists")
                continue
            row = EmailTemplate(
                template_key=t["template_key"],
                subject=t["subject"],
                html_body=t["html_body"],
                updated_at=datetime.now().isoformat(),
                updated_by=None
            )
            db.add(row)
            print(f"Seeded '{t['template_key']}'")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()