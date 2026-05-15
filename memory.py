from langchain_core.tools import tool
from db_manager import SessionLocal
from sqlalchemy import text
from pydantic import BaseModel, Field

# 1. 為 save_user_memory 建立輸入結構(才可以讓Llama正確解析參數)
class SaveMemoryInput(BaseModel):
    customer_id: int = Field(description="The exact integer ID of the customer.")
    key: str = Field(description="The memory key, e.g., 'refund_preference'.")
    value: str = Field(description="The memory value.")

@tool(args_schema=SaveMemoryInput)
def save_user_memory(customer_id: int, key: str, value: str): 
    """Saves OR updates customer preferences and memories in the database. Use this tool even if the user asks to 'update' their preference."""
    db = SessionLocal()
    try:
        query = text("INSERT INTO customer_memory (customer_id, memory_key, memory_value) VALUES (:cid, :k, :v)")
        db.execute(query, {"cid": customer_id, "k": key, "v": value})
        db.commit()
        return f"Memory successfully saved/updated for customer {customer_id}: {key} = {value}"
    except Exception as e:
        db.rollback()
        return f"Failed to save memory. Error: {str(e)}"
    finally:
        db.close()

# 2. 為 load_user_memory 建立輸入結構
class LoadMemoryInput(BaseModel):
    customer_id: int = Field(description="The exact integer ID of the customer.")

@tool(args_schema=LoadMemoryInput)
def load_user_memory(customer_id: int):
    """Loads all personalized memories for the specified customer."""
    db = SessionLocal()
    try:
        query = text("SELECT memory_key, memory_value FROM customer_memory WHERE customer_id = :cid")
        results = db.execute(query, {"cid": customer_id}).fetchall()
        return "\n".join([f"{r[0]}: {r[1]}" for r in results]) if results else "No previous memories found."
    finally:
        db.close()