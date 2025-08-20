import pytest
from unittest.mock import MagicMock
from collections import Counter
import numpy as np

from utils.recommender_fast import RecommenderFast
from models.db_models import UserDB, PlaceDB, LikeDB
from models.models import PlaceRecommendation

# Mock 데이터베이스 세션 및 데이터
@pytest.fixture
def mock_db_session():
    # SQLAlchemy 세션을 흉내내는 MagicMock 객체 생성
    mock_session = MagicMock()
    return mock_session

@pytest.fixture
def mock_data(mock_db_session):
    mock_users = [
        MagicMock(UserDB, user_id=1, prefer_places=[], purposes=[], locations=[], likes=[]),
        MagicMock(UserDB, user_id=2, prefer_places=[], purposes=[], locations=[], likes=[]),
        MagicMock(UserDB, user_id=3, prefer_places=[], purposes=[], locations=[], likes=[]),
    ]

    mock_places = [
        MagicMock(PlaceDB, place_id=1, name="Place A", purposes=["개인공부"], moods=["조용한"]),
        MagicMock(PlaceDB, place_id=2, name="Place B", purposes=["개인공부"], moods=["넓은"]),
        MagicMock(PlaceDB, place_id=3, name="Place C", purposes=["토론"], moods=["넓은"]),
    ]

    mock_likes = [
        MagicMock(LikeDB, user_id=1, place_id=1),
        MagicMock(LikeDB, user_id=1, place_id=2),
        MagicMock(LikeDB, user_id=2, place_id=1),
        MagicMock(LikeDB, user_id=3, place_id=3),
    ]

    mock_db_session.query.return_value.all.side_effect = [mock_users, mock_places, mock_likes]

    return {
        "users": mock_users,
        "places": {p.place_id: p for p in mock_places},
        "likes": mock_likes
    }

# 테스트 함수 시작

def test_load_data(mock_db_session, mock_data):
    recommender = RecommenderFast(mock_db_session)

    # 데이터가 올바르게 로드되었는지 검증
    assert len(recommender.user_profiles) == 3
    assert recommender.user_likes[1] == {1, 2}
    assert recommender.user_profiles[1]['개인공부'] == 2
    # 좋아요한 장소 특징 반영 확인

def test_create_feature_matrix(mock_db_session):
    recommender = RecommenderFast(mock_db_session)

    # 피처 매트릭스가 올바르게 생성되었는지 검증
    assert recommender.feature_matrix.shape == (3, 3) # (사용자 수, 특징 수)

    # 사용자의 특징 벡터 내용 검증 (순서에 따라 달라질 수 있음)
    # user 1의 프로필은 '개인공부':2, '조용한':1, '넓은':1 (총 3개 특징)
    # 매트릭스는 이 특징들의 순서에 따라 [2, 1, 1] 또는 다른 순서가 될 수 있음
    assert sum(recommender.feature_matrix[0]) == 4  # (개인공부: 2, 조용한:1, 넓은:1)

def test_calculate_similarity(mock_db_session):
    recommender = RecommenderFast(mock_db_session)

    # 유사도 행렬이 올바르게 계산되었는지 검증
    assert recommender.similarity_matrix.shape == (3, 3)
    assert np.allclose(recommender.similarity_matrix, recommender.similarity_matrix.T) # 대칭성 확인
    assert np.allclose(np.diag(recommender.similarity_matrix), [1.0, 1.0, 1.0]) # 자기 자신과의 유사도 = 1

def test_get_similar_users(mock_db_session):
    recommender = RecommenderFast(mock_db_session)

    similar_users = recommender.get_similar_users(target_user_id=1, n_users=2)

    # user 1과 가장 유사한 user 2를 찾아야 함
    # mock 데이터에서 user 1과 2는 '개인공부'와 '넓은' 특징을 공유
    assert 2 in similar_users
    assert len(similar_users) == 2

def test_recommend_places(mock_db_session, mock_data):
    recommender = RecommenderFast(mock_db_session)

    # user 1은 user 2와 유사하므로, user 2가 좋아한 장소(id:1)가 추천되어야 함.
    # mock_likes에 따라 user 1은 1,2를 좋아하고 user 2는 1을 좋아함.
    # 추천 로직은 이미 좋아한 장소를 제거하므로 추천 대상은 없음.

    # user 3이 user 1과 유사하다고 가정하고 테스트 진행
    # user 1: {1, 2} 좋아요
    # user 3: {3} 좋아요
    # 실제로는 유사도가 낮겠지만, 테스트를 위해 user 3을 추천 대상에 포함시켜 봄

    # 추천 로직을 위한 가짜 유사도 행렬 직접 주입
    recommender.similarity_matrix = np.array([
        [1.0, 0.9, 0.1],  # user 1 -> user 2와 유사
        [0.9, 1.0, 0.1],  # user 2 -> user 1과 유사
        [0.1, 0.1, 1.0]
    ])

    # user 1에게 추천 실행
    recommended_places = recommender.recommend_places(target_user_id=1, n_recommendations=1)

    # user 1은 이미 Place 1과 2를 좋아하므로, user 2가 좋아하는 장소 1이 추천되면 안됨.
    # 유사 사용자가 좋아한 장소(1)를 추천 후보로 고려하지만, 이미 좋아요를 눌렀으므로 최종 목록에서 제외.
    # 이 mock 데이터로는 추천 결과가 비어있을 수 있음
    assert len(recommended_places) == 0