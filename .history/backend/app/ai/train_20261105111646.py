import csv
from pathlib import Path
from collections import Counter

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# Locate the dataset and model directory
AI_DIR = Path(__file__).resolve().parent
DATASET_PATH = AI_DIR / "datasets" / "security_alerts.csv"
MODEL_DIR = AI_DIR / "models"
MODEL_PATH = MODEL_DIR / "security_classifier.joblib"


def load_dataset():
    descriptions = []
    labels = []

    with open(DATASET_PATH, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if not {"descriptiom", "label"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV must contain description and label columns.")

        for row in reader: 
            description = (row.get("description") or "").strip()
            label = (row.get("label" or "").strip())
            
            if description and label: 
                descriptions.append(description)
                labels.append(label)

    if not descriptions:
        raise ValueError("No valid training examples found.")

    counts = Counter(labels)

    if len(counts) < 2 or min(counts.values()) < 2:
        raise ValueError("Each category needs at least two examples.")

    return descriptions, labels

def main():
    print("Loading security alert dataset...")

    descriptions, labels = load_dataset()

    print(f"Total examples: {len(descriptions)}")
    print(f"Categories: {len(set(labels))}")
    print("Category distribution:", Counter(labels))

    # Create machine0learning pipeline
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase = True,
            ngram_range=(1,2),
            sublinear_tf=True
        )),
        ("classifier, LogisiticRegression(
            max_iter =1000,
            class_weights="balanced"
        ))
    ])  

    # Split data for intial evaluation