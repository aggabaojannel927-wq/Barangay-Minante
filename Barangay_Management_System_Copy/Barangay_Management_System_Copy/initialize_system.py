"""Initialize this transferred copy with a new, locally chosen administrator."""
import getpass
import os
from pathlib import Path
import secrets
import sys


def main():
    application_dir = Path(__file__).resolve().parent / 'barangay_system'
    sys.path.insert(0, str(application_dir))
    from dotenv import dotenv_values
    env_path = application_dir / '.env'
    settings = dotenv_values(env_path) if env_path.exists() else {}
    secret = settings.get('SECRET_KEY')
    if not secret:
        secret = secrets.token_urlsafe(48)
        with env_path.open('a', encoding='utf-8') as output:
            output.write('\nSECRET_KEY=' + secret + '\nDATA_DIR=instance\nSQLITE_DB_PATH=instance/minante.db\nSESSION_COOKIE_SECURE=0\nFLASK_DEBUG=0\nSMS_PROVIDER=simulated\n')
        try:
            env_path.chmod(0o600)
        except OSError:
            pass
    if secret == 'development-only-change-me' or len(secret) < 32:
        raise RuntimeError('Choose a unique SECRET_KEY of at least 32 characters in barangay_system/.env.')
    # Initialize this copy only, even if the computer has unrelated DB settings.
    os.environ['SECRET_KEY'] = secret
    os.environ.pop('DATABASE_URL', None)
    os.environ['DATA_DIR'] = str(application_dir / 'instance')
    os.environ['SQLITE_DB_PATH'] = str(application_dir / 'instance' / 'minante.db')
    from app import app, email_valid, password_valid
    from migration import upgrade_legacy_schema
    from models import User
    from seed import initialize
    with app.app_context():
        upgrade_legacy_schema()
        existing = User.query.filter_by(role='admin').first()
    if not existing:
        username = os.environ.get('INITIAL_ADMIN_USERNAME') or input('New administrator username: ').strip()
        email = os.environ.get('INITIAL_ADMIN_EMAIL') or input('Administrator email: ').strip()
        password = os.environ.get('INITIAL_ADMIN_PASSWORD')
        if not password:
            password = getpass.getpass('New password (10+ characters, letters and numbers): ')
            if password != getpass.getpass('Confirm password: '):
                raise ValueError('Passwords do not match.')
        if not username or len(username) > 80 or not email_valid(email) or not password_valid(password):
            raise ValueError('Provide a username, valid email, and password with 10+ characters including letters and numbers.')
        os.environ['INITIAL_ADMIN_USERNAME'] = username
        os.environ['INITIAL_ADMIN_EMAIL'] = email
        os.environ['INITIAL_ADMIN_PASSWORD'] = password
    try:
        initialize()
    finally:
        os.environ.pop('INITIAL_ADMIN_PASSWORD', None)
    print('Setup complete. Start the system using run.ps1 or the README commands.')
    print('Keep the generated .env private. Configure accepted IDs, venues, and service rules as Administrator.')


if __name__ == '__main__':
    main()
