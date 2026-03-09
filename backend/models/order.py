# backend/models/order.py
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class OrderModel:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.database_name = "ecommerce"
        self.collection_name = "orders"
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        """Kết nối đến MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri, tlsCAFile=certifi.where())
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            return True
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False

    def disconnect(self):
        """Đóng kết nối"""
        if self.client:
            self.client.close()

    def create_order(self, order_data: Dict) -> bool:
        """Thêm đơn hàng mới vào DB"""
        if self.collection is None:
            return False
        try:
            result = self.collection.insert_one(order_data)
            return result.acknowledged
        except Exception as e:
            print(f"❌ Error creating order: {e}")
            return False

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Lấy đơn hàng theo mã đơn"""
        if self.collection is None:
            return None
        return self.collection.find_one({"order_id": order_id}, {"_id": 0})

    def get_orders_by_user(self, user_id: str) -> List[Dict]:
        """Lấy tất cả đơn hàng của một user (Sắp xếp mới nhất lên đầu)"""
        if self.collection is None:
            return []
        # sort("created_at", -1) để đơn hàng mới nhất hiện lên trên cùng
        return list(self.collection.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1))
        
    def update_order(self, order_id: str, update_data: Dict) -> bool:
        """Cập nhật thông tin/trạng thái đơn hàng"""
        if self.collection is None:
            return False
        try:
            result = self.collection.update_one(
                {"order_id": order_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating order: {e}")
            return False