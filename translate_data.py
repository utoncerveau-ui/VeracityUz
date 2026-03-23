import pandas as pd
from deep_translator import GoogleTranslator
import time
import os

# Load original dataset
df = pd.read_csv('dataset_english.csv')

# Check if partial translation exists
if os.path.exists('dataset_uzbek.csv'):
    df_existing = pd.read_csv('dataset_uzbek.csv')
    already_done = len(df_existing)
    print(f"✅ Found existing progress: {already_done} articles already translated")
    print(f"▶️ Resuming from article {already_done + 1}...\n")
    translated_texts = df_existing['content_uz'].tolist()
else:
    already_done = 0
    translated_texts = []
    print("Starting fresh translation...\n")

# Only translate what's remaining
remaining_df = df.iloc[already_done:]

for i, row in remaining_df.iterrows():
    try:
        text = str(row['content'])[:500]
        translated = GoogleTranslator(source='en', target='uz').translate(text)
        translated_texts.append(translated)

        # Save progress every 100 articles
        if len(translated_texts) % 100 == 0:
            temp_df = df.iloc[:len(translated_texts)].copy()
            temp_df['content_uz'] = translated_texts
            temp_df[['content_uz', 'label']].to_csv('dataset_uzbek.csv', index=False)
            print(f"✅ Translated & saved {len(translated_texts)}/2000 articles...")

        time.sleep(0.3)

    except Exception as e:
        print(f"⚠️ Error at row {i}: {e}")
        translated_texts.append(str(row['content'])[:500])
        time.sleep(1)

# Final save
df_uz = df.copy()
df_uz['content_uz'] = translated_texts
df_uz[['content_uz', 'label']].to_csv('dataset_uzbek.csv', index=False)

print(f"\n✅ Done! Total translated: {len(translated_texts)}/2000")
print("Saved as dataset_uzbek.csv")
print("\nSample:")
print(df_uz[['content_uz', 'label']].head(3))