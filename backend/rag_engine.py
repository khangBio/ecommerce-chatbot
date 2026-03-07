import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import json
import re

class RAGEngine:
    """Hỗ trợ khách hàng bằng NLP và LLM - Gemini version"""
    
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        genai.configure(api_key=gemini_key)
        
        # Thử các model theo thứ tự ưu tiên
        models_to_try = [
            'models/gemini-2.5-flash'
        ]
        
        self.model = None
        for model_name in models_to_try:
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test model
                test_response = self.model.generate_content("Hi")
                print(f"✅ Using Gemini model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} not available: {e}")
                continue
        
        if not self.model:
            raise ValueError("No Gemini model available. Check your API key.")
        
        # Load embeddings
        print("Loading embeddings...")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        self.vectorstore = None
        self.memory = {}
        
        try:
            self._load_knowledge_base()
        except Exception as e:
            print(f"Warning: {e}")
            self.vectorstore = None
    
    def _load_knowledge_base(self):
        faq_path = os.path.join(os.path.dirname(__file__), "..", "data", "faq.txt")
        
        try:
            with open(faq_path, "r", encoding="utf-8") as f:
                faq_text = f.read()
        except FileNotFoundError:
            faq_text = "Chính sách bảo hành: 12 tháng. Đổi trả: 7 ngày."
            os.makedirs(os.path.dirname(faq_path), exist_ok=True)
            with open(faq_path, "w", encoding="utf-8") as f:
                f.write(faq_text)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_text(faq_text)
        
        self.vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=self.embeddings
        )
        print("✅ Knowledge base loaded with Gemini")
    
    def classify_intent(self, message: str) -> dict:
        """Phân loại ý định bằng Gemini"""
        prompt = f"""Phân loại ý định người dùng vào 1 trong các loại:
        - product_search, product_recommendation, order_tracking, 
          return_request, technical_support, general_inquiry
        
        Tin nhắn: "{message}"
        
        Trả về JSON format: {{"intent": "...", "entities": {{}}}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
        except Exception as e:
            print(f"Intent error: {e}")
            result = {"intent": "general_inquiry", "entities": {}}
        
        return result
    
    def generate_response(self, query: str, conversation_id: str = None) -> str:
        """Sinh câu trả lời bằng Gemini"""
        try:
            context = ""
            if self.vectorstore:
                docs = self.vectorstore.similarity_search(query, k=3)
                context = "\n".join([d.page_content for d in docs])
            
            prompt = f"""Bạn là trợ lý ảo thương mại chuyên nghiệp.
            
            Kiến thức có sẵn:
            {context}
            
            Câu hỏi khách hàng: {query}
            
            Hãy trả lời ngắn gọn, hữu ích và thân thiện bằng tiếng Việt.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"Error: {e}")
            return "Xin lỗi, tôi gặp vấn đề kỹ thuật."
