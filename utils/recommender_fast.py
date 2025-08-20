# utils/recommender_fast.py
import numpy as np
from collections import Counter, defaultdict
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
import time

from sqlalchemy.orm import Session
from models.db_models import UserDB, PlaceDB, LikeDB
from models.models import PlaceRecommendation
from models.enums import PlaceEnum

class RecommenderFast:
    """
    빠른 사용자 기반 협업 필터링 추천 시스템.
    사용자의 명시적 선호도와 좋아요 장소의 특징을 모두 반영.
    """
    def __init__(self, db: Session):
        self.db = db
        self.user_profiles = {}
        self.user_likes = defaultdict(set)
        self.similarity_matrix = None
        self.feature_columns = {}
        self.user_id_list = []
        self.user_idx_map = {}
        self.feature_matrix = None

        print("RecommenderFast 초기화 시작...")
        start_time = time.time()
        self._load_data()
        self._create_feature_matrix()
        self._calculate_similarity()
        print(f"RecommenderFast 초기화 완료. 소요 시간: {time.time() - start_time:.2f}초")

    def _load_data(self):
        print("데이터 로드 중...")
        start_time = time.time()

        users = self.db.query(UserDB).all()
        places = {p.place_id: p for p in self.db.query(PlaceDB).all()}
        likes = self.db.query(LikeDB).all()

        # 사용자 좋아요 맵 생성
        for like in likes:
            if isinstance(like.place_id, int):
                self.user_likes[like.user_id].add(like.place_id)
            else:
                print(f"[WARN] 잘못된 place_id: {like.place_id} (type={type(like.place_id)})")

        # 사용자 프로필 생성
        for user in users:
            profile_features = Counter()

            # User의 M2M 관계 직접 반영
            profile_features.update([p.value for p in user.prefer_places])
            profile_features.update([p.value for p in user.purposes])
            profile_features.update([l.value for l in user.locations])

            # 좋아요한 장소 특징 반영
            for place_id in self.user_likes[user.user_id]:
                place = places.get(place_id)
                if place:
                    profile_features.update([p.value for p in place.purposes])
                    profile_features.update([m.value for m in place.moods])
            self.user_profiles[user.user_id] = profile_features

        print(f"데이터 로드 완료. Users: {len(users)}, Places: {len(places)}, Likes: {len(likes)}")
        print(f"데이터 로드 소요 시간: {time.time() - start_time:.2f}초")

    def _create_feature_matrix(self):
        print("피처 매트릭스 생성 중...")
        all_features = set()
        for profile in self.user_profiles.values():
            all_features.update(profile.keys())
        self.feature_columns = {f: i for i, f in enumerate(sorted(all_features))}

        feature_matrix = []
        user_ids = []
        for user_id, profile in self.user_profiles.items():
            vec = [0] * len(self.feature_columns)
            for feature, count in profile.items():
                idx = self.feature_columns.get(feature)
                if idx is not None:
                    vec[idx] = count
            feature_matrix.append(vec)
            user_ids.append(user_id)

        self.feature_matrix = np.array(feature_matrix)
        self.user_id_list = user_ids
        print("피처 매트릭스 생성 완료.")

    def _calculate_similarity(self):
        print("유사도 행렬 계산 중...")
        if len(self.feature_matrix) == 0:
            self.similarity_matrix = np.array([])
        else:
            self.similarity_matrix = cosine_similarity(self.feature_matrix)
        self.user_idx_map = {uid: idx for idx, uid in enumerate(self.user_id_list)}
        print("유사도 행렬 계산 완료.")

    def get_similar_users(self, target_user_id: int, n_users: int = 5) -> List[int]:
        if target_user_id not in self.user_idx_map:
            return []
        idx = self.user_idx_map[target_user_id]
        sim_scores = self.similarity_matrix[idx]
        user_id_list_np = np.array(self.user_id_list)
        is_not_target = user_id_list_np != target_user_id
        sorted_indices = np.argsort(sim_scores * is_not_target)[::-1]
        return [user_id_list_np[i] for i in sorted_indices[:n_users]]

    def recommend_places(self, target_user_id: int, n_recommendations: int = 10) -> List[PlaceRecommendation]:
        similar_users = self.get_similar_users(target_user_id)
        if not similar_users:
            return []

        candidate_places = []
        for uid in similar_users:
            candidate_places.extend(self.user_likes.get(uid, []))

        # 좋아요 이미 한 장소 제거
        liked = self.user_likes.get(target_user_id, set())
        candidate_counts = Counter(candidate_places)
        for place_id in liked:
            candidate_counts.pop(place_id, None)

        recommended_ids = [pid for pid, _ in candidate_counts.most_common(n_recommendations)]
        if not recommended_ids:
            return []

        places = self.db.query(PlaceDB).filter(PlaceDB.place_id.in_(recommended_ids)).all()
        recommended_places = [
            PlaceRecommendation(
                place_id=p.place_id,
                name=p.name,
                type=p.types[0].value if p.types else PlaceEnum.공공학습공간,
                purpose=[x.value for x in p.purposes],
                mood=[x.value for x in p.moods],
                location=[x.value for x in p.locations],
                photo_url=p.photo_url
            )
            for p in places
        ]
        return recommended_places
