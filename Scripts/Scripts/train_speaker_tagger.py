#!/usr/bin/env python3
"""
train_speaker_tagger.py — train a simple AI/STUDENT line classifier

Usage:
  python3 train_speaker_tagger.py --data train_lines.csv --out model.joblib [--drop-unk]

- Pipeline: TfidfVectorizer (character n-grams) + LogisticRegression (balanced)
- Reports 5-fold stratified CV (accuracy, precision/recall/F1)
- Saves the fitted model to --out
"""
import argparse, pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="CSV from mk_trainset.py")
    ap.add_argument("--out", required=True, help="Path to save trained model, e.g., model.joblib")
    ap.add_argument("--drop-unk", action="store_true", help="Drop any UNK rows if present")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    if args.drop_unk and "UNK" in df["label"].unique():
        df = df[df["label"].isin(["AI","STUDENT"])].copy()

    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]
    X = df["text"].values
    y = df["label"].values

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3,5), min_df=2)),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred = cross_val_predict(pipe, X, y, cv=skf)

    print("=== 5-fold CV report ===")
    print(classification_report(y, y_pred, digits=3))
    print("Confusion matrix (rows=true, cols=pred):")
    print(confusion_matrix(y, y_pred))

    pipe.fit(X, y)
    joblib.dump(pipe, args.out)
    print(f"Saved model to {args.out}")

if __name__ == "__main__":
    main()
