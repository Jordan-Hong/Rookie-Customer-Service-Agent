# init_db.py
from db_manager import SessionLocal, engine
from sqlalchemy import text

def init_mock_data():
    db = SessionLocal()
    try:
        print("開始注入測試資料...")
        
        # 1. 插入假客戶
        db.execute(text("INSERT IGNORE INTO customers (customer_id, name, email) VALUES (1, 'Jordan', 'jordan@example.com')"))
        db.execute(text("INSERT IGNORE INTO customers (customer_id, name, email) VALUES (2, 'Pei', 'pei@example.com')"))
        
        # 2. 插入假訂單
        db.execute(text("INSERT IGNORE INTO orders (order_id, customer_id, product_name, status) VALUES (1001, 1, 'Arduino Uno R3', 'delivered')"))
        db.execute(text("INSERT IGNORE INTO orders (order_id, customer_id, product_name, status) VALUES (1002, 1, 'Motor Shield', 'shipped')"))
        db.execute(text("INSERT IGNORE INTO orders (order_id, customer_id, product_name, status) VALUES (2001, 2, 'Color Theory Book', 'pending')"))
        
        db.commit()
        print("測試資料注入完成！")
    except Exception as e:
        db.rollback()
        print(f"發生錯誤: {e}")
    finally:
        db.close()

# 你可以使用這個檔案創建完整假資料進DB，也可以直接透過客服系統創建新會員、新訂單，但是無法指定order_id與customer_id。
if __name__ == "__main__":
    init_mock_data()
