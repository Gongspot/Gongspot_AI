# db_models.py

from sqlalchemy import Column, BigInteger, String, DateTime, Enum, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship, declarative_base
from models.enums import PlaceEnum, PurposeEnum, LocationEnum, MoodEnum
import enum

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"

# 모든 Table 객체들을 먼저 정의합니다.
user_prefer_place_table = Table(
    "user_prefer_place", Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id"), primary_key=True),
    Column("value", Enum(PlaceEnum), primary_key=True)
)

user_purpose_table = Table(
    "user_purpose", Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id"), primary_key=True),
    Column("value", Enum(PurposeEnum), primary_key=True)
)

user_location_table = Table(
    "user_location", Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id"), primary_key=True),
    Column("value", Enum(LocationEnum), primary_key=True)
)

place_purpose_table = Table(
    "place_purpose", Base.metadata,
    Column("place_id", BigInteger, ForeignKey("places.place_id"), primary_key=True),
    Column("value", Enum(PurposeEnum), primary_key=True)
)

place_mood_table = Table(
    "place_mood", Base.metadata,
    Column("place_id", BigInteger, ForeignKey("places.place_id"), primary_key=True),
    Column("value", Enum(MoodEnum), primary_key=True)
)

place_location_table = Table(
    "place_location", Base.metadata,
    Column("place_id", BigInteger, ForeignKey("places.place_id"), primary_key=True),
    Column("value", Enum(LocationEnum), primary_key=True)
)

place_type_table = Table(
    "place_type", Base.metadata,
    Column("place_id", BigInteger, ForeignKey("places.place_id"), primary_key=True),
    Column("value", Enum(PlaceEnum), primary_key=True)
)

class UserDB(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    nickname = Column(String(50), unique=True, nullable=True)
    email = Column(String(30), nullable=False)
    profile_img = Column(String(1000), nullable=True)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    likes = relationship("LikeDB", viewonly=True, back_populates="user")

class LikeDB(Base):
    __tablename__ = "likes"

    likes_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    place_id = Column(BigInteger, ForeignKey("places.place_id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("UserDB", back_populates="likes")
    place = relationship("PlaceDB", back_populates="likes")

class PlaceDB(Base):
    __tablename__ = "places"

    place_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255))
    likes = relationship("LikeDB", back_populates="place")