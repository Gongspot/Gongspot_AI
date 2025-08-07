from pydantic import BaseModel
from typing import List

class Memo(BaseModel):
    id: str
    content: str

class MemoList(BaseModel):
    memos: List[Memo]
