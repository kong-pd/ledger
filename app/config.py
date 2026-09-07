"""App configuration. In production, read SECRET_KEY from env vars."""

SECRET_KEY = "dev-secret-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
