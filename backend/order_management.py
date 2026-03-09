# backend/order_management.py
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from models.order import OrderModel

class OrderManager:
    """
    Hỗ trợ sau bán hàng
    - Theo dõi đơn hàng
    - Xử lý khiếu nại và đổi trả
    - Troubleshooting
    """
    
    def __init__(self):
        # Kết nối DB thay vì dùng dictionary lưu tạm
        self.order_model = OrderModel()
        self.order_model.connect()
        self.return_requests = {}
        
    def create_order(self, order_data: dict) -> dict:
        """Tự động tạo đơn hàng và lưu vào MongoDB"""
        order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
        
        order = {
            "order_id": order_id,
            "user_id": order_data["user_id"],
            "products": order_data["products"],
            "total": order_data["total"],
            "customer_info": order_data.get("customer_info", {}),
            "payment_method": order_data.get("payment_method", "COD"),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_delivery": (datetime.now() + timedelta(days=3)).isoformat(),
            "tracking_number": f"TRK{uuid.uuid4().hex[:10].upper()}",
            "tracking_events": [
                {"status": "Đơn hàng đã được tạo thành công", "time": datetime.now().isoformat()}
            ]
        }
        
        # Lưu vào MongoDB
        self.order_model.create_order(order)
        
        if '_id' in order:
            del order['_id']

        return order
    
    def track_order(self, order_id: str) -> Optional[Dict]:
        """
        Theo dõi đơn hàng real-time từ MongoDB
        """
        # Lấy từ DB
        order = self.order_model.get_order_by_id(order_id)
        
        if not order:
            return None
        
        # Mock tracking status (Giả lập vận chuyển đơn hàng để demo)
        statuses = ["pending", "confirmed", "shipping", "delivered"]
        current_status = order["status"]
        
        status_index = statuses.index(current_status) if current_status in statuses else 0
        if status_index < len(statuses) - 1:
            new_status = statuses[status_index + 1]
            order["status"] = new_status
            
            # Thêm event vận chuyển mới
            event_msg = self._translate_status(new_status)
            new_event = {"status": event_msg, "time": datetime.now().isoformat()}
            
            if "tracking_events" not in order:
                order["tracking_events"] = []
            order["tracking_events"].append(new_event)
            
            # Cập nhật ngược lại vào MongoDB
            self.order_model.update_order(order_id, {
                "status": new_status,
                "tracking_events": order["tracking_events"]
            })
        
        return order
        
    def get_user_orders(self, user_id: str) -> List[Dict]:
        """Lấy danh sách đơn hàng của user"""
        return self.order_model.get_orders_by_user(user_id)
    
    def format_tracking_info(self, order: dict) -> str:
        """Format tracking info as conversational message"""
        if not order:
            return "Không tìm thấy đơn hàng. Vui lòng kiểm tra lại mã đơn hàng."
        
        message = f"📦 Thông tin đơn hàng #{order['order_id']}\n\n"
        message += f"Trạng thái: {self._translate_status(order['status'])}\n"
        message += f"Mã vận đơn: {order['tracking_number']}\n"
        message += f"Dự kiến giao: {order['estimated_delivery'][:10]}\n\n"
        message += "Lịch sử vận chuyển:\n"
        
        for event in order.get("tracking_events", []):
            message += f"• {event['status']} - {event['time'][:16]}\n"
        
        return message
    
    # ... (Giữ nguyên các hàm handle_return_request, troubleshoot, _translate_status như cũ) ...
    def handle_return_request(self, user_id: str, reason: str, order_id: str = None) -> dict:
        if not order_id:
            return {"status": "need_order_id", "message": "Vui lòng cung cấp mã đơn hàng để tôi kiểm tra điều kiện đổi trả."}
        
        order = self.order_model.get_order_by_id(order_id)
        if not order:
            return {"status": "order_not_found", "message": "Không tìm thấy đơn hàng."}
            
        order_date = datetime.fromisoformat(order["created_at"])
        days_since_order = (datetime.now() - order_date).days
        if days_since_order > 7:
            return {"status": "not_eligible", "message": "Đơn hàng đã quá thời gian đổi trả (7 ngày). Vui lòng liên hệ hotline để được hỗ trợ."}
            
        return_id = f"RET{uuid.uuid4().hex[:8].upper()}"
        self.return_requests[return_id] = {
            "return_id": return_id, "order_id": order_id, "user_id": user_id,
            "reason": reason, "status": "pending", "created_at": datetime.now().isoformat()
        }
        return {"status": "success", "return_id": return_id, "message": f"Yêu cầu đổi trả #{return_id} đã được tạo.\n\nQuy trình:\n1. Đóng gói sản phẩm theo đúng tình trạng ban đầu\n2. Chụp ảnh sản phẩm và gửi cho tôi\n3. Shipper sẽ đến lấy hàng trong 24h\n4. Hoàn tiền sau 3-5 ngày làm việc\n\nBạn có thể chụp ảnh sản phẩm ngay không?"}

    def troubleshoot(self, product_name: str, issue: str) -> str:
        troubleshooting_guide = {
            "không bật được": ["1. Kiểm tra xem đã cắm sạc đúng cách chưa", "2. Thử nút nguồn trong 10 giây", "3. Kiểm tra đèn báo nguồn", "Nếu vẫn không được, vui lòng gửi video cho tôi."],
            "lỗi kết nối": ["1. Tắt và bật lại Bluetooth/WiFi", "2. Xóa thiết bị và kết nối lại", "3. Khởi động lại thiết bị", "4. Cập nhật phần mềm mới nhất"],
            "màn hình bị đen": ["1. Kiểm tra độ sáng màn hình", "2. Khởi động lại thiết bị", "3. Kiểm tra cáp kết nối (nếu có)", "Nếu vẫn lỗi, có thể cần bảo hành phần cứng."]
        }
        for key, steps in troubleshooting_guide.items():
            if key in issue.lower():
                response = f"Hướng dẫn xử lý '{key}' cho {product_name}:\n\n"
                response += "\n".join(steps)
                response += "\n\nBạn đã thử các bước trên chưa?"
                return response
        return (f"Tôi hiểu bạn gặp vấn đề với {product_name}. Để hỗ trợ tốt nhất, bạn có thể:\n1. Mô tả chi tiết vấn đề\n2. Gửi ảnh/video minh họa\n3. Hoặc kết nối với chuyên viên kỹ thuật\n\nBạn muốn làm gì?")

    def _translate_status(self, status: str) -> str:
        status_map = {
            "pending": "Chờ xác nhận",
            "confirmed": "Đã xác nhận",
            "shipping": "Đang giao hàng",
            "delivered": "Đã giao hàng",
            "cancelled": "Đã hủy"
        }
        return status_map.get(status, status)