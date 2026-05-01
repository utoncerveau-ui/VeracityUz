import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]

print(f"Testing Key: {key[:10]}...")

for model in models:
    for version in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": "Salom, kimsan?"}]}]
        }
        print(f"Trying {model} ({version})...")
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                print(f"SUCCESS: {model} {version}")
                # print(res['candidates'][0]['content']['parts'][0]['text'])
                break
        except Exception as e:
            print(f"FAILED: {model} {version} - {e}")

