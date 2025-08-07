from fastapi import FastAPI
from schemas.request_response import MemoList
from models.recommender_kobert import get_recommendations_kobert

app = FastAPI()

@app.post("/ai/recommend")
def recommend_places(memo_list: MemoList):
    return get_recommendations_kobert(memo_list)
