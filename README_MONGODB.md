# E-commerce Chatbot với MongoDB

## Setup MongoDB

### 1. Cài đặt MongoDB

### 2. Khởi động MongoDB

### 3. Cài đặt dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Setup dữ liệu MongoDB
```bash
# Import dữ liệu từ products.json vào MongoDB
python database_setup.py
```

### 5. Cấu hình environment
Tạo file `.env`:
```env
MONGO_URI=mongodb://localhost:27017/
GOOGLE_API_KEY=google_api_key_here
```

### 6. Chạy ứng dụng
```bash
# Backend
python app.py

# Frontend (mở file index.html trong browser)
```

## Cấu trúc Database MongoDB

### Database: `ecommerce`
### Collection: `products`

**Schema mẫu:**
```json
{
  "id": "PRD001",
  "name": "iPhone 15 Pro Max",
  "category": "Điện thoại",
  "price": 29990000,
  "description": "Smartphone cao cấp...",
  "rating": 4.8,
  "stock": 50,
  "emoji": "📱",
  "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## API Endpoints

- `GET /` - Health check
- `POST /chat` - Chat với bot
- `POST /search` - Tìm kiếm sản phẩm
- `GET /orders/{order_id}` - Tra cứu đơn hàng
- `POST /orders` - Tạo đơn hàng

## Scripts

### Import dữ liệu
```bash
python backend/database_setup.py
```

### Test kết nối MongoDB
```python
from models.product import ProductModel

model = ProductModel()
if model.connect():
    products = model.get_all_products(5)
    print(f"Found {len(products)} products")
    model.disconnect()
```

### Tìm kiếm sản phẩm
```python
from models.product import ProductModel

model = ProductModel()
model.connect()
results = model.search_products("iPhone")
print(results)
model.disconnect()
```

## Lưu ý

- **MongoDB không cần tạo bảng** - Collections tự động tạo khi insert
- **Base64 images**: Hình ảnh được lưu dưới dạng base64 string trong document
- **Indexes**: Tự động tạo cho `id` (unique), `name`, `category`, và full-text search
- **Vector search**: Sử dụng FAISS cho semantic search

## Troubleshooting

### Lỗi kết nối MongoDB
```bash
# Kiểm tra MongoDB chạy
ps aux | grep mongod

# Restart MongoDB
brew services restart mongodb-community
```

### Lỗi API key
```bash
# Thêm GOOGLE_API_KEY vào .env
echo "GOOGLE_API_KEY=your_key_here" >> .env
```