import pytest
from collections import Counter, defaultdict
import numpy as np
from utils.recommender_fast import RecommenderFast, PlaceEnum
from models.models import PlaceRecommendation

class MockUser:
    def __init__(self, user_id, prefer_places=None, purposes=None, locations=None):
        self.user_id = user_id
        self.prefer_places = prefer_places or []
        self.purposes = purposes or []
        self.locations = locations or []

class MockPlace:
    def __init__(self, place_id, name, types=None, purposes=None, moods=None, locations=None, is_free=None, address=None, photo_url=""):
        self.place_id = place_id
        self.name = name
        self.types = types or []
        self.purposes = purposes or []
        self.moods = moods or []
        self.locations = locations or []
        self.photo_url = photo_url
        self.is_free = is_free
        self.location = address

class MockLike:
    def __init__(self, user_id, place_id):
        self.user_id = user_id
        self.place_id = place_id

class MockEnum:
    def __init__(self, value):
        self.value = value

class MockQuery:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def filter(self, condition):
        recommended_ids = getattr(condition.right, 'value', [])
        filtered = [p for p in self.items if p.place_id in recommended_ids]
        return MockQuery(filtered)

class MockDB:
    def __init__(self):
        self.users = [
            MockUser(
                1,
                prefer_places=[MockEnum("공공학습공간")],
                purposes=[MockEnum("휴식")],
                locations=[MockEnum("강북권")]
            ),
            MockUser(
                2,
                prefer_places=[MockEnum("카페")],
                purposes=[MockEnum("집중공부")],
                locations=[MockEnum("서남권")]
            )
        ]
        self.places = [
            MockPlace(
                101, "Seoul Library",
                types=[MockEnum("공공학습공간")],
                purposes=[MockEnum("휴식")],
                moods=[MockEnum("아늑한")],
                locations=[MockEnum("강북권")],
                is_free=True,  # Add is_free
                address="서울특별시 강북구 도봉로123" # Add a mock address
            ),
            MockPlace(
                102, "Busan Cafe",
                types=[MockEnum("카페")],
                purposes=[MockEnum("집중공부")],
                moods=[MockEnum("조용한")],
                locations=[MockEnum("서남권")],
                is_free=False,
                address="부산광역시 해운대구 센텀로456"
            )
        ]
        self.likes = [MockLike(2, 101)]

def test_recommender_basic():
    mock_db = MockDB()
    recommender = RecommenderFast(mock_db)

    assert len(recommender.user_profiles) == 2
    assert recommender.user_profiles[1]["공공학습공간"] > 0
    assert recommender.user_profiles[2]["집중공부"] > 0

    similar = recommender.get_similar_users(1)
    assert 2 in similar

    recommendations = recommender.recommend_places(1)
    assert len(recommendations) > 0
    assert isinstance(recommendations[0], PlaceRecommendation)
    assert recommendations[0].place_id == 101

    recommended_place = recommendations[0]
    assert recommended_place.address == "서울특별시 강북구 도봉로123"
    assert recommended_place.is_free is True
    assert recommended_place.name == "Seoul Library"
    assert recommended_place.type == PlaceEnum.공공학습공간
