from tools import order_lookup, customer_profile_lookup, refund_order, log_complaint, register_customer, create_new_order, cancel_refund
from langgraph.checkpoint.memory import MemorySaver # 導入短期記憶存檔點
from memory import save_user_memory, load_user_memory
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
import json
import uuid
import re

# 定義狀態類型
class CustomerServiceState(TypedDict):
    messages: Annotated[list, add_messages]
    is_verified: bool

# 初始化 LLM 和工具
llm = ChatOllama(model="llama3.1", temperature=0)
tools = [order_lookup, customer_profile_lookup, refund_order, log_complaint, save_user_memory, load_user_memory, register_customer, create_new_order, cancel_refund]
llm__withtools = llm.bind_tools(tools)
memory = MemorySaver()

# 提取system prompt
def load_prompts():
    with open("system_prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG_PROMPTS = load_prompts()

# 定義節點及函數
def agent_node(state: CustomerServiceState):
    system_prompt = SystemMessage(content=CONFIG_PROMPTS["agent_system_prompt"])
    full_msg = [system_prompt] + state["messages"]
    response = llm__withtools.invoke(full_msg)
    
    return {"messages": [response]}
    
def verifier_node(state: CustomerServiceState):
    last_message = state["messages"][-1]
    
    # 簡化 Verifier 邏輯，避免它誤砍正常的對話交際
    verifier_prompt = f"""You are a safety verifier for a customer service agent. 
    The agent's last message was: {last_message.content if hasattr(last_message, 'content') else last_message}
    
    CRITICAL CHECK: 
    1. If the agent's message contains raw JSON like '{{"name": "function_name"}}' in plain text, REJECT it immediately! Tell the agent to use native tool calling.
    2. If the agent is simply talking to the user (e.g., politely asking for their name or ID), APPROVE.
    3. If the agent successfully used a tool and is reporting the result, APPROVE.
    
    Respond with exactly "approve" if everything is fine, or "reject" followed by a brief reason if there is plain text JSON.
    """
    
    # 使用基礎 LLM (不綁定 tools) 來做純文字驗證
    verification_response = llm.invoke(verifier_prompt)
    state["is_verified"] = "approve" in verification_response.content.lower()

    if not state["is_verified"]:
        feedback_content = f"[System Verifier Feedback]: {verification_response.content}\nPlease correct your format."
        feedback_msg = HumanMessage(content=feedback_content)
        return {"messages": [feedback_msg], "is_verified": False}
    else:
        return {"is_verified": True}



def after_verification(state: CustomerServiceState):
    if not state["is_verified"]: 
        return "agent" # 審核未通過，打回票請 Agent 重新回覆
    return END

def should_continue(state: CustomerServiceState) -> Literal["tools", "verifier"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "verifier"


# 定義工作流程
workflow = StateGraph(CustomerServiceState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("verifier", verifier_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("verifier", after_verification)

app = workflow.compile(checkpointer=memory) # 編譯工作流程，並指定記憶存檔點(Short-term memory)




def run_interactive_test():
    print("=== 智慧客服 Agent 測試啟動 ===")
    print("輸入 'exit' 或 'quit' 離開系統\n")
    
    # 建立一個唯一的 session ID，用來觸發 Short-term Memory
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        # 1. 將使用者的話包裝成 HumanMessage
        initial_input = {"messages": [HumanMessage(content=user_input)]}
        
        # 2. 觸發 LangGraph 狀態機
        # stream() 可以讓我們看到每一個 Node 的執行過程
        for event in app.stream(initial_input, config=config):
            for node_name, node_state in event.items():
                print(f"\n--- [系統狀態] 離開節點: {node_name} ---")
                
                # 印出該節點產生的最新訊息
                if "messages" in node_state and len(node_state["messages"]) > 0:
                    last_msg = node_state["messages"][-1]
                    
                    if isinstance(last_msg, AIMessage):
                        if last_msg.tool_calls:
                            print(f"Agent 決定呼叫工具: {last_msg.tool_calls[0]['name']}")
                        else:
                            print(f"Agent 回覆: {last_msg.content}")
                    elif isinstance(last_msg, ToolMessage):
                        print(f"工具執行結果: {last_msg.content}")
        print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    run_interactive_test()