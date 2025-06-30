import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

# Test connection
try:
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hello"}]
    )
    
    print("✅ Success! Claude API is working")
    print(f"Response: {message.content[0].text}")
    
except Exception as e:
    print(f"❌ Error: {e}")