import os
import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv("data/processed/intent_dataset.csv")

print(f"Dataset Size : {len(df)}")
print(df.head())

# ==========================
# Features & Labels
# ==========================

X = df["instruction"]
y = df["intent"]

# ==========================
# Train/Test Split
# ==========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ==========================
# ML Pipeline
# ==========================

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        stop_words="english"
    )),
    ("classifier", LogisticRegression(
        max_iter=1000
    ))
])

# ==========================
# Train Model
# ==========================

model.fit(X_train, y_train)

# ==========================
# Predictions
# ==========================

predictions = model.predict(X_test)

# ==========================
# Evaluation
# ==========================

accuracy = accuracy_score(y_test, predictions)

print("\n==============================")
print(f"Accuracy : {accuracy:.4f}")
print("==============================\n")

report = classification_report(
    y_test,
    predictions,
    zero_division=0
)

print(report)

# ==========================
# Save Evaluation Reports
# ==========================

os.makedirs("outputs/intent_detection", exist_ok=True)

with open("outputs/intent_detection/classification_report.txt", "w") as f:
    f.write(report)

with open("outputs/intent_detection/accuracy.txt", "w") as f:
    f.write(f"Accuracy : {accuracy:.4f}")

# ==========================
# Save Model
# ==========================

os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/intent_model.pkl")

print("\nModel saved successfully!")
print("Classification report saved to outputs/intent_detection/")
print("Accuracy report saved to outputs/intent_detection/")
print("Model saved to models/intent_model.pkl")