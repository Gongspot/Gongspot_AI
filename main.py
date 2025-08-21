# main.py

import time
from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from utils.database import get_db, engine, SessionLocal
from utils.recommender_fast import RecommenderFast
from models.models import RecommendationRequest, RecommendationResponse, PlaceRecommendation
from models.db_models import Base, UserDB, PlaceDB, ReviewDB

# 테이블 생성
Base.metadata.create_all(bind=engine)

# RecommenderFast 인스턴스 전역 저장
recommender_instance: RecommenderFast = None

def get_recommender_fast_instance() -> RecommenderFast:
    """
    미리 생성된 RecommenderFast 인스턴스 반환
    """
    return recommender_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작 시 RecommenderFast 인스턴스를 초기화
    """
    global recommender_instance
    print("서버 시작 중: RecommenderFast 인스턴스 생성 및 데이터 로딩 시작...")
    db_session = SessionLocal()
    recommender_instance = RecommenderFast(db_session)
    db_session.close()
    print("데이터 로딩 완료. 서버가 요청을 처리할 준비가 되었습니다.")
    yield
    print("서버 종료 중...")

# FastAPI 앱 생성
app = FastAPI(title="GongSpot Recommendation API", lifespan=lifespan)

origins = [
    "http://localhost:5182",
    "https://gong-spot.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "GongSpot Recommendation API is running!"}

@app.post("/fast-recommendations", response_model=RecommendationResponse)
def get_fast_recommendations(
        request: RecommendationRequest,
        db: Session = Depends(get_db),
        recommender: RecommenderFast = Depends(get_recommender_fast_instance)
):
    print(f"[/fast-recommendations] 요청 시작: user_id={request.user_id}")
    start_time = time.time()

    # 사용자 존재 여부 확인
    user_exists = db.query(UserDB.user_id).filter(UserDB.user_id == request.user_id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # 추천 실행 (recommender가 기본 정보를 포함한 리스트를 반환)
    recommended_places_with_details: list[PlaceRecommendation] = recommender.recommend_places(request.user_id)

    # 추천된 장소들의 ID만 추출
    recommended_place_ids = [p.place_id for p in recommended_places_with_details]

    # 별점 평균 쿼리
    avg_ratings_query = db.query(
        ReviewDB.place_id,
        func.avg(ReviewDB.rating).label('average_rating')
    ).filter(
        ReviewDB.place_id.in_(recommended_place_ids)
    ).group_by(
        ReviewDB.place_id
    ).all()

    # 딕셔너리로 변환
    avg_ratings_dict = {
        place_id: float(round(avg_rating, 2)) if avg_rating is not None else None
        for place_id, avg_rating in avg_ratings_query
    }

    # 기존 추천 목록에 별점 평균 추가
    final_recommended_places = []
    for place_rec in recommended_places_with_details:
        # Pydantic 객체의 필드에 별점 평균 값 할당
        place_rec.average_rating = avg_ratings_dict.get(place_rec.place_id)
        final_recommended_places.append(place_rec)

    end_time = time.time()
    print(f"[/fast-recommendations] 요청 완료. 추천 수: {len(final_recommended_places)}, 소요 시간: {end_time - start_time:.4f}초")

    return RecommendationResponse(recommended_places=final_recommended_places)