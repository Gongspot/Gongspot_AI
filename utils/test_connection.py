# utils/test_connection.py
from utils.database import SessionLocal, engine
from models.db_models import UserDB, Base  # models는 루트 기준

# 1. 테이블 연결 확인
try:
    Base.metadata.create_all(bind=engine)
    print("✅ 테이블 연결 OK")
except Exception as e:
    print("❌ 테이블 연결 실패:", e)

# 2. 세션 연결 확인
try:
    db = SessionLocal()
    users = db.query(UserDB).all()
    print("✅ DB 세션 OK, 현재 유저 수:", len(users))
    for user in users:
        print(f"user_id: {user.user_id}, username: {user.username}")
    db.close()
except Exception as e:
    print("❌ DB 쿼리 실패:", e)
