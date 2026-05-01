import httpx
import asyncio
import time
import os
import hashlib
import json
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from vector_store import SimpleVectorStore
import pickle
import numpy as np
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = FastAPI(title="Veracity Uz API (RAG Version)")

# --- RATE LIMITING ---
rate_limit_store: Dict[str, List[float]] = {}
def check_rate_limit(ip: str):
    now = time.time()
    if ip not in rate_limit_store:
        rate_limit_store[ip] = []
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < 60]
    if len(rate_limit_store[ip]) >= 10:
        raise HTTPException(status_code=429, detail="Too Many Requests. Limit exceeded. Please wait a minute.")
    rate_limit_store[ip].append(now)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    text: str

class VerifyRequest(BaseModel):
    text: str

# --- LINGUISTIC NORMALIZATION ---
def normalize_uzbek(text: str) -> str:
    mapping = { "o'": "ў", "O'": "Ў", "o`": "ў", "O`": "Ў", "g'": "ғ", "G'": "Ғ", "g`": "ғ", "G`": "Ғ", "sh": "ш", "Sh": "Ш", "SH": "Ш", "ch": "ч", "Ch": "Ч", "CH": "Ч", "a": "а", "A": "А", "b": "б", "B": "Б", "d": "д", "D": "Д", "e": "е", "E": "Е", "f": "ф", "F": "Ф", "g": "г", "G": "Г", "h": "ҳ", "H": "Ҳ", "i": "и", "I": "И", "j": "ж", "J": "Ж", "k": "к", "K": "К", "l": "л", "L": "Л", "m": "м", "M": "М", "n": "н", "N": "Н", "o": "о", "O": "О", "p": "п", "P": "П", "q": "қ", "Q": "Қ", "r": "р", "R": "Р", "s": "с", "S": "С", "t": "т", "T": "Т", "u": "у", "U": "У", "v": "в", "V": "В", "x": "х", "X": "Х", "y": "й", "Y": "Й", "z": "з", "Z": "З", "o‘": "ў", "g‘": "ғ" }
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    result = str(text)
    for key in sorted_keys: result = result.replace(key, mapping[key])
    return result

def clean_text(text: str) -> str:
    normalized = normalize_uzbek(text)
    return re.sub(r'[^а-яА-ЯёЁқҚғҒҳҲчЧшШўЎ0-9\s]', '', normalized.lower())

def classify_input(text: str) -> str | None:
    words = text.strip().split()
    if len(words) < 4: return "NOT_NEWS"
    personal_keywords = ['men', 'mani', 'mening', 'ismim', 'salom', 'qalesiz', 'qalaysiz', 'siz', 'sizi', 'sizning', 'ман', 'мани', 'менинг', 'исмим', 'салом', 'қалайсиз', 'қалесиз', 'сиз', 'сизи', 'сизни']
    if any(word in text.lower() for word in personal_keywords) and len(words) < 7: return "NOT_NEWS"
    return None

# --- RAG Setup ---
vector_store = None
collection = None
tfidf_vectorizer = None

# Simple in-memory cache for LLM responses
llm_cache = {}

async def embedding_func(texts: List[str]) -> List[List[float]]:
    """Calls Google Gemini Embedding API asynchronously."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return [[0.0] * 768 for _ in texts]
        
    embeddings = []
    async with httpx.AsyncClient() as client:
        for text in texts:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={gemini_key}"
                payload = {
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": text}]}
                }
                resp = await client.post(url, json=payload, timeout=10.0)
                if resp.status_code == 200:
                    res = resp.json()
                    embeddings.append(res['embedding']['values'])
                else:
                    print(f"Embedding API error {resp.status_code}: {resp.text}")
                    embeddings.append([0.0] * 768)
            except Exception as e:
                print(f"Embedding error for text '{text[:20]}...': {e}")
                embeddings.append([0.0] * 768)
    return embeddings

@app.on_event("startup")
async def startup_event():
    global vector_store, collection, tfidf_vectorizer
    print("Initializing Vector Store & TF-IDF Vectorizer...")
    
    try:
        # Load local vectorizer (Fix #3)
        if os.path.exists("tfidf_vectorizer.pkl"):
            with open("tfidf_vectorizer.pkl", "rb") as f:
                tfidf_vectorizer = pickle.load(f)
            print("TF-IDF Vectorizer loaded successfully!")
        else:
            print("WARNING: tfidf_vectorizer.pkl not found. Please run create_index.py.")
    except Exception as e:
        print(f"Error loading TF-IDF vectorizer: {e}")

    try:
        collection = SimpleVectorStore(storage_path="uzbek_news_vectors.pkl")
        print(f"Vector Store loaded with {collection.count()} items.")
    except Exception as e:
        print(f"Error loading Vector Store: {e}")

async def ask_llm(context_texts: List[str], user_query: str):
    """
    Calls the LLM with the context and user query asynchronously.
    """
    global llm_cache
    
    cache_key = hashlib.md5((user_query + "".join(context_texts)).encode()).hexdigest()
    if cache_key in llm_cache:
        return llm_cache[cache_key]

    preferred_llm = os.getenv("PREFERRED_LLM", "mock").lower()
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    prompt = f"""Siz O'zbekistonda faktlarni tekshiruvchi mutaxassis (fact-checking expert)siz.
Taqdim etilgan dalillar asosida yangilikni tahlil qiling.

