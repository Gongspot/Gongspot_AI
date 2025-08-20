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
    def __init__(self, place_id, name, types=None, purposes=None, moods=None, locations=None, photo_url=""):
        self.place_id = place_id
        self.name = name
        self.types = types or []
        self.purposes = purposes or []
        self.moods = moods or []
        self.locations = locations or []
        self.photo_url = photo_url

class MockLike:
    def __init__(self, user_id, place_id):
        self.user_id = user_id
        self.place_id = place_id

class MockEnum:
    def __init__(self, value):
        self.value = value

class MockDB:
    def __init__(self):
        self.users = [
            MockUser(1, prefer_places=[MockEnum("park")], purposes=[MockEnum("relax")], locations=[MockEnum("seoul")]),
            MockUser(2, prefer_places=[MockEnum("cafe")], purposes=[MockEnum("study")], locations=[MockEnum("busan")])
        ]
        self.places = [
            MockPlace(101, "Seoul Park", types=[MockEnum("공원")], purposes=[MockEnum("relax")], moods=[MockEnum("happy")], locations=[MockEnum("seoul")]),
            MockPlace(102, "Busan Cafe", types=[MockEnum("카페")], purposes=[MockEnum("study")], moods=[MockEnum("calm")], locations=[MockEnum("busan")])
        ]
        self.likes = [MockLike(2, 101)]

    def query(self, model):
        if model.__name__ == "UserDB":
            return self
        elif model.__name__ == "PlaceDB":
            return self
        elif model.__name__ == "LikeDB":
            return self
        return self

    def all(self):
        import inspect
        caller_frame = inspect.stack()[1]
        if 'UserDB' in caller_frame.code_context[0]:
            return self.users
        elif 'PlaceDB' in caller_frame.code_context[0]:
            return self.places
        elif 'LikeDB' in caller_frame.code_context[0]:
            return self.likes
        return []

    def filter(self, condition):
        recommended_ids = condition.right.value
        return [p for p in self.places if p.place_id in recommended_ids]

def test_recommender_basic():
    mock_db = MockDB()
    recommender = RecommenderFast(mock_db)
    assert len(recommender.user_profiles) == 2
    assert recommender.user_profiles[1]["park"] > 0
    assert recommender.user_profiles[2]["study"] > 0
    similar = recommender.get_similar_users(1)
    assert 2 in similar
    recommendations = recommender.recommend_places(1)
    assert len(recommendations) > 0
    assert isinstance(recommendations[0], PlaceRecommendation)
    assert recommendations[0].place_id == 101
