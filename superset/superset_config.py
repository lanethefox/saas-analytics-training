import os
from celery.schedules import crontab

# Superset specific config
ROW_LIMIT = 5000
SECRET_KEY = os.environ.get('SECRET_KEY', 'superset_secret_key_2024_change_in_production')

# JWT secret for async queries (must be at least 32 bytes)
GLOBAL_ASYNC_QUERIES_JWT_SECRET = os.environ.get('GLOBAL_ASYNC_QUERIES_JWT_SECRET', 'superset_jwt_secret_key_2024_for_async_queries_change_in_production')

# Flask App Builder configuration
# Your App secret key will be used for securely signing the session cookie
# and encrypting sensitive information on the database
# Make sure you are changing this key for your deployment with a strong key.
# You can generate a strong key using `openssl rand -base64 42`

# The SQLAlchemy connection string to your database backend
# This connection defines the path to the database that stores your
# superset metadata (slices, connections, tables, dashboards, ...).
# Note that the connection information to connect to the datasources
# you want to explore are managed directly in the web UI
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{os.environ.get('DATABASE_USER', 'superset_user')}:"
    f"{os.environ.get('DATABASE_PASSWORD', 'superset_secure_password_2024')}@"
    f"{os.environ.get('DATABASE_HOST', 'postgres')}:"
    f"{os.environ.get('DATABASE_PORT', '5432')}/"
    f"{os.environ.get('DATABASE_DB', 'superset_db')}"
)

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
# Add endpoints that need to be exempt from CSRF protection
WTF_CSRF_EXEMPT_LIST = []
# A CSRF token that expires in 1 year
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = ''

# Redis configuration for caching
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', 'redis'),
    'CACHE_REDIS_PORT': os.environ.get('REDIS_PORT', 6379),
    'CACHE_REDIS_DB': os.environ.get('REDIS_DB', 1),
}

# Configure Celery for async queries
class CeleryConfig:
    broker_url = f"redis://{os.environ.get('REDIS_HOST', 'redis')}:{os.environ.get('REDIS_PORT', 6379)}/2"
    imports = (
        'superset.sql_lab',
        'superset.tasks',
    )
    result_backend = f"redis://{os.environ.get('REDIS_HOST', 'redis')}:{os.environ.get('REDIS_PORT', 6379)}/3"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
    }
    beat_schedule = {
        'reports.scheduler': {
            'task': 'reports.scheduler',
            'schedule': crontab(minute='*', hour='*'),
        },
        'reports.prune_log': {
            'task': 'reports.prune_log',
            'schedule': crontab(minute=0, hour=0),
        },
    }

CELERY_CONFIG = CeleryConfig

# Feature flags
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_VIRTUALIZATION": True,
    "GLOBAL_ASYNC_QUERIES": False,  # Disabled for now
}

# Thumbnail configuration
THUMBNAIL_SELENIUM_USER = "admin"
THUMBNAIL_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 24 * 60 * 60,  # 1 day
    'CACHE_KEY_PREFIX': 'superset_thumbnail_',
    'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', 'redis'),
    'CACHE_REDIS_PORT': os.environ.get('REDIS_PORT', 6379),
    'CACHE_REDIS_DB': os.environ.get('REDIS_DB', 1),
}

# Filter results cache
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 24 * 60 * 60,  # 1 day
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', 'redis'),
    'CACHE_REDIS_PORT': os.environ.get('REDIS_PORT', 6379),
    'CACHE_REDIS_DB': os.environ.get('REDIS_DB', 1),
}

# SQL Lab configuration
SQL_MAX_ROW = 100000
SQLLAB_ASYNC_TIME_LIMIT_SEC = 60 * 60 * 6  # 6 hours
SQLLAB_TIMEOUT = 300  # 5 minutes
SUPERSET_WEBSERVER_TIMEOUT = 60

# Security configurations
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Email configuration (optional)
# SMTP_HOST = "smtp.gmail.com"
# SMTP_STARTTLS = True
# SMTP_SSL = False
# SMTP_USER = "your_email@gmail.com"
# SMTP_PORT = 587
# SMTP_PASSWORD = "your_password"
# SMTP_MAIL_FROM = "your_email@gmail.com"

# WebDriver configuration for screenshots
# WEBDRIVER_TYPE = "chrome"
# WEBDRIVER_OPTION_ARGS = [
#     "--headless",
#     "--no-sandbox",
#     "--disable-dev-shm-usage",
#     "--disable-gpu",
# ]

# Logging configuration
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = 'INFO'

# Enable proxy fix for deployments behind a reverse proxy
ENABLE_PROXY_FIX = False

# Disable sample data
SUPERSET_LOAD_EXAMPLES = False