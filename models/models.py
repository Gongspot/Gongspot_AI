# models.py

from typing import List, Optional
from pydantic import BaseModel
from models.enums import PlaceEnum, PurposeEnum, LocationEnum, MoodEnum
from pydantic.v1 import validator


class User(BaseModel):
    id: int
    email: str
    nickname: Optional[str] = None
    prefer_place: List[PlaceEnum] = []
    purpose: List[PurposeEnum] = []
    location: List[LocationEnum] = []
    likes: List[int] = []  # 유저가 좋아요 누른 place_id 리스트

    class Config:
        from_attributes = True

class PlaceRecommendation(BaseModel):
    place_id: int
    name: str
    address: Optional[str] = None
    is_free: Optional[bool] = None
    type: Optional[PlaceEnum] = None
    purpose: Optional[List[PurposeEnum]] = []
    mood: Optional[List[MoodEnum]] = []
    location: Optional[List[LocationEnum]] = []
    average_rating: Optional[float] = None
    photo_url: Optional[str] = None

    @validator('average_rating', pre=True)
    def convert_rating_to_float(cls, v):
        if v is None:
            return None

        return float(v)

class RecommendationRequest(BaseModel):
    user_id: int

class RecommendationResponse(BaseModel):
    recommended_places: List[PlaceRecommendation]