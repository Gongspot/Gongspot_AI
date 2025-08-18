# recommender.py

import pandas as pd
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from .db_models import UserDB, UserLike
from .models import LocationEnum, PlaceEnum, PurposeEnum

class Recommender:
    """
    사용자 기반 협업 필터링 추천 시스템 클래스
    """
    def __init__(self, db: Session):
        self.db = db
        # 모든 사용자 데이터와 좋아요 데이터를 초기화 시점에 미리 로드 (성능 최적화를 위해)
        self.user_profiles = self._load_user_profiles()
        self.user_likes = self._load_user_likes()
        self.similarity_matrix = self._calculate_similarity()

    def _load_user_profiles(self) -> pd.DataFrame:
        """
        데이터베이스에서 모든 사용자의 선호 데이터를 로드하고 DataFrame으로 변환합니다.
        """
        users = self.db.query(UserDB).all()
        data = []
        for user in users:
            # 쉼표로 구분된 문자열을 리스트로 변환
            prefer_place = user.prefer_place.split(',') if user.prefer_place else []
            purpose = user.purpose.split(',') if user.purpose else []
            location = user.location.split(',') if user.location else []

            data.append({
                'user_id': user.user_id,
                'prefer_place': prefer_place,
                'purpose': purpose,
                'location': location
            })
        return pd.DataFrame(data).set_index('user_id')

    def _load_user_likes(self) -> pd.DataFrame:
        """
        데이터베이스에서 모든 사용자의 '좋아요' 기록을 로드합니다.
        """
        likes = self.db.query(UserLike).all()
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

    def get_similar_users(self, target_user_id: int, n_users: int = 5) -> List[int]:
        """
        특정 사용자와 가장 유사한 사용자들의 ID를 반환합니다.
        """
        if self.similarity_matrix.empty or target_user_id not in self.similarity_matrix.index:
            return []

        # 자기 자신을 제외하고 유사도 상위 n명의 사용자 찾기
        similar_users = self.similarity_matrix.loc[target_user_id].sort_values(ascending=False)
        similar_users = similar_users[similar_users.index != target_user_id]

        return similar_users.head(n_users).index.tolist()

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