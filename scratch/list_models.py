import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"

try:
    with urllib.request.urlopen(url) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        for model in res.get('models', []):
            print(model['name'])
except Exception as e:
    print(f"Error: {e}")
