import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GOOGLE_API_KEY")

if key:
    print(f"✅ Success! Key found: {key[:5]}...")
else:
    print("❌ Error: GOOGLE_API_KEY not found in .env file.")