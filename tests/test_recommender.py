import pytest
from unittest.mock import MagicMock
from collections import Counter
import numpy as np

# 테스트 대상 모듈 임포트
from utils.recommender_fast import RecommenderFast
from models.db_models import UserDB, PlaceDB, LikeDB
from models.models import PlaceRecommendation
from models.enums import PurposeEnum, MoodEnum, PlaceEnum, LocationEnum

# Mock 데이터베이스 세션 및 데이터
@pytest.fixture
def mock_db_session():
    mock_session = MagicMock()
    return mock_session

@pytest.fixture
def mock_data(mock_db_session):
    # Enum 객체를 흉내내는 Mock 객체를 생성
    mock_purpose_1 = MagicMock(PurposeEnum, value="개인공부")
    mock_purpose_2 = MagicMock(PurposeEnum, value="토론")
    mock_mood_1 = MagicMock(MoodEnum, value="조용한")
    mock_mood_2 = MagicMock(MoodEnum, value="넓은")

    mock_users = [
        MagicMock(UserDB, user_id=1, prefer_places=[], purposes=[mock_purpose_1], locations=[]),
        MagicMock(UserDB, user_id=2, prefer_places=[], purposes=[mock_purpose_1], locations=[]),
        MagicMock(UserDB, user_id=3, prefer_places=[], purposes=[mock_purpose_2], locations=[]),
    ]

    mock_places = [
        MagicMock(PlaceDB, place_id=1, name="Place A", purposes=[mock_purpose_1], moods=[mock_mood_1]),
        MagicMock(PlaceDB, place_id=2, name="Place B", purposes=[mock_purpose_1], moods=[mock_mood_2]),
        MagicMock(PlaceDB, place_id=3, name="Place C", purposes=[mock_purpose_2], moods=[mock_mood_2]),
        MagicMock(PlaceDB, place_id=4, name="Place D", purposes=[mock_purpose_2], moods=[mock_mood_1]),
    ]

    mock_likes = [
        MagicMock(LikeDB, user_id=1, place_id=1),
        MagicMock(LikeDB, user_id=2, place_id=2),
        MagicMock(LikeDB, user_id=3, place_id=4),
    ]

    mock_db_session.query.return_value.all.side_effect = [mock_users, mock_places, mock_likes]

    return {
        "users": mock_users,
        "places": {p.place_id: p for p in mock_places},
        "likes": mock_likes
    }

# --- 테스트 함수 시작 ---

def test_load_data(mock_db_session, mock_data):
    recommender = RecommenderFast(mock_db_session)

    # 데이터가 올바르게 로드되었는지 검증
    assert len(recommender.user_profiles) == 3
    assert recommender.user_likes[1] == {1} # `mock_likes` 데이터에 맞게 수정
    assert recommender.user_profiles[1]['개인공부'] == 2 # 좋아요한 장소 특징 반영 확인

def test_create_feature_matrix(mock_db_session):
    # GIVEN
    recommender = RecommenderFast(mock_db_session)

    # 피처 매트릭스가 올바르게 생성되었는지 검증
    assert recommender.feature_matrix.shape[0] == 3 # (사용자 수)
    assert recommender.feature_matrix.shape[1] > 0 # (특징 수)

def test_calculate_similarity(mock_db_session):
    # GIVEN
    recommender = RecommenderFast(mock_db_session)

    # 유사도 행렬이 올바르게 계산되었는지 검증
    assert recommender.similarity_matrix.shape == (3, 3)
    assert np.allclose(recommender.similarity_matrix, recommender.similarity_matrix.T) # 대칭성 확인
    assert np.allclose(np.diag(recommender.similarity_matrix), [1.0, 1.0, 1.0]) # 자기 자신과의 유사도 = 1

def test_get_similar_users(mock_db_session):
    recommender = RecommenderFast(mock_db_session)

    similar_users = recommender.get_similar_users(target_user_id=1, n_users=2)

    # user 1과 가장 유사한 user 2를 찾아야 함
    # mock 데이터에서 user 1과 2는 '개인공부'
    assert 2 in similar_users
    assert len(similar_users) == 2

def test_recommend_places(mock_db_session, mock_data):
    recommender = RecommenderFast(mock_db_session)

    # user 1은 user 2와 유사하므로, user 2가 좋아한 장소(id:2)가 추천되어야 함.
    # user 1은 Place 1을 좋아함. user 2는 Place 2를 좋아함.
    # 추천 로직은 이미 좋아한 장소(Place 1)를 제거하고, 유사 사용자가 좋아한 장소(Place 2)를 추천.
    recommended_places = recommender.recommend_places(target_user_id=1, n_recommendations=1)

    assert len(recommended_places) > 0
    assert recommended_places[0].place_id == 2