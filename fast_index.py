import pandas as pd
from vector_store import SimpleVectorStore
import os
import json
import urllib.request
import time
from dotenv import load_dotenv

load_dotenv()

def get_embedding(text, key):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={key}"
        payload = {"model": "models/gemini-embedding-001", "content": {"parts": [{"text": text}]}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res['embedding']['values']
    except Exception as e:
        print(f"E", end="", flush=True)
        return None

def main():
    key = os.getenv("GEMINI_API_KEY")
    df = pd.read_csv("dataset_uzbek.csv").dropna(subset=['content_uz', 'label']).head(100)
    
    docs, metadatas, ids, embs = [], [], [], []
    print(f"Indexing 100 docs semantically...")
    
    for idx, row in df.iterrows():
        text = row['content_uz'][:500] # Cap length
        emb = get_embedding(text, key)
        if emb:
            docs.append(text)
            metadatas.append({"label": "REAL" if row['label'] == 1 else "FAKE"})
            ids.append(f"fast_{idx}")
            embs.append(emb)
            print(".", end="", flush=True)
        time.sleep(0.4)

    store = SimpleVectorStore(storage_path="uzbek_news_vectors.pkl")
    store.documents, store.metadatas, store.ids, store.embeddings = docs, metadatas, ids, embs
    store.save()
    print("\nSemantic Index Ready!")

if __name__ == "__main__":
    main()
