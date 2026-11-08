"""Production-safe initialization: never creates demo Staff or Resident users."""
import hashlib
import hmac
import os
from sqlalchemy import func

from app import app, email_valid, password_valid
from models import ActivityLog, db, EventCategory, PermitType, SystemSetting, User
from migration import upgrade_legacy_schema


RESET_TOKEN_SETTING = "admin_credential_reset_token_sha256"


def reset_existing_admin(admin):
    """Apply a Render-authorized, one-time credential reset to the current admin."""
    reset_token = os.environ.get("ADMIN_CREDENTIAL_RESET_TOKEN", "").strip()
    if not reset_token:
        return False
    if len(reset_token) < 32:
        print("Administrator credential reset skipped: reset token must be at least 32 characters.")
        return False

    token_hash = hashlib.sha256(reset_token.encode("utf-8")).hexdigest()
    marker = SystemSetting.query.filter_by(key=RESET_TOKEN_SETTING).first()
    if marker and hmac.compare_digest(marker.value or "", token_hash):
        print("One-time administrator credential reset already applied; credentials preserved.")
        return False

    username = (os.environ.get("INITIAL_ADMIN_USERNAME") or "").strip()
    email = (os.environ.get("INITIAL_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("INITIAL_ADMIN_PASSWORD") or ""
    full_name = (os.environ.get("INITIAL_ADMIN_NAME") or admin.full_name or "System Administrator").strip()
    if (
        not username
        or len(username) > 80
        or not email_valid(email)
        or len(email) > 150
        or not password_valid(password)
        or not full_name
        or len(full_name) > 150
    ):
        print("Administrator credential reset skipped: check the Render username, email, name, and password values.")
        return False

    username_conflict = User.query.filter(
        User.id != admin.id, User.username == username
    ).first()
    email_conflict = User.query.filter(
        User.id != admin.id, func.lower(User.email) == email
    ).first()
    if username_conflict or email_conflict:
        print("Administrator credential reset skipped: the requested username or email is already in use.")
        return False

    admin.username = username
    admin.email = email
    admin.full_name = full_name
    admin.is_active = True
    admin.set_password(password)

    if marker is None:
        marker = SystemSetting(key=RESET_TOKEN_SETTING)
        db.session.add(marker)
    marker.value = token_hash
    db.session.add(
        ActivityLog(
            user_id=admin.id,
            actor_role="system",
            action="ADMIN_BOOTSTRAP_CREDENTIALS_RESET",
            resource="user",
            target_reference=str(admin.id),
            details="Administrator credentials reset through one-time Render bootstrap authorization.",
        )
    )
    db.session.commit()
    print("Administrator credentials reset once using authorized Render settings.")
    return True


def initialize():
    with app.app_context():
        upgrade_legacy_schema()
        admin=User.query.filter_by(role="admin").order_by(User.id).first()
        if admin:
            if not reset_existing_admin(admin):
                print(f"Permanent administrator preserved (ID {admin.id}).")
        else:
            username=os.environ.get("INITIAL_ADMIN_USERNAME"); email=os.environ.get("INITIAL_ADMIN_EMAIL"); password=os.environ.get("INITIAL_ADMIN_PASSWORD")
            if not all((username,email,password)): raise RuntimeError("No administrator exists. Set INITIAL_ADMIN_USERNAME, INITIAL_ADMIN_EMAIL, and INITIAL_ADMIN_PASSWORD.")
            admin=User(username=username,email=email.lower(),full_name=os.environ.get("INITIAL_ADMIN_NAME","System Administrator"),role="admin"); admin.set_password(password); db.session.add(admin)
        for name in ("Barangay Clearance","Business Clearance","Certificate of Residency"):
            if not PermitType.query.filter_by(name=name).first(): db.session.add(PermitType(name=name))
        for name in ("Community Event","Sports Activity","Public Assembly"):
            if not EventCategory.query.filter_by(name=name).first(): db.session.add(EventCategory(name=name))
        db.session.commit(); print("Catalogs initialized. No demo Staff or Resident accounts were created.")

if __name__=="__main__": initialize()
