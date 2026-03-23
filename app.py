import joblib
import re
import urllib.request
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Fake News Detector API")

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

def load_models():
    try:
        model = joblib.load('model.pkl')
        vectorizer = joblib.load('vectorizer.pkl')
        return model, vectorizer
    except FileNotFoundError:
        return None, None

model, vectorizer = load_models()

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    return text

@app.post("/api/predict")
def predict(request: PredictRequest):
    if model is None or vectorizer is None:
        raise HTTPException(status_code=500, detail="Models not found! Train models first.")
    
    user_input = request.text
    if not user_input or not user_input.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    def classify_input(text: str) -> str | None:
        """Returns 'NOT_NEWS' if text is gibberish/too short/not a news article, else None."""
        words = text.strip().split()

        # Too short to be a news article
        if len(words) < 4:
            return "NOT_NEWS"

        # Personal / Greeting filter (Personal sentences usually aren't news articles)
        personal_keywords = [
            'men', 'mani', 'mening', 'ismlim', 'ismim', 'salom', 'qalesiz', 'qalaysiz', 'siz', 'sizi', 'sizning',
            'ман', 'мани', 'менинг', 'исмим', 'салом', 'қалайсиз', 'қалесиз', 'сиз', 'сизи', 'сизни'
        ]
        text_lower = text.lower()
        if any(word in text_lower for word in personal_keywords):
            # If it's short AND has personal keywords, it's definitely not news
            if len(words) < 7:
                return "NOT_NEWS"

        # Gibberish detector: count words that look like real words
        vowels = set('aeiouAEIOUaeiouAEIOUаеёиоуыьъэюяАЕЁИОУЫЬЪЭЮЯ' + 'aeiouAEIOUoʻgʻ')
        real_word_count = sum(1 for w in words if any(c in vowels for c in w) and len(w) >= 2)
        real_ratio = real_word_count / len(words)

        if real_ratio < 0.5:
            return "NOT_NEWS"

        return None

    not_news_reason = classify_input(user_input)
    if not_news_reason:
        return {
            "prediction": "NOT_NEWS",
            "confidence": 0.0,
            "fake_probability": 0.0,
            "real_probability": 0.0,
            "text": user_input,
            "linguistics": {"objectivity": 50, "emotional": 0}
        }

    cleaned = clean_text(user_input)
    vec_text = vectorizer.transform([cleaned])
    prediction = int(model.predict(vec_text)[0])
    prob = model.predict_proba(vec_text)[0]
    fake_prob = float(prob[0])
    real_prob = float(prob[1])

    def analyze_linguistics(text: str) -> dict:
        if not text:
            return {"objectivity": 50, "emotional": 0}
        
        text_upper = text.upper()
        
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        words = text.split()
        all_caps_words = [w for w in words if w.isupper() and len(w) > 3]
        
        buzzwords = ["SHOK", "DAHSHAT", "SENSATSIYA", "SHOSHILINCH", "DIQQAT", "BOSHQA", "HECH QACHON", "YOLG'ON", "HAQIQAT", "SIRLAR", "FOSH", "SHOK XABAR"]
        buzzword_count = sum(1 for b in buzzwords if b in text_upper)
        
        emotional_score = min(100, (exclamation_count * 10) + (question_count * 5) + (len(all_caps_words) * 5) + (buzzword_count * 15))
        
        has_numbers = bool(re.search(r'\d+', text))
        quotes_count = text.count('"') + text.count("'") + text.count('«') + text.count('»')
        
        objectivity_score = 100 - (emotional_score * 0.7)
        if has_numbers:
            objectivity_score = min(100, objectivity_score + 10)
        if quotes_count > 0:
            objectivity_score = min(100, objectivity_score + 5)
            
        return {
            "objectivity": round(objectivity_score),
            "emotional": round(emotional_score)
        }

    linguistics = analyze_linguistics(user_input)

    return {
        "prediction": "REAL" if prediction == 1 else "FAKE",
        "confidence": real_prob if prediction == 1 else fake_prob,
        "fake_probability": fake_prob,
        "real_probability": real_prob,
        "text": user_input,
        "linguistics": linguistics
    }

@app.post("/api/verify")
def verify(request: VerifyRequest):
    user_input = request.text
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="No text to verify")

    # Filter query words to 12 for high-precision matches on DDG
    words = user_input.split()[:12]
    query = ' '.join(words)
    
    # We search the main headline. Filtering for trusted sites in Python is more robust than complex DDG OR queries.
    search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    trusted_domains = [
        'kun.uz', 'daryo.uz', 'gazeta.uz', 'uza.uz', 'sputniknews-uz.com', 'sputniknews.uz',
        'podrobno.uz', 'xabar.uz', 'qallampir.uz', 'huquqiyportal.uz', 'uznews.uz', 'spot.uz'
    ]

    try:
        html_content = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        
        # Capture links with class result__a (titles) or result__url (breadcurmbs)
        # result__a is preferred as it contains the full title.
        pattern = r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
        raw_results = re.findall(pattern, html_content, re.DOTALL)
        
        # Fallback if result__a is not found (though unlikely on DDG html)
        if not raw_results:
            pattern = r'class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
            raw_results = re.findall(pattern, html_content, re.DOTALL)
        
        matches = []
        for link, title_raw in raw_results:
            # Clean HTML tags from title
            title = re.sub(r'<[^>]+>', '', title_raw).strip()
            
            # Extract actual URL from DDG redirect
            actual_url = link
            if 'duckduckgo.com/l/' in link or link.startswith('//duckduckgo'):
                parsed_link = urllib.parse.urlparse(link if link.startswith('http') else 'https:' + link)
                qs = urllib.parse.parse_qs(parsed_link.query)
                uddg = qs.get('uddg')
                if uddg:
                    actual_url = urllib.parse.unquote(uddg[0])
            
            # Validate domain against trusted list
            parsed_actual = urllib.parse.urlparse(actual_url)
            domain = parsed_actual.netloc.lower().replace('www.', '')
            
            if any(trusted in domain for trusted in trusted_domains):
                matches.append({"url": actual_url, "title": title})
        
        # Deduplicate and limit to top 5
        seen = set()
        final_sources = []
        for m in matches:
            if m["url"] not in seen:
                final_sources.append(m)
                seen.add(m["url"])
        
        return {
            "found": len(final_sources) > 0,
            "sources": final_sources[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search Error: {str(e)}")


