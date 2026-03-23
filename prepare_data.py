import pandas as pd

# Load the datasets
fake = pd.read_csv('Fake.csv')
real = pd.read_csv('True.csv')

# Add labels: 0 = fake, 1 = real
fake['label'] = 0
real['label'] = 1

# Take only 1000 from each to keep it manageable
fake_sample = fake[['title', 'text', 'label']].sample(1000, random_state=42)
real_sample = real[['title', 'text', 'label']].sample(1000, random_state=42)

# Combine into one dataset
df = pd.concat([fake_sample, real_sample], ignore_index=True)

# Shuffle it
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Combine title + text into one column
df['content'] = df['title'] + ' ' + df['text']

# Keep only what we need
df = df[['content', 'label']]

# Save it
df.to_csv('dataset_english.csv', index=False)

print("✅ Dataset ready!")
print("Total articles:", len(df))
print("Fake (0):", len(df[df['label'] == 0]))
print("Real (1):", len(df[df['label'] == 1]))
print("\nSample:")
print(df.head(3))