# backend/recommendation.py
import json
from typing import List, Dict
import random
from models.product import ProductModel

class RecommendationEngine:
    """
    Tư vấn mua hàng tự động
    Gợi ý sản phẩm dựa trên preferences và lịch sử
    """
    
    def __init__(self):
        # KHỞI TẠO KẾT NỐI MONGODB
        self.product_model = ProductModel()
        self.product_model.connect()
        self.user_profiles = {}

    def _normalize_budget(self, budget) -> float:
        """Chuẩn hóa budget về đơn vị VNĐ"""
        if not budget:
            return None
        budget = float(budget)
        if budget < 1_000:          # vd: 20 → 20_000_000
            return budget * 1_000_000
        elif budget < 100_000:    # vd: 20_000 → 20_000_000
            return budget * 1_000
        return budget               # đã đúng dạng VNĐ    
    
    def get_recommendations(self, user_id: str, preferences: dict, 
                          conversation_history: dict = None) -> dict:
        """
        Generate product recommendations
        """
        # Lấy danh sách sản phẩm trực tiếp từ DB
        products = self.product_model.get_all_products(limit=100)

        # Normalize budget: nếu Gemini trả về 20 thay vì 20_000_000
        if "budget" in preferences and preferences["budget"]:
            preferences["budget"] = self._normalize_budget(preferences["budget"])

        # Fallback: nếu không có budget, không gợi ý sản phẩm giá quá cao
        max_price_fallback = preferences.get("budget", float("inf"))
        # Nếu không có budget, áp dụng giới hạn giá mặc định
        if "budget" not in preferences:
            preferences["budget"] = max_price_fallback  # Dùng thực sự

        # Extract preferences from conversation
        budget = preferences.get("budget")
        category = preferences.get("category")
        features = preferences.get("features", [])
        
        # Filter products
        candidates = []
        for product in products: 
            score = self._calculate_score(product, preferences)
            if score >= 0:
                candidates.append({**product, "score": score})
        
        # Sort by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply collaborative filtering (simplified)
        recommendations = self._apply_collaborative_filtering(
            candidates[:10],
            user_id
        )
        
        return {
            "products": recommendations[:5],
            "reasoning": self._generate_reasoning(recommendations[0] if recommendations else {}, preferences)
        }
    
    def _calculate_score(self, product: dict, preferences: dict) -> float:
        """Calculate relevance score"""
        score = 0.0
        
        # Budget matching
        if "budget" in preferences:
            if product["price"] > preferences["budget"]:
                return -1  # Loại bỏ vượt ngân sách
            score += 5.0    

            if product["price"] < preferences["budget"] * 0.8:
                score += 2.0
        
        # Category matching
        if "category" in preferences:
            if product["category"] == preferences["category"]:
                score += 10.0
        
        # Feature matching
        if "features" in preferences:
            for feature in preferences["features"]:
                if feature.lower() in product["description"].lower():
                    score += 3.0
        
        # Popularity (mock)
        score += product.get("rating", 0) * 2
        
        return score
    
    def _apply_collaborative_filtering(self, products: List[dict], 
                                      user_id: str) -> List[dict]:
        """
        Simple collaborative filtering based on user profiles
        """
        # In production: use actual user purchase history
        # and similarity with other users
        return products
    
    def _generate_reasoning(self, product: dict, preferences: dict) -> str:
        """Generate explanation for recommendation"""
        if not product:
            return "Không tìm thấy sản phẩm phù hợp với yêu cầu của bạn."

        budget_display = preferences.get("budget")
        #[CHỈNH SỬA] Hiển thị budget dạng có dấu phẩy, bỏ "inf" khó đọc
        # Bản cũ: in thẳng số float, vd: "1e+18" hoặc "inf"
        # Bản mới: format đẹp hoặc fallback sang "của bạn"
        if budget_display and budget_display != float("inf"):
            budget_str = f"{int(budget_display):,}đ"
        else:
            budget_str = "của bạn"

        reasoning = f"Tôi gợi ý {product['name']} vì:\n"
        reasoning += f"- Phù hợp với ngân sách {preferences.get('budget', 'của bạn')}\n"
        reasoning += f"- Thuộc danh mục {product['category']}\n"
        reasoning += f"- Đánh giá cao ({product.get('rating', 'N/A')} sao)\n"
        return reasoning
    
    def generate_recommendation_message(self, recommendations: dict) -> str:
        """Generate conversational recommendation message"""
        products = recommendations["products"]
        
        if not products:
            return "Tôi chưa tìm thấy sản phẩm phù hợp. Bạn có thể cho tôi biết thêm về ngân sách và nhu cầu không?"
        
        message = f"Dựa trên nhu cầu của bạn, tôi gợi ý:\n\n"
        message += f"🌟 {products[0]['name']}\n"
        message += f"💰 Giá: {products[0]['price']:,}đ\n"
        message += f"📝 {products[0]['description']}\n\n"
        message += recommendations["reasoning"]
        message += "\n\nBạn muốn đặt hàng ngay không?"
        
        return message
