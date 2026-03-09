# backend/database_setup.py
"""
Script để setup MongoDB và import dữ liệu sản phẩm
Chạy: python database_setup.py
"""
import certifi
import json
import base64
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv() # Load biến môi trường từ file .env

# ===== CẤU HÌNH MONGODB =====
# MONGO_URI = "mongodb://localhost:27017/"
# Lấy URI từ .env, nếu không có thì fallback về localhost
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "ecommerce"
COLLECTION_NAME = "products"

# ===== HÀM KẾT NỐI MONGODB =====
def connect_mongodb():
    """Kết nối đến MongoDB"""
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        # Test kết nối
        client.admin.command('ping')
        print(" Kết nối MongoDB thành công!")
        return client
    except ConnectionFailure:
        print(" Không thể kết nối MongoDB. Hãy đảm bảo MongoDB đang chạy!")
        print("   - Cài đặt MongoDB: https://www.mongodb.com/try/download/community")
        print("   - Khởi động: mongod (trên Windows) hoặc brew services start mongodb-community (macOS)")
        return None

# ===== HÀM TẠO DỮ LIỆU FAKE VỚI HÌNH ẢNH BASE64 =====
def create_fake_image_base64(product_name):
    """
    Tạo fake base64 image cho demo
    Trong thực tế, bạn sẽ đọc từ file thật
    """
    # Tạo một hình ảnh đơn giản 100x100 pixels màu ngẫu nhiên
    from PIL import Image, ImageDraw
    import io

    # Tạo ảnh
    img = Image.new('RGB', (100, 100), color=(200, 200, 255))
    draw = ImageDraw.Draw(img)

    # Vẽ text tên sản phẩm
    text = product_name[:10]  # Giới hạn 10 ký tự
    draw.text((10, 40), text, fill=(0, 0, 0))

    # Chuyển sang base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return f"data:image/png;base64,{img_base64}"

# ===== HÀM IMPORT DỮ LIỆU =====
def import_products_data():
    """Import dữ liệu sản phẩm từ products.json"""

    # Kết nối DB
    client = connect_mongodb()
    if not client:
        return

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Xóa dữ liệu cũ (optional)
    collection.drop()
    print("🗑️ Đã xóa collection cũ")

    # Đọc dữ liệu từ products.json
    products_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.json')

    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {products_file}")
        return

    # Thêm trường image_base64 và emoji
    emoji_map = {
        "Điện thoại": "📱",
        "Laptop": "💻",
        "Máy tính bảng": "📟",
        "Tai nghe": "🎧"
    }

    products_to_insert = []
    for product in products_data:
        # Thêm emoji dựa trên category
        emoji = emoji_map.get(product.get('category', ''), '📦')

        # Tạo fake image base64
        image_base64 = create_fake_image_base64(product['name'])

        # Chuẩn bị document
        product_doc = {
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "description": product["description"],
            "rating": product["rating"],
            "stock": product["stock"],
            "emoji": emoji,
            "image_base64": image_base64,  # Hình ảnh dạng base64
            "created_at": {"$date": "2024-01-01T00:00:00Z"}  # Timestamp
        }

        products_to_insert.append(product_doc)

    # Insert vào MongoDB
    if products_to_insert:
        result = collection.insert_many(products_to_insert)
        print(f"✅ Đã insert {len(result.inserted_ids)} sản phẩm vào MongoDB!")

        # Hiển thị sample
        sample = collection.find_one()
        print("\n📋 Sample document:")
        print(f"   ID: {sample['id']}")
        print(f"   Name: {sample['name']}")
        print(f"   Price: {sample['price']:,}đ")
        print(f"   Image Base64 length: {len(sample['image_base64'])} chars")

    # Tạo index cho tìm kiếm
    collection.create_index("id", unique=True)
    collection.create_index("name")
    collection.create_index("category")
    collection.create_index([("name", "text"), ("description", "text")])
    print("✅ Đã tạo indexes cho tìm kiếm")

    client.close()
    print("🔌 Đã đóng kết nối MongoDB")

# ===== HÀM HIỂN THỊ DỮ LIỆU =====
def show_products():
    """Hiển thị tất cả sản phẩm trong DB"""
    client = connect_mongodb()
    if not client:
        return

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    products = list(collection.find({}, {"_id": 0, "image_base64": 0}))  # Ẩn base64 để gọn

    print(f"\n📦 Tất cả sản phẩm ({len(products)}):")
    for p in products:
        print(f"   {p['emoji']} {p['name']} - {p['price']:,}đ (Stock: {p['stock']})")

    client.close()

# ===== HÀM TÌM KIẾM SẢN PHẨM =====
def search_products(query):
    """Tìm kiếm sản phẩm theo text"""
    client = connect_mongodb()
    if not client:
        return

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Tìm kiếm full-text
    results = list(collection.find(
        {"$text": {"$search": query}},
        {"_id": 0, "image_base64": 0}
    ).limit(5))

    print(f"\n🔍 Kết quả tìm kiếm '{query}':")
    for p in results:
        print(f"   {p['emoji']} {p['name']} - {p['price']:,}đ")

    client.close()

# ===== MAIN =====
if __name__ == "__main__":
    print("🚀 MongoDB Setup Script")
    print("=" * 50)

    # Import dữ liệu
    import_products_data()

    # Hiển thị dữ liệu
    show_products()

    # Demo tìm kiếm
    search_products("iPhone")

    print("\n✨ Hoàn thành! Bạn có thể sử dụng MongoDB trong ứng dụng của mình.")