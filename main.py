# main.py

from models.db_models import Base, UserDB, UserLike

from utils.database import get_db, engine
from utils.recommender import Recommender
from models.models import RecommendationRequest, RecommendationResponse, PlaceRecommendation

# 테이블 생성 (최초 1회만 실행)
Base.metadata.create_all(bind=engine)

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="GongSpot Recommendation API")

@app.get("/")
def read_root():
    return {"message": "GongSpot Recommendation API is running!"}

@app.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(request: RecommendationRequest, db: Session = Depends(get_db)):
    """
    사용자 ID를 기반으로 장소 추천 목록을 반환하는 API 엔드포인트
    """
    # 1. 사용자 존재 여부 확인
    user_exists = db.query(UserDB.user_id).filter(UserDB.user_id == request.user_id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # 2. Recommender 클래스 인스턴스 생성
    # Recommender는 초기화 시 데이터베이스에서 데이터를 로드합니다.
    recommender = Recommender(db)

    # 3. 추천 로직 실행
    recommended_place_ids = recommender.recommend_places(request.user_id)

    # 4. 추천된 장소 ID를 기반으로 장소 정보 조회 (추후 구현)
    # 현재는 Place 정보가 없으므로 더미 데이터를 반환합니다.
    # TODO: Place 테이블과 연결하여 실제 장소 정보를 가져오는 로직 추가
    recommended_places = [
        PlaceRecommendation(place_id=place_id, name=f"장소_{place_id}")
        for place_id in recommended_place_ids
    ]

    return RecommendationResponse(recommended_places=recommended_places)