import csv
import pandas as pd
import time
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ------------------------------------------------
# Step 1: Function to load messy CSV safely
# ------------------------------------------------
def load_messy_sql_csv(file_path):
    queries = []
    labels = []

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"', escapechar='\\')
        header_skipped = False
        for row in reader:
            if not header_skipped:
                header_skipped = True
                continue
            if len(row) != 2:
                continue
            query, label = row
            queries.append(query.strip())
            labels.append(label.strip())

    df = pd.DataFrame({'Query': queries, 'Label': labels})
    return df

# ------------------------------------------------
# Step 2: Load and clean dataset
# ------------------------------------------------
df = load_messy_sql_csv('train.csv')
print(f"✅ Loaded {len(df)} samples before cleaning.")

df = df[df['Label'].isin(['0', '1'])]
df['Label'] = df['Label'].astype(int)

if df['Label'].nunique() < 2:
    print("❌ Not enough distinct labels for training. Exiting.")
    exit()

print("✅ Cleaned label distribution:\n", df['Label'].value_counts())

# ------------------------------------------------
# Step 3: Prepare data
# ------------------------------------------------
X = df['Query']
y = df['Label']
vectorizer = CountVectorizer()
X_vectorized = vectorizer.fit_transform(X)
print(f"✅ Vectorized shape: {X_vectorized.shape}")

# ------------------------------------------------
# Step 4: Train/test split
# ------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X_vectorized, y, test_size=0.2, random_state=42, stratify=y
)
print(f"✅ Training size: {X_train.shape[0]}, Testing size: {X_test.shape[0]}")

# ------------------------------------------------
# Step 5: Train model on training set
# ------------------------------------------------
print("⏳ Training model on training set...")
start = time.time()
model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)
end = time.time()
print(f"✅ Model trained in {end - start:.2f} seconds.")

# ------------------------------------------------
# Step 6: Evaluation on test set
# ------------------------------------------------
y_pred_test = model.predict(X_test)
print("🎯 Accuracy on test data:", accuracy_score(y_test, y_pred_test))
print("📊 Test Classification Report:\n",
      classification_report(y_test, y_pred_test, target_names=['Safe', 'Attack']))

# ------------------------------------------------
# Step 7: (Optional) Evaluation on full training set
# ------------------------------------------------
y_pred_train = model.predict(X_train)
print("📈 Accuracy on training data:", accuracy_score(y_train, y_pred_train))
print("📋 Train Classification Report:\n",
      classification_report(y_train, y_pred_train, target_names=['Safe', 'Attack']))

# ------------------------------------------------
# Step 8: Save model and vectorizer
# ------------------------------------------------
joblib.dump(model, 'sqli_model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
print("💾 Model and vectorizer saved successfully.")

