# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from rag_engine import RAGEngine
from recommendation import RecommendationEngine
from conversation_search import ConversationalSearch
from order_management import OrderManager
#CORS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# CẤU HÌNH CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain gọi API. Khi chạy thực tế có thể thay bằng domain Vercel của bạn
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép GET, POST, PUT, DELETE...
    allow_headers=["*"],
)

load_dotenv()

app = FastAPI(title="E-commerce Chatbot API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
rag_engine = RAGEngine()
recommendation_engine = RecommendationEngine()
conversation_search = ConversationalSearch()
order_manager = OrderManager()

# Request/Response models
class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    bot_message: str
    conversation_id: str
    intent: str
    products: Optional[List[dict]] = None
    order_info: Optional[dict] = None

class ProductSearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    conversation_id: Optional[str] = None

class OrderRequest(BaseModel):
    order_id: str
    user_id: str

# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Xử lý tin nhắn từ người dùng và trả lời thông minh
    Tích hợp 4 tính năng: tư vấn, hỗ trợ, tìm kiếm, sau bán hàng
    """
    try:
        # 1. Phân tích ý định (intent classification)
        intent_result = rag_engine.classify_intent(request.message)
        intent = intent_result["intent"]
        entities = intent_result["entities"]
        
        bot_message = ""
        products = None
        order_info = None
        
        # 2. Xử lý theo intent
        if intent == "product_search":
            # Tính năng: Conversational Search
            search_result = conversation_search.search(
                query=request.message,
                conversation_id=request.conversation_id,
                entities=entities
            )
            products = search_result["products"]
            bot_message = search_result["response"]
            
        elif intent == "product_recommendation":
            # Tính năng: Tư vấn mua hàng tự động
            recommendations = recommendation_engine.get_recommendations(
                user_id=request.user_id,
                preferences=entities,
                conversation_history=conversation_search.get_context(request.conversation_id)
            )
            products = recommendations["products"]
            bot_message = recommendation_engine.generate_recommendation_message(recommendations)
            
        elif intent == "order_tracking":
            # Tính năng: Hỗ trợ sau bán hàng - Theo dõi đơn hàng
            order_id = entities.get("order_id")
            if order_id:
                order_info = order_manager.track_order(order_id)
                bot_message = order_manager.format_tracking_info(order_info)
            else:
                bot_message = "Vui lòng cung cấp mã đơn hàng để tôi tra cứu cho bạn."
                
        elif intent == "return_request":
            # Tính năng: Hỗ trợ sau bán hàng - Đổi trả
            return_info = order_manager.handle_return_request(
                user_id=request.user_id,
                reason=entities.get("reason"),
                order_id=entities.get("order_id")
            )
            bot_message = return_info["message"]
            
        elif intent == "technical_support":
            # Tính năng: Hỗ trợ sau bán hàng - Troubleshooting
            support_response = order_manager.troubleshoot(
                product_name=entities.get("product"),
                issue=entities.get("issue")
            )
            bot_message = support_response
            
        else:
            # Tính năng: Hỗ trợ khách hàng bằng NLP và LLM
            # Sử dụng RAG để trả lời câu hỏi chung
            bot_message = rag_engine.generate_response(
                query=request.message,
                conversation_id=request.conversation_id
            )
        
        # Lưu conversation context
        conversation_id = conversation_search.save_context(
            conversation_id=request.conversation_id,
            user_message=request.message,
            bot_message=bot_message,
            intent=intent
        )
        
        return ChatResponse(
            bot_message=bot_message,
            conversation_id=conversation_id,
            intent=intent,
            products=products,
            order_info=order_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Product search endpoint
@app.post("/search")
async def search_products(request: ProductSearchRequest):
    """Tìm kiếm sản phẩm bằng ngôn ngữ tự nhiên"""
    try:
        result = conversation_search.search(
            query=request.query,
            filters=request.filters,
            conversation_id=request.conversation_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Order tracking endpoint
@app.get("/orders/{order_id}")
async def get_order_status(order_id: str):
    """Tra cứu trạng thái đơn hàng"""
    try:
        order_info = order_manager.track_order(order_id)
        return order_info
    except Exception as e:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

# Create order endpoint
@app.post("/orders")
async def create_order(order_data: dict):
    """Tạo đơn hàng tự động"""
    try:
        order = order_manager.create_order(order_data)
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
