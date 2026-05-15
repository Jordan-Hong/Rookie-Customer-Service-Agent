from langchain_core.tools import tool
from db_manager import SessionLocal
from sqlalchemy import text
from pydantic import BaseModel, Field # 用於定義工具輸入的數據模型
from typing import Optional

class OrderLookupInput(BaseModel):
    order_id: Optional[int] = Field(default=None, description="The exact integer ID of the order to look up.")
    customer_id: Optional[int] = Field(default=None, description="The exact integer ID of the customer. Use this if the order ID is unknown.")
    
@tool(args_schema=OrderLookupInput)
def order_lookup(order_id: int, customer_id: int):
    """Searching for Order States(such as: shipped, delivered)"""
    db = SessionLocal()
    try:
        if order_id:
            query = text("SELECT product_name, status, delivery_date FROM orders WHERE order_id = :oid")
            result = db.execute(query, {"oid": order_id}).fetchone()
            return f"Order {order_id}: {result}" if result else "Order not found."
        elif customer_id:
            query = text("SELECT order_id, product_name, status, delivery_date FROM orders WHERE customer_id = :cid")
            results = db.execute(query, {"cid": customer_id}).fetchall()
        else:
            return "Error: Please provide either order_id or customer_id."
        
        if results:
                return "\n".join([f"Order {r[0]}: {r[1]}, Status: {r[2]}, Delivery Date: {r[3]}" for r in results])
        else:
            return "No orders found for this customer."
    finally:
        db.close()


class CustomerProfileInput(BaseModel):
    customer_id: Optional[int] = Field(default=None, description="The exact integer ID of the customer.")
    name: Optional[str] = Field(default=None, description="The name of the customer. Use this if the customer ID is unknown.")

@tool(args_schema=CustomerProfileInput)
def customer_profile_lookup(customer_id: int = None, name: str = None):
    """Searching for Customer Profile Information (Name, Email, and ID)."""
    db = SessionLocal()
    try:
        if customer_id:
            query = text("SELECT customer_id, name, email FROM customers WHERE customer_id = :cid")
            result = db.execute(query, {"cid": customer_id}).fetchone()
        elif name:
            query = text("SELECT customer_id, name, email FROM customers WHERE name = :name")
            result = db.execute(query, {"name": name}).fetchone()
        else:
            return "Error: Please provide either customer_id or name."
            
        if result:
            return f"Found! Customer ID is {result[0]}, Name is {result[1]}, Email is {result[2]}"
        else:
            return "Cannot find customer profile. Please ask the user for their exact Customer ID."
    finally:
        db.close()

class RefundOrderInput(BaseModel):
    order_id: int = Field(description="The exact integer ID of the order to refund.")
@tool(args_schema=RefundOrderInput)
def refund_order(order_id: int):
    """[Dangerous Operation]Set order status to refund_requested。"""
    db = SessionLocal()
    try:
        # UPDATE orders SET status='refund_requested' WHERE order_id = ?
        query = text("UPDATE orders SET status='refund_requested' WHERE order_id = :oid")
        db.execute(query, {"oid": order_id})
        db.commit()
        return f"Order {order_id} has successfully submitted a refund request."
    except Exception as e:
        return f"Refund execution failed: {e}"
    finally:
        db.close()

class LogComplaintInput(BaseModel):
    customer_id: int = Field(description="The exact integer ID of the customer.")
    order_id: int = Field(description="The exact integer ID of the order.")
    issue: str = Field(description="The description of the complaint or issue.")

@tool(args_schema=LogComplaintInput)
def log_complaint(customer_id: int, order_id: int, issue: str):
    """Records customer complaints in the database."""
    db = SessionLocal()
    try:
        query = text("INSERT INTO complaints (customer_id, order_id, issue, status) VALUES (:cid, :oid, :issue, 'open')")
        db.execute(query, {"cid": customer_id, "oid": order_id, "issue": issue})
        db.commit()
        return "Complaint has been recorded, we will handle it as soon as possible."
    except Exception as e:
        db.rollback() 
        return f"Failed to log complaint. Please ensure the order_id is correct. Error detail: {str(e)}"
    finally:
        db.close()



class RegisterCustomerInput(BaseModel):
    name: str = Field(description="The name of the new customer to register.")
    email: Optional[str] = Field(default="unknown@example.com", description="The email of the new customer.")

@tool(args_schema=RegisterCustomerInput)
def register_customer(name: str, email: str = "unknown@example.com"):
    """Registers a new customer into the database and generates a new Customer ID."""
    db = SessionLocal()
    try:
        # 第一道防線：再次確認這個名字是否真的不存在
        check_query = text("SELECT customer_id FROM customers WHERE name = :name")
        existing = db.execute(check_query, {"name": name}).fetchone()
        if existing:
            return f"Customer {name} already exists with ID: {existing[0]}"

        # 找出目前資料庫中最大的 customer_id，並 +1 當作新 ID
        max_id_query = text("SELECT COALESCE(MAX(customer_id), 0) + 1 FROM customers")
        new_id = db.execute(max_id_query).fetchone()[0]

        # 寫入新用戶資料
        insert_query = text("INSERT INTO customers (customer_id, name, email) VALUES (:cid, :name, :email)")
        db.execute(insert_query, {"cid": new_id, "name": name, "email": email})
        db.commit()
        
        return f"Registration successful! Welcome {name}. Your new Customer ID is {new_id}."
    except Exception as e:
        db.rollback()
        return f"Failed to register new customer. Error: {str(e)}"
    finally:
        db.close()


class NewOrderInput(BaseModel):
    customer_id: int = Field(description="The exact integer ID of the customer placing the order.")
    product_name: str = Field(description="The name of the product the customer wants to order.")

@tool(args_schema=NewOrderInput)
def create_new_order(customer_id: int, product_name: str):
    """Creates a new order for the customer and returns the new Order ID."""
    db = SessionLocal()
    try:
        # 找出目前最大的 order_id 並 +1。為了與舊訂單(1001, 2001)區隔，設定基準值為 3000
        max_id_query = text("SELECT COALESCE(MAX(order_id), 3000) + 1 FROM orders")
        new_order_id = db.execute(max_id_query).fetchone()[0]

        # 寫入新訂單 (狀態預設為 pending，日期使用 MySQL 內建的 NOW())
        insert_query = text("""
            INSERT INTO orders (order_id, customer_id, product_name, status, order_date) 
            VALUES (:oid, :cid, :pname, 'pending', NOW())
        """)
        db.execute(insert_query, {
            "oid": new_order_id, 
            "cid": customer_id, 
            "pname": product_name
        })
        db.commit()
        
        return f"Order successfully created! The new Order ID is {new_order_id} for the product '{product_name}'."
    except Exception as e:
        db.rollback()
        return f"Failed to create new order. Error: {str(e)}"
    finally:
        db.close()

class CancelRefundInput(BaseModel):
    order_id: int = Field(description="The exact integer ID of the order to cancel the refund for.")

@tool(args_schema=CancelRefundInput)
def cancel_refund(order_id: int):
    """Cancels a refund request and resets the order status back to 'pending' or 'shipped'."""
    db = SessionLocal()
    try:
        # 將訂單狀態從 refund_requested 改回 pending
        query = text("UPDATE orders SET status='pending' WHERE order_id = :oid")
        db.execute(query, {"oid": order_id})
        db.commit()
        return f"Successfully cancelled the refund request for Order {order_id}."
    except Exception as e:
        db.rollback()
        return f"Failed to cancel refund: {str(e)}"
    finally:
        db.close()