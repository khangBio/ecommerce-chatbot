# backend/models/conversation.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import List, Dict
from datetime import datetime
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

class ConversationModel:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.database_name = "ecommerce"
        self.collection_name = "chat_history"
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        try:
            self.client = MongoClient(self.mongo_uri, tlsCAFile=certifi.where())
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            return True
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()

    def save_interaction(self, user_id: str, user_message: str, bot_response: str, intent: str = ""):
        """Lưu một lượt hỏi-đáp vào DB"""
        if self.collection is None:
            return False
        
        doc = {
            "user_id": user_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "intent": intent,
            "timestamp": datetime.utcnow()
        }
        try:
            self.collection.insert_one(doc)
            return True
        except Exception as e:
            print(f"❌ Error saving chat: {e}")
            return False

    def get_history_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Lấy lịch sử chat của user, sắp xếp từ cũ đến mới để vẽ lên giao diện"""
        if self.collection is None:
            return []
        
        # sort("timestamp", 1) để tin cũ ở trên, tin mới ở dưới
        cursor = self.collection.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", 1).limit(limit)
        return list(cursor)