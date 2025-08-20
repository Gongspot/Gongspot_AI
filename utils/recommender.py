# recommender.py

import pandas as pd
import numpy as np
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from models.db_models import UserDB, LikeDB
from models.models import LocationEnum, PlaceEnum, PurposeEnum

class Recommender:
    ''' 사용자 협업 필터링 기반 추천 클래스 '''
    def __init__(self, db: Session):
        self.db = db
        self.user_profiles = None
        self.user_likes = None
        self.similarity_matrix = None

    def _ensure_loaded(self):
        if self.user_profiles is None:
            self.user_profiles = self._load_user_profiles()
        if self.user_likes is None:
            self.user_likes = self._load_user_likes()
        if self.similarity_matrix is None:
            self.similarity_matrix = self._calculate_similarity()

    def _load_user_profiles(self) -> pd.DataFrame:
        """
        데이터베이스에서 모든 사용자의 선호 데이터를 로드하고 DataFrame으로 변환합니다.
        """
        # users = self.db.query(UserDB).all()
        users = self.db.query(UserDB.user_id, UserDB.prefer_place, UserDB.purpose, UserDB.location).all()

        data = []
        for user in users:
            # Java 엔티티 기준: prefer_place, purpose, location이 리스트 형태로 이미 존재
            data.append({
                'user_id': user.user_id,
                'prefer_place': [p.value for p in user.prefer_place] if user.prefer_place else [],
                'purpose': [p.value for p in user.purpose] if user.purpose else [],
                'location': [l.value for l in user.location] if user.location else []
            })
        return pd.DataFrame(data).set_index('user_id')

    def _load_user_likes(self) -> pd.DataFrame:
        """
        데이터베이스에서 모든 사용자의 '좋아요' 기록을 로드합니다.
        """
        likes = self.db.query(LikeDB).all()
        data = [{'user_id': like.user_id, 'place_id': like.place_id} for like in likes]
        return pd.DataFrame(data)


    def _create_feature_matrix(self) -> pd.DataFrame:
        """
        사용자 프로필을 기반으로 특성 행렬(Feature Matrix)을 생성합니다.
        One-Hot Encoding 방식을 사용하여 각 선호 항목을 숫자로 변환합니다.
        """
        df = self.user_profiles.reset_index()

        # PlaceEnum, PurposeEnum, LocationEnum의 모든 값을 포함하는 컬럼 생성
        all_places = [e.value for e in PlaceEnum]
        all_purposes = [e.value for e in PurposeEnum]
        all_locations = [e.value for e in LocationEnum]

        all_features = all_places + all_purposes + all_locations

        # 각 사용자의 선호도에 따라 0 또는 1로 채워진 행렬 생성
        feature_matrix = pd.DataFrame(0, index=df['user_id'], columns=all_features)

        for index, row in df.iterrows():
            for feature in row['prefer_place']:
                feature_matrix.loc[row['user_id'], feature] = 1
            for feature in row['purpose']:
                feature_matrix.loc[row['user_id'], feature] = 1
            for feature in row['location']:
                feature_matrix.loc[row['user_id'], feature] = 1

        return feature_matrix

    def _calculate_similarity(self):
        """
        코사인 유사도를 사용하여 사용자 간의 유사성 행렬을 계산합니다.
        """
        feature_matrix = self._create_feature_matrix()
        if feature_matrix.empty:
            return pd.DataFrame()

        similarity_df = pd.DataFrame(
            cosine_similarity(feature_matrix),
            index=feature_matrix.index,
            columns=feature_matrix.index
        )
        return similarity_df

    def get_similar_users(self, target_user_id: int, n_users: int = 5):
        feature_matrix = self._create_feature_matrix()
        if target_user_id not in feature_matrix.index:
            return []
        target_vec = feature_matrix.loc[target_user_id].values.reshape(1, -1)
        others = feature_matrix.drop(target_user_id)
        sim = cosine_similarity(target_vec, others)[0]
        return others.index[np.argsort(sim)[::-1][:n_users]].tolist()


    def recommend_places(self, target_user_id: int, n_recommendations: int = 10) -> List[int]:
        """
        유사한 사용자들이 좋아한 장소를 추천합니다.
        """
        similar_users = self.get_similar_users(target_user_id)
        if not similar_users:
            return []

        # 유사한 사용자들이 좋아요 누른 장소 목록 필터링
        similar_users_likes = self.user_likes[self.user_likes['user_id'].isin(similar_users)]

        if similar_users_likes.empty:
            return []

        # 좋아요를 가장 많이 받은 장소 상위 n개 선정
        recommended_places = similar_users_likes['place_id'].value_counts().head(n_recommendations).index.tolist()

        return recommended_places