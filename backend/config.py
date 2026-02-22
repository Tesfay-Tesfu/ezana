import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database – will be overridden by DATABASE_URL env var on Render
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ezana.db'
    
    # Fix for PostgreSQL URL format and ensure SSL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Add SSL mode if not present and using PostgreSQL (critical for Render)
    if SQLALCHEMY_DATABASE_URI and 'postgresql' in SQLALCHEMY_DATABASE_URI:
        if 'sslmode' not in SQLALCHEMY_DATABASE_URI:
            # Add sslmode=require to the connection string
            separator = '&' if '?' in SQLALCHEMY_DATABASE_URI else '?'
            SQLALCHEMY_DATABASE_URI = f"{SQLALCHEMY_DATABASE_URI}{separator}sslmode=require"
            print(f"✅ Added sslmode=require to database URL")  # This will show in logs
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Stripe – use environment variables
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    if not STRIPE_PUBLIC_KEY or not STRIPE_SECRET_KEY:
        print("⚠️  Warning: Stripe keys not set in environment")
    
    # Gmail SMTP
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("⚠️  Warning: Mail credentials not set in environment")
    
    # Admin notification email
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    @classmethod
    def check_config(cls):
        """Helper method to verify critical config (optional)"""
        issues = []
        if not cls.SECRET_KEY:
            issues.append("SECRET_KEY is not set")
        if not cls.SQLALCHEMY_DATABASE_URI:
            issues.append("DATABASE_URL is not set")
        if issues:
            print("⚠️  Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration looks good")
        return len(issues) == 0

# Optional: Run check when config is imported
if __name__ != '__main__':
    Config.check_config()
