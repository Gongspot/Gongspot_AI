# main.py

import asyncio
from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import time

from utils.database import get_db, engine, SessionLocal
from utils.recommender import Recommender
from utils.recommender_fast import RecommenderFast
from models.models import RecommendationRequest, RecommendationResponse, PlaceRecommendation

from models.db_models import (
    Base, UserDB, LikeDB, PlaceDB,
    place_type_table, place_purpose_table, place_mood_table, place_location_table
)

# 테이블 생성 (가장 먼저 실행)
# 모든 모델 클래스가 완전히 정의된 상태에서 테이블을 생성합니다.
Base.metadata.create_all(bind=engine)

# RecommenderFast 인스턴스를 저장할 전역 변수
recommender_instance = None

def get_recommender_fast_instance() -> RecommenderFast:
    """
    미리 생성된 RecommenderFast 인스턴스를 반환하는 종속성 주입 함수
    """
    return recommender_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션의 시작 및 종료 이벤트를 처리합니다.
    서버 시작 시 RecommenderFast 인스턴스를 미리 생성합니다.
    """
    global recommender_instance
    print("서버 시작 중: RecommenderFast 인스턴스 생성 및 데이터 로딩 시작...")

    # 서버 시작 시에만 단 한 번 실행
    db_session = SessionLocal()
    recommender_instance = RecommenderFast(db_session)
    db_session.close()
    print("데이터 로딩 완료. 서버가 요청을 처리할 준비가 되었습니다.")
    yield
    print("서버 종료 중...")

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="GongSpot Recommendation API", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "GongSpot Recommendation API is running!"}

@app.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
        request: RecommendationRequest,
        db: Session = Depends(get_db)
):
    """
    사용자 ID를 기반으로 장소 추천 목록을 반환하는 API 엔드포인트
    (전통적인, 매번 계산 방식)
    """
    print(f"[/recommendations] 요청 시작: user_id={request.user_id}")
    start_time = time.time()

    # 사용자 존재 여부 확인
    user_exists = db.query(UserDB.user_id).filter(UserDB.user_id == request.user_id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Recommender 클래스 인스턴스 생성
    recommender = Recommender(db)

    # 추천 장소 ID 가져오기
    recommended_place_ids = recommender.recommend_places(request.user_id)

    if not recommended_place_ids:
        end_time = time.time()
        print(f"[/recommendations] 요청 완료. 소요 시간: {end_time - start_time:.4f}초")
        return RecommendationResponse(recommended_places=[])

    # 실제 Place 정보 조회
    places = db.query(PlaceDB).filter(PlaceDB.place_id.in_(recommended_place_ids)).all()

    recommended_places = [
        PlaceRecommendation(place_id=place.place_id, name=place.name)
        for place in places
    ]

    end_time = time.time()
    print(f"[/recommendations] 요청 완료. 소요 시간: {end_time - start_time:.4f}초")

    return RecommendationResponse(recommended_places=recommended_places)


@app.post("/fast-recommendations", response_model=RecommendationResponse)
def get_fast_recommendations(
        request: RecommendationRequest,
        db: Session = Depends(get_db),
        recommender: RecommenderFast = Depends(get_recommender_fast_instance)
):
    """
    사전 로드된 RecommenderFast 객체를 사용하여 빠른 추천을 제공하는 API 엔드포인트
    """
    print(f"[/fast-recommendations] 요청 시작: user_id={request.user_id}")
    start_time = time.time()

    # 사용자 존재 여부 확인
    user_exists = db.query(UserDB.user_id).filter(UserDB.user_id == request.user_id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # 이제 RecommenderFast 객체를 새로 생성하지 않고 미리 로드된 객체를 사용합니다.
    # 추천 실행
    recommended_place_ids = recommender.recommend_places(request.user_id)

    if not recommended_place_ids:
        end_time = time.time()
        print(f"[/fast-recommendations] 요청 완료. 소요 시간: {end_time - start_time:.4f}초")
        return RecommendationResponse(recommended_places=[])

    # 실제 Place 정보 조회
    places = db.query(PlaceDB).filter(PlaceDB.place_id.in_(recommended_place_ids)).all()

    # Place 객체에서 필요한 정보 추출
    recommended_places = [
        PlaceRecommendation(place_id=place.place_id, name=place.name)
        for place in places
    ]

    end_time = time.time()
    print(f"[/fast-recommendations] 요청 완료. 소요 시간: {end_time - start_time:.4f}초")

    return RecommendationResponse(recommended_places=recommended_places)
