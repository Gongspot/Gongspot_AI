# database.py

import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 데이터베이스 세션 관리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 모델 기본 클래스
Base = declarative_base()

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()