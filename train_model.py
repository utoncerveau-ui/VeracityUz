import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
from collections import Counter

# --- LINGUISTIC NORMALIZATION (Matches app.py) ---
def normalize_uzbek(text: str) -> str:
    """Standardizes Uzbek text by converting Latin characters/ligatures to Cyrillic."""
    mapping = {
        "o'": "ў", "O'": "Ў", "o`": "ў", "O`": "Ў",
        "g'": "ғ", "G'": "Ғ", "g`": "ғ", "G`": "Ғ",
        "sh": "ш", "Sh": "Ш", "SH": "Ш",
        "ch": "ч", "Ch": "Ч", "CH": "Ч",
        "a": "а", "A": "А", "b": "б", "B": "Б", "d": "д", "D": "Д",
        "e": "е", "E": "Е", "f": "ф", "F": "Ф", "g": "г", "G": "Г",
        "h": "ҳ", "H": "Ҳ", "i": "и", "I": "И", "j": "ж", "J": "Ж",
        "k": "к", "K": "К", "l": "л", "L": "Л", "m": "м", "M": "М",
        "n": "н", "N": "Н", "o": "о", "O": "О", "p": "п", "P": "П",
        "q": "қ", "Q": "Қ", "r": "р", "R": "Р", "s": "с", "S": "С",
        "t": "т", "T": "Т", "u": "у", "U": "У", "v": "в", "V": "В",
        "x": "х", "X": "Х", "y": "й", "Y": "Й", "z": "з", "Z": "З",
        "o‘": "ў", "g‘": "ғ"
    }
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    result = str(text)
    for key in sorted_keys:
        result = result.replace(key, mapping[key])
    return result

def clean_text(text: str) -> str:
    """Standardized cleaning (Latin->Cyrillic -> Strip non-alphanumeric)."""
    normalized = normalize_uzbek(text)
    return re.sub(r'[^а-яА-ЯёЁқҚғҒҳҲчЧшШўЎ0-9\s]', '', normalized.lower())

print("Loading dataset...")
df = pd.read_csv('dataset_uzbek.csv')
df = df.dropna(subset=['content_uz', 'label'])

print("Cleaning and Normalizing text...")
df['clean_text'] = df['content_uz'].apply(clean_text)

# Check Class Balance (Phase 2 Item 10)
X, y = df['clean_text'], df['label']
counts = Counter(y)
print(f"Class distribution: {counts}")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Vectorizing text with TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("Training Balanced Logistic Regression Model...")
# Phase 2 Item 10: Use class_weight='balanced' if imbalanced
model = LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
model.fit(X_train_vec, y_train)

print("Evaluating model...")
y_pred = model.predict(X_test_vec)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Saving optimized model and vectorizer...")
joblib.dump(model, 'uzbek_news_model.joblib')
joblib.dump(vectorizer, 'vectorizer.joblib')
print("Phase 1 Overhaul Complete!")
