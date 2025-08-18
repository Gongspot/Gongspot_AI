# models.py

from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class LocationEnum(str, Enum):
    강남권 = '강남권'
    강북권 = '강북권'
    도심권 = '도심권'
    성동_광진권 = '성동_광진권'
    서남권 = '서남권'
    서북권 = '서북권'
    동남권 = '동남권'

class PlaceEnum(str, Enum):
    도서관 = '도서관'
    카페 = '카페'
    민간학습공간 = '민간학습공간'
    교내학습공간 = '교내학습공간'
    공공학습공간 = '공공학습공간'

class PurposeEnum(str, Enum):
    개인공부 = '개인공부'
    그룹공부 = '그룹공부'
    집중공부 = '집중공부'
    휴식 = '휴식'
    노트북작업 = '노트북작업'

# User 엔티티를 FastAPI에서 사용할 Pydantic 모델로 정의
class User(BaseModel):
    id: int
    email: str
    nickname: Optional[str] = None
    prefer_place: List[PlaceEnum] = []
    purpose: List[PurposeEnum] = []
    location: List[LocationEnum] = []

    class Config:
        # ORM 모델을 Pydantic 모델로 변환할 수 있도록 허용
        orm_mode = True

class PlaceRecommendation(BaseModel):
    place_id: int
    name: str

class RecommendationRequest(BaseModel):
    user_id: int

class RecommendationResponse(BaseModel):
    recommended_places: List[PlaceRecommendation]