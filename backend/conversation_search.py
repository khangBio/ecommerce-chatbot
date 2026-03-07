# backend/conversation_search.py - GEMINI VERSION

from langchain_community.vectorstores import FAISS  # Thay Chroma bằng FAISS
#from langchain_community.embeddings import HuggingFaceEmbeddings  # Embeddings miễn phí
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import uuid
import os
from datetime import datetime

class ConversationalSearch:
    """
    Tìm kiếm hội thoại - Conversational Search
    Tìm kiếm sản phẩm bằng ngôn ngữ tự nhiên với ngữ cảnh
    VERSION: Gemini + FAISS (MIỄN PHÍ)
    """
    
    def __init__(self):
        # Sử dụng HuggingFace Embeddings (miễn phí, chạy local)
        print("🔄 Loading embeddings model for product search...")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        self.product_vectorstore = None
        self.conversations = {}
        
        # Load product catalog
        self._load_products()
    
    def _load_products(self):
        """Load và vectorize product catalog"""
        # Đường dẫn linh hoạt
        products_path = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")
        
        try:
            with open(products_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except FileNotFoundError:
            print("⚠️ File products.json không tồn tại. Đang tạo dữ liệu mẫu...")
            
            # Tạo sample products
            products = [
                {
                    "id": "PRD001",
                    "name": "iPhone 15 Pro Max",
                    "category": "Điện thoại",
                    "price": 29990000,
                    "description": "Smartphone cao cấp với chip A17 Pro, camera 48MP, màn hình Super Retina XDR",
                    "rating": 4.8,
                    "stock": 50
                },
                {
                    "id": "PRD002",
                    "name": "Samsung Galaxy S24 Ultra",
                    "category": "Điện thoại",
                    "price": 27990000,
                    "description": "Flagship Android với bút S Pen, camera 200MP, chip Snapdragon 8 Gen 3",
                    "rating": 4.7,
                    "stock": 40
                },
                {
                    "id": "PRD003",
                    "name": "MacBook Air M3",
                    "category": "Laptop",
                    "price": 28990000,
                    "description": "Laptop mỏng nhẹ với chip M3, pin 18 giờ, màn hình Liquid Retina",
                    "rating": 4.9,
                    "stock": 30
                },
                {
                    "id": "PRD004",
                    "name": "AirPods Pro 2",
                    "category": "Tai nghe",
                    "price": 5990000,
                    "description": "Tai nghe chống ồn chủ động, âm thanh không gian, chuẩn MagSafe",
                    "rating": 4.6,
                    "stock": 100
                },
                {
                    "id": "PRD005",
                    "name": "iPad Pro 12.9 inch M2",
                    "category": "Máy tính bảng",
                    "price": 32990000,
                    "description": "Máy tính bảng cao cấp với màn hình Liquid Retina XDR, chip M2",
                    "rating": 4.8,
                    "stock": 25
                },
                {
                    "id": "PRD006",
                    "name": "Dell XPS 15",
                    "category": "Laptop",
                    "price": 35990000,
                    "description": "Laptop cao cấp Intel Core i7, RAM 16GB, màn hình 4K OLED",
                    "rating": 4.7,
                    "stock": 20
                },
                {
                    "id": "PRD007",
                    "name": "Sony WH-1000XM5",
                    "category": "Tai nghe",
                    "price": 8990000,
                    "description": "Tai nghe over-ear chống ồn hàng đầu, âm thanh Hi-Res",
                    "rating": 4.9,
                    "stock": 60
                }
            ]
            
            # Tạo thư mục và lưu file
            os.makedirs(os.path.dirname(products_path), exist_ok=True)
            with open(products_path, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Đã tạo file: {products_path}")
        
        # Create product descriptions for embedding
        product_texts = []
        product_metadata = []
        
        for product in products:
            # Tạo text mô tả đầy đủ cho embedding
            text = f"{product['name']} {product['category']} {product['description']} giá {product['price']:,}đ"
            product_texts.append(text)
            product_metadata.append(product)
        
        # Create FAISS vector store (thay Chroma)
        # FAISS nhẹ hơn, không cần persist_directory
        print("🔄 Creating product vector store...")
        self.product_vectorstore = FAISS.from_texts(
            texts=product_texts,
            embedding=self.embeddings,
            metadatas=product_metadata
        )
        
        print(f"✅ Đã load {len(products)} sản phẩm vào vector store")
    
    def search(self, query: str, filters: dict = None, conversation_id: str = None) -> dict:
        """
        Tìm kiếm sản phẩm với context retention
        """
        # Get conversation context
        context = self.get_context(conversation_id) if conversation_id else {}
        
        # Enhance query with context
        enhanced_query = self._enhance_query(query, context)
        
        # Apply filters from previous conversation
        if context.get("filters"):
            filters = {**context.get("filters", {}), **(filters or {})}
        
        # Semantic search với FAISS
        results = self.product_vectorstore.similarity_search(
            enhanced_query,
            k=5  # Lấy top 5 sản phẩm
        )
        
        # Filter results
        products = []
        for doc in results:
            product = doc.metadata
            if self._apply_filters(product, filters):
                products.append(product)
        
        # Generate conversational response
        response = self._generate_search_response(products, query, context)
        
        return {
            "products": products[:5],
            "response": response,
            "query": enhanced_query
        }
    
    def _enhance_query(self, query: str, context: dict) -> str:
        """
        Bổ sung query với context từ hội thoại trước
        """
        if not context:
            return query
        
        enhanced = query
        
        # Add previous preferences
        if context.get("category"):
            enhanced = f"{enhanced} {context['category']}"
        
        if context.get("price_range"):
            enhanced = f"{enhanced} giá {context['price_range']}"
        
        # Add previous brand preference
        if context.get("brand"):
            enhanced = f"{enhanced} {context['brand']}"
        
        return enhanced
    
    def _apply_filters(self, product: dict, filters: dict) -> bool:
        """Apply filters to product"""
        if not filters:
            return True
        
        # Price filters
        if "price_min" in filters and product["price"] < filters["price_min"]:
            return False
        
        if "price_max" in filters and product["price"] > filters["price_max"]:
            return False
        
        # Category filter
        if "category" in filters and product["category"] != filters["category"]:
            return False
        
        # Stock filter
        if filters.get("in_stock_only") and product.get("stock", 0) <= 0:
            return False
        
        # Rating filter
        if "min_rating" in filters and product.get("rating", 0) < filters["min_rating"]:
            return False
        
        return True
    
    def _generate_search_response(self, products: list, query: str, context: dict) -> str:
        """Generate natural language response"""
        if not products:
            return "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp. Bạn có thể mô tả cụ thể hơn không?"
        
        # Tạo response tự nhiên
        response = f"Tôi tìm thấy {len(products)} sản phẩm phù hợp cho bạn:\n\n"
        
        # Hiển thị top 3 sản phẩm
        for i, product in enumerate(products[:3], 1):
            response += f"{i}. **{product['name']}**\n"
            response += f"   💰 Giá: {product['price']:,}đ\n"
            response += f"   📝 {product['description']}\n"
            
            # Thêm thông tin rating và stock
            if product.get('rating'):
                response += f"   ⭐ Đánh giá: {product['rating']}/5\n"
            if product.get('stock'):
                response += f"   📦 Còn hàng: {product['stock']} sản phẩm\n"
            
            response += "\n"
        
        # Gợi ý hành động tiếp theo
        if len(products) > 3:
            response += f"Và còn {len(products) - 3} sản phẩm khác.\n\n"
        
        response += "Bạn muốn xem chi tiết sản phẩm nào? 😊"
        
        return response
    
    def save_context(self, conversation_id: str, user_message: str, 
                    bot_message: str, intent: str) -> str:
        """Save conversation context"""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "messages": [],
                "filters": {},
                "created_at": datetime.now()
            }
        
        # Lưu message
        self.conversations[conversation_id]["messages"].append({
            "user": user_message,
            "bot": bot_message,
            "intent": intent,
            "timestamp": datetime.now()
        })
        
        # Extract và lưu filters từ message (có thể mở rộng)
        self._extract_filters_from_message(conversation_id, user_message)
        
        return conversation_id
    
    def _extract_filters_from_message(self, conversation_id: str, message: str):
        """Trích xuất filters từ message và lưu vào context"""
        message_lower = message.lower()
        
        # Extract category
        categories = ["điện thoại", "laptop", "tai nghe", "máy tính bảng"]
        for cat in categories:
            if cat in message_lower:
                self.conversations[conversation_id]["filters"]["category"] = cat.title()
                break
        
        # Extract price range (đơn giản)
        if "dưới" in message_lower or "dưới" in message_lower:
            # Có thể parse số từ message
            pass
    
    def get_context(self, conversation_id: str) -> dict:
        """Retrieve conversation context"""
        return self.conversations.get(conversation_id, {})
    
    def clear_context(self, conversation_id: str):
        """Clear conversation context"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_product_by_id(self, product_id: str) -> dict:
        """Lấy thông tin chi tiết sản phẩm theo ID"""
        # Search trong vector store bằng ID
        results = self.product_vectorstore.similarity_search(
            product_id,
            k=10
        )
        
        for doc in results:
            if doc.metadata.get("id") == product_id:
                return doc.metadata
        
        return None
