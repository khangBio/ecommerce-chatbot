# backend/recommendation.py
import json
from typing import List, Dict
import random

class RecommendationEngine:
    """
    Tư vấn mua hàng tự động
    Gợi ý sản phẩm dựa trên preferences và lịch sử
    """
    
    def __init__(self):
        with open("../data/products.json", "r", encoding="utf-8") as f:
            self.products = json.load(f)
        self.user_profiles = {}
    
    def get_recommendations(self, user_id: str, preferences: dict, 
                          conversation_history: dict = None) -> dict:
        """
        Generate product recommendations
        """
        # Extract preferences from conversation
        budget = preferences.get("budget")
        category = preferences.get("category")
        features = preferences.get("features", [])
        
        # Filter products
        candidates = []
        for product in self.products:
            score = self._calculate_score(product, preferences)
            if score > 0:
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
            "reasoning": self._generate_reasoning(recommendations[0], preferences)
        }
    
    def _calculate_score(self, product: dict, preferences: dict) -> float:
        """Calculate relevance score"""
        score = 0.0
        
        # Budget matching
        if "budget" in preferences:
            budget = preferences["budget"]
            if product["price"] <= budget:
                score += 5.0
                # Bonus for value-for-money
                if product["price"] < budget * 0.8:
                    score += 2.0
            else:
                return 0  # Out of budget
        
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
