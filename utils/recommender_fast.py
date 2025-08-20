# recommender_fast.py

import pandas as pd
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from sqlalchemy import select
from collections import Counter, defaultdict
import time

from models.db_models import (
    UserDB, LikeDB,
    user_prefer_place_table, user_purpose_table, user_location_table,
    place_purpose_table, place_mood_table
)

class RecommenderFast:
    """
    빠른 사용자 기반 협업 필터링 추천 시스템.
    사용자의 명시적 선호도와 좋아요 장소의 특징을 모두 반영합니다.
    """
    def __init__(self, db: Session):

        self.db = db
        self.user_profiles = {}
        self.user_likes = {}
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
        end_time = time.time()
        print(f"RecommenderFast 초기화 완료. 총 소요 시간: {end_time - start_time:.2f}초")

    def _load_data(self):
        print("데이터베이스에서 모든 데이터 로드 중...")
        start_time = time.time()

        # 1. 모든 사용자 정보 미리 로드
        users = self.db.query(UserDB).all()

        # 2. 사용자-선호도 중간 테이블 데이터 한 번에 로드
        prefer_places_data = self.db.execute(select(user_prefer_place_table)).fetchall()
        purposes_data = self.db.execute(select(user_purpose_table)).fetchall()
        locations_data = self.db.execute(select(user_location_table)).fetchall()

        # 3. 장소-특징 중간 테이블 데이터 한 번에 로드
        place_purposes_data = self.db.execute(select(place_purpose_table)).fetchall()
        place_moods_data = self.db.execute(select(place_mood_table)).fetchall()

        # 4. 모든 좋아요 미리 로드
        likes = self.db.query(LikeDB).all()

        # 5. 데이터 그룹화 (사용자 선호도)
        user_places_map = defaultdict(list)
        for row in prefer_places_data:
            user_places_map[row.user_id].append(row.value)

        user_purposes_map = defaultdict(list)
        for row in purposes_data:
            user_purposes_map[row.user_id].append(row.value)

        user_locations_map = defaultdict(list)
        for row in locations_data:
            user_locations_map[row.user_id].append(row.value)

        # 6. 데이터 그룹화 (장소 특징)
        place_purposes_map = defaultdict(list)
        for row in place_purposes_data:
            place_purposes_map[row.place_id].append(row.value)

        place_moods_map = defaultdict(list)
        for row in place_moods_data:
            place_moods_map[row.place_id].append(row.value)

        # 7. 좋아요 데이터 그룹화
        self.user_likes = defaultdict(set)
        for like in likes:
            self.user_likes[like.user_id].add(like.place_id)

        # 8. 모든 데이터를 결합하여 최종 사용자 프로필 생성
        self.user_profiles = {}
        for user in users:
            profile_features = Counter()

            # 사용자의 명시적 선호도 반영
            profile_features.update(user_places_map[user.user_id])
            profile_features.update(user_purposes_map[user.user_id])
            profile_features.update(user_locations_map[user.user_id])

            # 사용자가 좋아요한 장소의 특징 반영
            liked_places = self.user_likes[user.user_id]
            for place_id in liked_places:
                profile_features.update(place_purposes_map[place_id])
                profile_features.update(place_moods_map[place_id])

            self.user_profiles[user.user_id] = profile_features

        end_time = time.time()
        print(f"데이터 로드 및 프로필 생성 완료. 소요 시간: {end_time - start_time:.2f}초")

    def _create_feature_matrix(self):
        print("피처 매트릭스 생성 중...")
        start_time = time.time()

        # 모든 가능한 피처 컬럼을 통합하여 생성
        all_features = set()
        for profile in self.user_profiles.values():
            all_features.update(profile.keys())

        self.feature_columns = {col: i for i, col in enumerate(sorted(list(all_features)))}

        feature_matrix = []
        user_ids = []
        for user_id, profile in self.user_profiles.items():
            vec = [0] * len(self.feature_columns)
            for feature, count in profile.items():
                if feature in self.feature_columns:
                    idx = self.feature_columns[feature]
                    vec[idx] = count
            feature_matrix.append(vec)
            user_ids.append(user_id)

        self.feature_matrix = np.array(feature_matrix)
        self.user_id_list = user_ids

        end_time = time.time()
        print(f"피처 매트릭스 생성 완료. 소요 시간: {end_time - start_time:.2f}초")

    def _calculate_similarity(self):
        print("유사도 행렬 계산 중...")
        start_time = time.time()

        if len(self.feature_matrix) == 0:
            self.similarity_matrix = np.array([])
        else:
            self.similarity_matrix = cosine_similarity(self.feature_matrix)

        self.user_idx_map = {user_id: idx for idx, user_id in enumerate(self.user_id_list)}

        end_time = time.time()
        print(f"유사도 행렬 계산 완료. 소요 시간: {end_time - start_time:.2f}초")

    def get_similar_users(self, target_user_id: int, n_users: int = 5) -> List[int]:
        if target_user_id not in self.user_idx_map:
            return []

        idx = self.user_idx_map[target_user_id]
        sim_scores = self.similarity_matrix[idx]

        user_id_list_np = np.array(self.user_id_list)
        is_not_target = user_id_list_np != target_user_id

        sorted_indices = np.argsort(sim_scores * is_not_target)[::-1]

        return [user_id_list_np[i] for i in sorted_indices[:n_users]]

    def recommend_places(self, target_user_id: int, n_recommendations: int = 10) -> List[int]:
        start_time = time.time()
        print(f"추천 요청 시작: User ID {target_user_id}")

        similar_users = self.get_similar_users(target_user_id)
        if not similar_users:
            print("유사한 사용자가 없습니다. 추천을 생성하지 않습니다.")
            return []

        all_candidate_places = []
        for uid in similar_users:
            all_candidate_places.extend(self.user_likes.get(uid, []))

        candidate_counts = Counter(all_candidate_places)

        liked = self.user_likes.get(target_user_id, set())
        for place_id in liked:
            candidate_counts.pop(place_id, None)

        recommended = candidate_counts.most_common(n_recommendations)

        end_time = time.time()
        print(f"추천 완료. 추천된 장소 수: {len(recommended)}, 소요 시간: {end_time - start_time:.4f}초")

        return [place_id for place_id, _ in recommended]
