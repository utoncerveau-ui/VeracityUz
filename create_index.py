import pandas as pd
from vector_store import SimpleVectorStore
import os
import json
import urllib.request
from tqdm import tqdm
import time
from dotenv import load_dotenv

load_dotenv()

def get_embedding(text, key):
    """Calls Google Gemini Embedding API."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={key}"
        payload = {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": text}]}
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res['embedding']['values']
    except Exception as e:
        print(f"\nError embedding text: {e}")
        return None

def main():
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return

    # 1. Load dataset
    print("Loading dataset_uzbek.csv...")
    try:
        df = pd.read_csv("dataset_uzbek.csv")
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return

    df = df.dropna(subset=['content_uz', 'label'])
    # For semantic RAG, we don't need thousands of tiny chunks if they are redundant.
    # But let's keep the chunking logic for better granularity.
    
    def chunk_text(text, max_sentences=3):
        import re
        sentences = re.split(r'(?<=[.!?])\s+', str(text).strip())
        chunks = []
        for i in range(0, len(sentences), max_sentences):
            chunk = ' '.join(sentences[i:i+max_sentences])
            if len(chunk) > 40: # Filter out very short noise
                chunks.append(chunk)
        return chunks

    all_docs = []
    all_metadatas = []
    all_ids = []

    print("Preparing documents...")
    for idx, row in df.iterrows():
        chunks = chunk_text(row['content_uz'])
        label_str = "REAL" if int(row['label']) == 1 else "FAKE"
        for c_idx, chunk in enumerate(chunks):
            all_docs.append(chunk)
            all_metadatas.append({"source": "dataset_uzbek", "label": label_str})
            all_ids.append(f"doc_{idx}_c_{c_idx}")

    # To save time and API quota, let's limit the index size for this demonstration
    # or just process them in batches. 
    # Let's take the first 500 high-quality chunks to ensure we don't hit 429 too fast.
    MAX_CHUNKS = 600 
    selected_docs = all_docs[:MAX_CHUNKS]
    selected_meta = all_metadatas[:MAX_CHUNKS]
    selected_ids = all_ids[:MAX_CHUNKS]

    print(f"Indexing {len(selected_docs)} chunks using Google Semantic Embeddings...")
    
    embeddings = []
    for i, doc in enumerate(tqdm(selected_docs)):
        emb = get_embedding(doc, gemini_key)
        if emb:
            embeddings.append(emb)
        else:
            embeddings.append([0.0] * 768)
        
        # Incremental Save
        if (i + 1) % 50 == 0:
            collection = SimpleVectorStore(storage_path="uzbek_news_vectors.pkl")
            collection.documents = selected_docs[:i+1]
            collection.embeddings = embeddings
            collection.metadatas = selected_meta[:i+1]
            collection.ids = selected_ids[:i+1]
            collection.save()
            
        time.sleep(0.5)

    # 2. Setup and Save Vector Store
    collection = SimpleVectorStore(storage_path="uzbek_news_vectors.pkl")
    collection.documents = selected_docs
    collection.embeddings = embeddings
    collection.metadatas = selected_meta
    collection.ids = selected_ids
    collection.save()

    print(f"\n--- SUCCESS ---")
    print(f"Created Semantic Index with {len(selected_docs)} items.")

if __name__ == "__main__":
    main()
