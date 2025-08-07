from schemas.request_response import MemoList
from utils.bert_embedder import get_kobert_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def get_recommendations_kobert(memo_list: MemoList):
    if len(memo_list.memos) == 0:
        return []

    memo_vectors = []
    for memo in memo_list.memos:
        vec = get_kobert_embedding(memo.content)
        memo_vectors.append((memo.id, vec))

    user_vec = np.mean([v for _, v in memo_vectors], axis=0).reshape(1, -1)

    results = []
    for place_id, vec in memo_vectors:
        sim = cosine_similarity(vec.reshape(1, -1), user_vec)[0][0]
        results.append({
            "place_id": place_id,
            "score": round(float(sim), 4)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)
