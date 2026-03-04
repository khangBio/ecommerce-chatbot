# test_search_api.py

import requests
import json

# URL API
BASE_URL = "http://localhost:8000"

def test_search(query, filters=None, conversation_id=None):
    """Test search API"""
    
    url = f"{BASE_URL}/search"
    
    payload = {
        "query": query,
        "filters": filters,
        "conversation_id": conversation_id
    }
    
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {query}")
    print(f"Filters: {filters}")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Success!")
            print(f"\nBot response:")
            print(result.get('response', 'No response'))
            
            print(f"\n📦 Products found: {len(result.get('products', []))}")
            for i, product in enumerate(result.get('products', [])[:3], 1):
                print(f"\n{i}. {product['name']}")
                print(f"   💰 {product['price']:,}đ")
                print(f"   📝 {product['description'][:80]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

# Run tests
if __name__ == "__main__":
    
    # Test 1: Tìm kiếm cơ bản
    test_search("Tôi muốn mua điện thoại")
    
    # Test 2: Tìm kiếm với giá
    test_search(
        "laptop cho sinh viên",
        filters={
            "price_max": 30000000,
            "category": "Laptop"
        }
    )
    
    # Test 3: Tìm tai nghe
    test_search(
        "tai nghe chống ồn",
        filters={
            "price_min": 5000000,
            "price_max": 10000000
        }
    )
    
    # Test 4: Tìm theo brand
    test_search("sản phẩm Apple")
    
    # Test 5: Tìm sản phẩm cao cấp
    test_search(
        "sản phẩm cao cấp",
        filters={
            "price_min": 25000000
        }
    )
