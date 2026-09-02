"""
应用配置
--------
SECRET_KEY 用来签发和验证 JWT。
生产环境应该从环境变量读，这里先硬编码方便开发。
"""

SECRET_KEY = "dev-secret-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
