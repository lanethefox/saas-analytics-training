import os
from celery.schedules import crontab

# Superset specific config
ROW_LIMIT = 5000
SECRET_KEY = os.environ.get('SECRET_KEY', 'superset_secret_key_2024_change_in_production')

# JWT secret for async queries (must be at least 32 bytes)
GLOBAL_ASYNC_QUERIES_JWT_SECRET = os.environ.get('GLOBAL_ASYNC_QUERIES_JWT_SECRET', 'superset_jwt_secret_key_2024_for_async_queries_change_in_production')

# The SQLAlchemy connection string to your database backend
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{os.environ.get('DATABASE_USER', 'superset_user')}:"
    f"{os.environ.get('DATABASE_PASSWORD', 'superset_secure_password_2024')}@"
    f"{os.environ.get('DATABASE_HOST', 'postgres')}:"
    f"{os.environ.get('DATABASE_PORT', '5432')}/"
    f"{os.environ.get('DATABASE_DB', 'superset_db')}"
)

# DISABLE AUTHENTICATION FOR LOCAL DEVELOPMENT
AUTH_TYPE = 1  # AUTH_DB
AUTH_ROLE_ADMIN = 'Admin'
AUTH_ROLE_PUBLIC = 'Public'
PUBLIC_ROLE_LIKE_GAMMA = True

# Auto-assign public role to all users
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Admin"

# Flask-WTF flag for CSRF - DISABLED for easier development
WTF_CSRF_ENABLED = False
WTF_CSRF_EXEMPT_LIST = ['*']

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

# Security configurations - RELAXED for local development
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = 'Lax'

# SQL Lab configuration
SQL_MAX_ROW = 100000
SQLLAB_ASYNC_TIME_LIMIT_SEC = 60 * 60 * 6  # 6 hours
SQLLAB_TIMEOUT = 300  # 5 minutes
SUPERSET_WEBSERVER_TIMEOUT = 60

# Logging configuration
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = 'INFO'

# Enable proxy fix for deployments behind a reverse proxy
ENABLE_PROXY_FIX = False

# Disable sample data
SUPERSET_LOAD_EXAMPLES = False

# Allow embedding (useful for development)
TALISMAN_ENABLED = False
