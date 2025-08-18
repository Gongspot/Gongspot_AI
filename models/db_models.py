# db_models.py

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey

# ORM 모델의 기본 클래스
Base = declarative_base()

# 데이터베이스의 Users 테이블에 매핑되는 ORM 모델
class UserDB(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(30), nullable=False)
    nickname = Column(String(50))
    profileImg = Column(String(1000))
    prefer_place = Column(String(255))
    purpose = Column(String(255))
    location = Column(String(255))

# 사용자의 장소 좋아요 기록을 위한 ORM 모델
class UserLike(Base):
    __tablename__ = "UserLike"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    place_id = Column(Integer)