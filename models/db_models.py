# db_models.py

from sqlalchemy import Column, BigInteger, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from models.enums import PlaceEnum, PurposeEnum, LocationEnum, MoodEnum
import enum

Base = declarative_base()

# ----------------------
# Enum 정의
# ----------------------
class RoleEnum(str, enum.Enum):
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"

# ----------------------
# User 관련
# ----------------------
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

    # 관계
    likes = relationship("LikeDB", back_populates="user", cascade="all, delete-orphan")
    prefer_places = relationship("UserPreferPlaceDB", back_populates="user", cascade="all, delete-orphan")
    purposes = relationship("UserPurposeDB", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("UserLocationDB", back_populates="user", cascade="all, delete-orphan")


# ----------------------
# Place 관련
# ----------------------
class PlaceDB(Base):
    __tablename__ = "places"

    place_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255))

    likes = relationship("LikeDB", back_populates="place", cascade="all, delete-orphan")
    purposes = relationship("PlacePurposeDB", back_populates="place", cascade="all, delete-orphan")
    moods = relationship("PlaceMoodDB", back_populates="place", cascade="all, delete-orphan")
    locations = relationship("PlaceLocationDB", back_populates="place", cascade="all, delete-orphan")
    types = relationship("PlaceTypeDB", back_populates="place", cascade="all, delete-orphan")

    reviews: Mapped[list["ReviewDB"]] = relationship(
        "ReviewDB", back_populates="place"
    )
# ----------------------
# Like 테이블
# ----------------------
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


# ----------------------
# User-M2M 관계
# ----------------------
class UserPreferPlaceDB(Base):
    __tablename__ = "user_prefer_place"

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    value = Column(Enum(PlaceEnum), primary_key=True)

    user = relationship("UserDB", back_populates="prefer_places")


class UserPurposeDB(Base):
    __tablename__ = "user_purpose"

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    value = Column(Enum(PurposeEnum), primary_key=True)

    user = relationship("UserDB", back_populates="purposes")


class UserLocationDB(Base):
    __tablename__ = "user_location"

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    value = Column(Enum(LocationEnum), primary_key=True)

    user = relationship("UserDB", back_populates="locations")


# ----------------------
# Place-M2M 관계
# ----------------------
class PlacePurposeDB(Base):
    __tablename__ = "place_purpose"

    place_id = Column(BigInteger, ForeignKey("places.place_id"), primary_key=True)
    value = Column(Enum(PurposeEnum), primary_key=True)

    place = relationship("PlaceDB", back_populates="purposes")


class PlaceMoodDB(Base):
    __tablename__ = "place_mood"

    place_id = Column(BigInteger, ForeignKey("places.place_id"), primary_key=True)
    value = Column(Enum(MoodEnum), primary_key=True)

    place = relationship("PlaceDB", back_populates="moods")


class PlaceLocationDB(Base):
    __tablename__ = "place_location"

    place_id = Column(BigInteger, ForeignKey("places.place_id"), primary_key=True)
    value = Column(Enum(LocationEnum), primary_key=True)

    place = relationship("PlaceDB", back_populates="locations")


class PlaceTypeDB(Base):
    __tablename__ = "place_type"

    place_id = Column(BigInteger, ForeignKey("places.place_id"), primary_key=True)
    value = Column(Enum(PlaceEnum), primary_key=True)

    place = relationship("PlaceDB", back_populates="types")

# ----------------------
# 리뷰 테이블 모델 정의
# ----------------------

class ReviewDB(Base):
    __tablename__ = "reviews"

    review_id = Column(BigInteger, primary_key=True, autoincrement=True)
    rating = Column(Integer)
    created_at = Column(DateTime, nullable=False)
    datetime = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    place_id = Column(BigInteger, ForeignKey("places.place_id", ondelete="cascade"), nullable=False)
    updated_at = Column(DateTime, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    content = Column(String(500), nullable=True)
    congestion = Column(Enum('높음', '보통', '낮음'), nullable=True)

    place: Mapped["PlaceDB"] = relationship(
        "PlaceDB", back_populates="reviews"
    )