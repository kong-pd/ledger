"""
数据库连接配置
--------------
目前用 SQLite 做开发，后面换 PostgreSQL 只需要改 DATABASE_URL 这一行。

关键概念：
  - Engine:    SQLAlchemy 与数据库之间的 "通道"
  - Session:   一次会话（一组操作），用完要关
  - Base:      所有 ORM 模型的父类，通过它做 create_all / migrate
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite 文件放在项目根目录
DATABASE_URL = "sqlite:///./ledger.db"

# check_same_thread 是 SQLite 特有的，PostgreSQL 不需要
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有模型都继承这个类"""
    pass


def get_db():
    """
    FastAPI 依赖注入：每个请求拿一个 Session，用完自动关闭。
    用法：  db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
