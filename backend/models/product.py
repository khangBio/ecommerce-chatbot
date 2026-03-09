# backend/models/product.py
"""
Model để tương tác với collection products trong MongoDB
"""
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ProductModel:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.database_name = "ecommerce"
        self.collection_name = "products"
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

    def get_all_products(self, limit: int = 100) -> List[Dict]:
        """Lấy tất cả sản phẩm"""
        if self.collection is None:
            return []

        products = list(self.collection.find({}, {"_id": 0}).limit(limit))
        return products

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Lấy sản phẩm theo ID"""
        if self.collection is None:
            return None

        product = self.collection.find_one({"id": product_id}, {"_id": 0})
        return product

    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """Tìm kiếm sản phẩm theo text"""
        if self.collection is None:
            return []

        # Tìm kiếm full-text
        results = list(self.collection.find(
            {"$text": {"$search": query}},
            {"_id": 0, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit))

        return results

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Lấy sản phẩm theo category"""
        if self.collection is None:
            return []

        products = list(self.collection.find(
            {"category": category},
            {"_id": 0}
        ))
        return products

    def add_product(self, product_data: Dict) -> bool:
        """Thêm sản phẩm mới"""
        if self.collection is None:
            return False

        try:
            # Thêm timestamp
            product_data["created_at"] = datetime.utcnow()

            result = self.collection.insert_one(product_data)
            return result.acknowledged
        except Exception as e:
            print(f"❌ Error adding product: {e}")
            return False

    def update_product(self, product_id: str, update_data: Dict) -> bool:
        """Cập nhật sản phẩm"""
        if self.collection is None:
            return False

        try:
            update_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"id": product_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating product: {e}")
            return False

    def delete_product(self, product_id: str) -> bool:
        """Xóa sản phẩm"""
        if self.collection is None:
            return False

        try:
            result = self.collection.delete_one({"id": product_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Error deleting product: {e}")
            return False

    def get_product_count(self) -> int:
        """Đếm số lượng sản phẩm"""
        if self.collection is None:
            return 0

        return self.collection.count_documents({})

# ===== USAGE EXAMPLE =====
if __name__ == "__main__":
    # Khởi tạo model
    product_model = ProductModel()

    # Kết nối
    if product_model.connect():
        print("✅ Connected to MongoDB")

        # Lấy tất cả sản phẩm
        products = product_model.get_all_products(5)
        print(f"📦 Found {len(products)} products")

        # Tìm kiếm
        search_results = product_model.search_products("iPhone")
        print(f"🔍 Search results: {len(search_results)}")

        # Lấy theo category
        phones = product_model.get_products_by_category("Điện thoại")
        print(f"📱 Phones: {len(phones)}")

        # Đóng kết nối
        product_model.disconnect()
        print("🔌 Disconnected")
    else:
        print("❌ Failed to connect")