QADAMLAR:
1. Asosiy faktik DA'VOni aniqlang.
2. Uni berilgan dalillar bilan solishtiring.
3. Ziddiyatlar (contradictions) yoki tasdiqlarni toping.
4. Ishonchlilikni baholang.

HAQIQIY YANGILIKLAR DALILLARI (CONTEXT):
{chr(10).join(context_texts) if context_texts else 'Tegishli haqiqiy xabar topilmadi.'}

FOYDALANUVCHI XABARI: {user_query}

Javobni FAQAT quyidagi JSON formatida bering:
{{
  "verdict": "REAL" | "FAKE" | "UNCERTAIN",
  "claim": "Yangilikdagi asosiy faktik da'vo (bir jumla)",
  "analysis": {{
    "linguistic_signals": "Matndagi shubhali yoki ishonchli lingvistik belgilar (masalan, sensatsionallik)",
    "evidence_summary": "Dalillar qisqacha mazmuni",
    "contradictions": "Dalillar va xabar orasidagi ziddiyatlar (agar bo'lsa)",
    "supporting_points": "Xabarni qo'llab-quvvatlovchi dalillar (agar bo'lsa)"
  }},
  "final_explanation": "Yakuniy tushuntirish (xalqchil tilda)"
}}"""

    GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]

    async def call_gemini(p):
        async with httpx.AsyncClient() as client:
            for model in GEMINI_MODELS:
                for version in ["v1beta", "v1"]:
                    try:
                        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={gemini_key}"
                        payload = {
                            "contents": [{"parts": [{"text": p}]}],
                            "generationConfig": {"temperature": 0.1}
                        }
                        if version == "v1beta":
                            payload["generationConfig"]["response_mime_type"] = "application/json"

                        resp = await client.post(url, json=payload, timeout=20.0)
                        if resp.status_code == 200:
                            res = resp.json()
                            return res['candidates'][0]['content']['parts'][0]['text']
                        elif resp.status_code == 429:
                            await asyncio.sleep(1)
                    except Exception:
                        continue
        return None

    def parse_llm_json(raw):
        try:
            return json.loads(raw)
        except:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match: return json.loads(match.group(0))
        raise ValueError("No JSON found")

    try:
        raw_response = None
        if preferred_llm == "gemini" and gemini_key:
            raw_response = await call_gemini(prompt)
        
        if raw_response:
            data = parse_llm_json(raw_response)
            if "prediction" in data and "verdict" not in data:
                data["verdict"] = data["prediction"]
            llm_cache[cache_key] = data
            return data
    except Exception as e:
        print(f"LLM API error: {e}")

    return {
        "verdict": "REAL" if context_texts else "UNCERTAIN",
        "claim": user_query[:150] + "...",
        "analysis": {
            "linguistic_signals": "AI tahlil amalga oshmadi.",
            "evidence_summary": f"Ma'lumotlar bazasida {len(context_texts)} ta o'xshash xabar topildi." if context_texts else "Tegishli xabar topilmadi.",
            "contradictions": "Aniqlanmadi",
            "supporting_points": f"{len(context_texts)} ta haqiqiy xabar dalil sifatida ishlatildi." if context_texts else "Yo'q"
        },
        "final_explanation": "LLM javob bermadi. Bilimlar bazasi asosida tahlil yakunlandi."
    }

@app.post("/api/predict")
async def predict(request_data: PredictRequest, request: Request):
    check_rate_limit(request.client.host)
    user_input = request_data.text
    if not user_input or not user_input.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    not_news_reason = classify_input(user_input)
    if not_news_reason:
        return {
            "prediction": "NOT_NEWS",
            "confidence": 0.0,
            "explanation": "Bu matn yangilik xabariga o'xshamaydi.",
            "sources": []
        }

    # 1. Retrieve & Poll RSS concurrently
    try:
        # Parallelize RAG and RSS
        query_embeddings_task = embedding_func([user_input])
        rss_task = poll_rss_feeds(user_input)
        
        query_embeddings, rss_sources = await asyncio.gather(query_embeddings_task, rss_task)
        
        sources = []
        context_texts = []
        rag_similarity_sum = 0
        rag_matches = 0

        if collection is not None:
            results = collection.query(query_embeddings=query_embeddings, n_results=5)
            if results and results['documents'] and results['distances']:
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    dist = results['distances'][0][i] 
                    similarity = 1 - dist
                    if similarity > 0.65: 
                        rag_matches += 1
                        rag_similarity_sum += similarity
                        meta = results['metadatas'][0][i] if results.get('metadatas') else {}
                        label = meta.get("label", "REAL")
                        if label == "REAL": context_texts.append(doc)
                        sources.append({
                            "title": f"Ma'lumotlar bazasi ({label})",
                            "snippet": doc[:150] + "...",
                            "relevance": round(similarity, 2),
                            "type": label
                        })
    except Exception as e:
        print("Error during RAG/RSS Fetch:", e)
        rss_sources = []

    # 2. LLM Analysis
    llm_result = await ask_llm(context_texts, user_input)

    # 3. Format RSS results
    formatted_rss = []
    rss_found = len(rss_sources) > 0
    for s in rss_sources:
        formatted_rss.append({
            "title": s['title'],
            "url": s['url'],
            "source": s['source'],
            "relevance": round(s['similarity'] / 100, 2),
            "match_reason": "Rasmiy yangiliklar tasdiqladi"
        })

    # 4. Scoring Logic
    llm_verdict = llm_result.get('verdict', 'UNCERTAIN')
    llm_signal = 1.0 if llm_verdict == "REAL" else (0.0 if llm_verdict == "FAKE" else 0.5)
    rag_avg_sim = (rag_similarity_sum / rag_matches) if rag_matches > 0 else None
    rss_signal = 1.0 if rss_found else None

    signals, weights = [llm_signal], [0.6]
    if rag_avg_sim is not None:
        signals.append(rag_avg_sim); weights.append(0.25)
    if rss_signal is not None:
        signals.append(rss_signal); weights.append(0.15)

    total_weight = sum(weights)
    confidence = sum(s * (w / total_weight) for s, w in zip(signals, weights))

    # Decision overrides
    verdict = llm_verdict
    if rss_found and llm_verdict in ("REAL", "UNCERTAIN"):
        verdict, confidence = "REAL", max(confidence, 0.85)
    elif rss_found and llm_verdict == "FAKE":
        verdict, confidence = "UNCERTAIN", 0.45

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "claim": llm_result.get('claim', user_input[:100]),
        "analysis": llm_result.get('analysis', {}),
        "sources": sources + formatted_rss,
        "final_explanation": llm_result.get('final_explanation', "Tahlil yakunlandi."),
        "text": user_input,
        "prediction": verdict # Compat
    }

class FeedbackRequest(BaseModel):
    text: Optional[str] = None
    prediction: str
    user_opinion: str

@app.post("/api/feedback")
def feedback(request_data: FeedbackRequest, request: Request):
    check_rate_limit(request.client.host)
    return {"message": "Thank you for your feedback!"}

# --- VERIFICATION CACHE ---
verify_cache = {}
def get_cache_key(text: str) -> str:
    return hashlib.md5(clean_text(text).encode('utf-8')).hexdigest()

RSS_FEEDS = {
    "Kun.uz": {"url": "https://kun.uz/uz/news/rss", "reliability": 100},
    "Daryo.uz": {"url": "https://daryo.uz/feed/", "reliability": 95},
    "Gazeta.uz": {"url": "https://www.gazeta.uz/uz/rss/", "reliability": 98},
    "UZA.uz": {"url": "https://uza.uz/uz/rss.xml", "reliability": 100}
}
async def poll_rss_feeds(query: str) -> list:
    normalized_query = clean_text(query)
    if tfidf_vectorizer is None: return []
    
    query_vector = tfidf_vectorizer.transform([normalized_query]).toarray()
    found_sources = []
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for name, data in RSS_FEEDS.items():
            tasks.append(client.get(data["url"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=5.0))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception) or resp.status_code != 200: continue
            try:
                name = list(RSS_FEEDS.keys())[i]
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item'):
                    title = item.find('title').text or ""
                    link = item.find('link').text or ""
                    if not title or not link: continue
                    
                    title_vec = tfidf_vectorizer.transform([clean_text(title)]).toarray()
                    score = float(np.dot(query_vector, title_vec.T))
                    if score > 0.70:
                        found_sources.append({"title": title, "url": link, "source": name, "similarity": round(score * 100, 1)})
                        break
            except: continue
    return found_sources

@app.post("/api/verify")
async def verify(request_data: VerifyRequest, request: Request):
    check_rate_limit(request.client.host)
    user_input = request_data.text
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="No text to verify")
    cache_key = get_cache_key(user_input)
    if cache_key in verify_cache: return verify_cache[cache_key]
    
    sources = await poll_rss_feeds(user_input)
    seen_urls = set()
    unique_sources = []
    for s in sources:
        if s["url"] not in seen_urls:
            unique_sources.append(s)
            seen_urls.add(s["url"])
            if len(unique_sources) >= 3: break
    result = {"found": len(unique_sources) > 0, "sources": unique_sources}
    verify_cache[cache_key] = result
    return result

# --- STATIC FILE SERVING ---
# Redirect root to landing page
@app.get("/")
async def read_index():
    return RedirectResponse(url="/landing_page.html")

# Mount the frontend directory
app.mount("/", StaticFiles(directory="frontend"), name="static")
