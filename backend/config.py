import os

class Config:
    # Mandatory: SECRET_KEY must be set in environment
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable not set")

    # Database – will use DATABASE_URL from environment (set by Render when you add PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        # Fallback to SQLite for local development (optional)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///ybBeauty.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Stripe – must be set in environment
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    if not STRIPE_PUBLIC_KEY or not STRIPE_SECRET_KEY:
        raise ValueError("Stripe keys must be set in environment")

    # Mail settings – required for sending emails
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise ValueError("Mail credentials must be set in environment")

    # Admin notification email
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or MAIL_USERNAME
