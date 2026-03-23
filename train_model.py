import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

print("🚀 Loading dataset...")
df = pd.read_csv('dataset_uzbek.csv')

# Drop missing values just in case
df = df.dropna(subset=['content_uz', 'label'])
print(f"Data shape after removing missing values: {df.shape}")

# Basic clean-up function
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    text = re.sub(r'\d+', '', text)      # remove numbers
    return text

print("🧹 Cleaning text...")
df['clean_text'] = df['content_uz'].apply(clean_text)

# Split features and target
X = df['clean_text']
y = df['label']

# Split train and test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

# Vectorize text
print("🔡 Vectorizing text with TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Train Model
print("🧠 Training Logistic Regression Model...")
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train_vec, y_train)

# Evaluate
print("📊 Evaluating model on test data...")
y_pred = model.predict(X_test_vec)

acc = accuracy_score(y_test, y_pred)
print(f"\n✅ Accuracy: {acc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Fake (0)', 'Real (1)']))

print("\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(f"[{cm[0][0]}  {cm[0][1]}]")
print(f"[{cm[1][0]}  {cm[1][1]}]")

# Save model & vectorizer
print("\n💾 Saving model and vectorizer to disk...")
joblib.dump(model, 'model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
print("🎉 All done! Ready for inference.")
