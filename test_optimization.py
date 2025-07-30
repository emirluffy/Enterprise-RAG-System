import requests
import json

# Test response optimization
url = "http://localhost:8002/api/v1/chat/query"
headers = {"Content-Type": "application/json"}
data = {
    "question": "fx emirleri nasıl verilir?",
    "conversation_id": "test-optimization-direct"
}

print("🧪 Testing Response Optimization...")
print(f"📞 Sending request to: {url}")
print(f"📝 Question: {data['question']}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Response received!")
        print(f"📏 Answer length: {len(result.get('answer', ''))}")
        
        # Check optimization metadata
        optimization = result.get('response_optimization', {})
        print(f"🤖 Optimization applied: {optimization.get('applied', False)}")
        
        if optimization.get('applied'):
            print(f"📊 Clarity score: {optimization.get('clarity_score', 'N/A')}")
            print(f"⚡ Optimization score: {optimization.get('optimization_score', 'N/A')}")
            print(f"🕒 Processing time: {optimization.get('processing_time_ms', 'N/A')}ms")
            print(f"🧹 Duplicates removed: {optimization.get('duplicates_removed', 'N/A')}")
        else:
            print(f"❌ Reason: {optimization.get('reason', 'N/A')}")
            print(f"⚠️ Error: {optimization.get('error', 'N/A')}")
        
        print("\n" + "="*50)
        print("📝 OPTIMIZED ANSWER:")
        print("="*50)
        print(result.get('answer', 'No answer'))
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}") 