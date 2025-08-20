# models.py

from typing import List, Optional
from pydantic import BaseModel
from models.enums import PlaceEnum, PurposeEnum, LocationEnum, MoodEnum

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
    type: Optional[PlaceEnum] = None
    purpose: Optional[List[PurposeEnum]] = []
    mood: Optional[List[MoodEnum]] = []
    location: Optional[List[LocationEnum]] = []

class RecommendationRequest(BaseModel):
    user_id: int

class RecommendationResponse(BaseModel):
    recommended_places: List[PlaceRecommendation]