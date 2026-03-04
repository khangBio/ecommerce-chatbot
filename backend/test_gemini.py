# check_gemini_models.py

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {api_key[:20]}...")
genai.configure(api_key=api_key)

print("\n" + "="*60)
print("AVAILABLE GEMINI MODELS")
print("="*60 + "\n")

available_models = []

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            available_models.append(model.name)
            print(f"✅ {model.name}")
            print(f"   Display: {model.display_name}")
            print(f"   Input limit: {model.input_token_limit} tokens")
            print(f"   Output limit: {model.output_token_limit} tokens")
            print()
except Exception as e:
    print(f"❌ Error listing models: {e}")
    exit(1)

print("="*60)
print(f"Total models: {len(available_models)}")
print("="*60)

# Test first model
if available_models:
    test_model_name = available_models[0]
    print(f"\n🧪 Testing model: {test_model_name}")
    
    try:
        model = genai.GenerativeModel(test_model_name)
        response = model.generate_content("Xin chào bằng tiếng Việt")
        print(f"✅ Test successful!")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
else:
    print("❌ No models available")
