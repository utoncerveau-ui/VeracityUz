# Veracity Uz: Advanced Fake News Detection for Uzbek Content

**Veracity Uz** is a state-of-the-art news verification platform specifically engineered for the Uzbek linguistic landscape. It employs a **Triple-Layer Hybrid Verification** architecture that combines traditional Machine Learning, Retrieval-Augmented Generation (RAG), and Live RSS cross-referencing.

---

## 🛡️ The Triple-Layer Defense Architecture

Unlike simple classifiers, Veracity Uz utilizes a weighted consensus model (**40/40/20**) to ensure maximum accuracy:

1.  **🧠 Layer 1: Neural Linguistic Analysis (40%)**
    *   Powered by a custom-trained **Logistic Regression** model.
    *   Analyzes structural patterns, emotional triggers, objectivity scores, and common dezinformatsiya markers in Uzbek text.
    *   Handles both **Latin and Cyrillic** scripts via a proprietary normalization engine.

2.  **📚 Layer 2: Knowledge Base RAG (40%)**
    *   **Retrieval-Augmented Generation**: Queries a local vector database of 15,000+ news chunks.
    *   **Negative Knowledge**: Indexes both known REAL and verified FAKE news to detect recurring rumors and debunked claims.
    *   **Semantic Search**: Uses stable TF-IDF vectorization for lightning-fast, dependency-free local retrieval.

3.  **📡 Layer 3: Live RSS Verification (20%)**
    *   Real-time polling of trusted Uzbek news outlets (`kun.uz`, `gazeta.uz`, `daryo.uz`, etc.).
    *   Uses semantic similarity to match user input against current breaking news.

---

## ✨ Key Technical Features

-   **🤖 Structured AI Reasoning**: Integrated with Gemini Pro to provide deep-dive "Chain-of-Thought" explanations for every verdict.
-   **📑 Sentence-Level Chunking**: RAG system breaks articles into overlapping windows for high-granularity evidence detection.
-   **⚖️ Weighted Verdict System**:
    *   **Haqiqiy (Real)**: High consensus across all layers.
    *   **Tasdiqlanmagan (Unverified)**: Plausible text but missing evidence in the knowledge base.
    *   **Yolg'on (Fake)**: Flagged by ML or matched against known misinformation patterns.
-   **📊 Advanced Linguistics Dashboard**: Visualizes Objectivity, Emotionality, and Source Credibility.
-   **🏙️ Glassmorphic UI**: A premium, dark-themed responsive interface designed for both professional and casual users.

---

## 🚀 Getting Started

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/fake-news-uzbek.git
cd fake-news-uzbek

# Install stable dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Initialize the Knowledge Base
```bash
python create_index.py
```

### 4. Run the Platform
```bash
# Start Backend
python -m uvicorn app:app --port 8000

# Start Frontend (in a new terminal)
cd frontend
python -m http.server 3000
```
Visit `http://localhost:3000`.

---

## 📂 Project Roadmap

- [x] **Phase 1**: Initial ML Classifier & Basic Search.
- [x] **Phase 2**: RAG Implementation with local vector storage.
- [x] **Phase 3**: Weighted Verdict Scoring & Semantic RSS.
- [ ] **Phase 4**: Native Uzbek Dataset Augmentation (Current Goal).
- [ ] **Phase 5**: Telegram Bot Integration.

---

## 📜 Technical Philosophy

Veracity Uz operates on the principle that **Facts > Predictions**. Even if our AI is suspicious of a text, if it finds a matching story on a trusted official source, the system intelligently upgrades the verdict. This "Fact-First" approach minimizes false positives and builds user trust.

---
*Developed for research and educational purposes in combating digital misinformation.*
