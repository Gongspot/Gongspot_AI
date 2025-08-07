from transformers import BertModel, BertTokenizer
import torch

# KoBERT 모델 로드
tokenizer = BertTokenizer.from_pretrained("monologg/kobert")
model = BertModel.from_pretrained("monologg/kobert")
model.eval()

def get_kobert_embedding(text: str):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] 토큰 벡터
        return cls_embedding.squeeze().numpy()
