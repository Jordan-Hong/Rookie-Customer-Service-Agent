from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 資料庫連線配置
# 格式: mysql+pymysql://帳號:密碼@主機:埠/資料庫名
DB_URL = "mysql+pymysql://"USER_NAME":"DB_PASSWORD"@localhost:3306/"DB_NAME""

# 建立 Engine，pool_size 是連線池大小，這就像韌體裡的 Buffer 管理
engine = create_engine(
    DB_URL, 
    pool_size=5, 
    max_overflow=10,
    pool_recycle=3600
)

# 建立 Session 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """獲取資料庫連線的 Generator，確保每次用完都會關閉連線"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# 測試連線是否成功
if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            print("Successfully connected to the database!")
    except Exception as e:
        print(f"Connection failed: {e}")