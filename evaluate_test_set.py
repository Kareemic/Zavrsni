"""
evaluate_test_set.py
====================
Rekreira isti test split koji smo koristili pri treniranju,
pusti trenirani model preko njega i spremi raw predikcije
za naknadnu analizu (precision@k, recall@k, AUC-PR, itd.).

Pokretanje:
    python evaluate_test_set.py

Izlaz:
    evaluacija/test_predictions.csv  — y_true, y_pred_proba za svaki test primjer
    Ispis u terminalu                 — AUC-PR, precision@k, recall@k tablica
"""

import os
import csv
import pickle
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_recall_curve,
)

# Koristimo iste konstante kao u classifier.py
DATASET_PATH = os.path.join("data", "dataset.csv")
MODEL_DIR    = "model"
OUTPUT_DIR   = "evaluacija"
IGNORED_COLUMNS = {"label", "source", "detected_language", "model_available"}
PERPLEXITY_MISSING = -1.0


# ─────────────────────────────────────────────────────────────────────────────
# UČITAVANJE — identično kao u classifier.py
# ─────────────────────────────────────────────────────────────────────────────

def ucitaj_dataset(path):
    redovi = list(csv.DictReader(open(path, encoding="utf-8")))
    if not redovi:
        raise ValueError("Dataset je prazan")
    sve_kolone    = list(redovi[0].keys())
    feature_names = [c for c in sve_kolone if c not in IGNORED_COLUMNS]
    X_rows, y_list, source_list = [], [], []
    for row in redovi:
        try:
            y_list.append(int(row["label"]))
            vrijednosti = []
            for feat in feature_names:
                val = float(row[feat])
                if feat == "perplexity" and val == PERPLEXITY_MISSING:
                    val = 0.0
                vrijednosti.append(val)
            X_rows.append(vrijednosti)
            source_list.append(row.get("source", ""))
        except (ValueError, KeyError):
            continue
    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y, feature_names, source_list


# ─────────────────────────────────────────────────────────────────────────────
# REKONSTRUKCIJA ISTOG SPLITA
# ─────────────────────────────────────────────────────────────────────────────

def rekonstruiraj_test_split(X, y, sources):
    """
    Primijeni isti undersampling i train/test split kao u classifier.py.
    random_state=42 + iste opcije daju uvijek isti rezultat.
    """
    # Korak 1: undersampling (kao u classifier.py)
    n_ai    = int(np.sum(y == 1))
    n_human = int(np.sum(y == 0))
    target_human = min(n_human, n_ai * 3)

    rng = np.random.default_rng(42)

    if n_human > target_human:
        human_idx = np.where(y == 0)[0]
        ai_idx    = np.where(y == 1)[0]
        chosen_human = rng.choice(human_idx, size=target_human, replace=False)
        all_idx = np.concatenate([chosen_human, ai_idx])
        rng.shuffle(all_idx)
        X = X[all_idx]
        y = y[all_idx]
        sources = [sources[i] for i in all_idx]

    # Korak 2: 80/20 split (identično classifier.py)
    indices = np.arange(len(y))
    _, X_test, _, y_test, _, idx_test = train_test_split(
        X, y, indices,
        test_size=0.2, random_state=42, stratify=y
    )
    sources_test = [sources[i] for i in idx_test]
    return X_test, y_test, sources_test


# ─────────────────────────────────────────────────────────────────────────────
# PRECISION@K / RECALL@K
# ─────────────────────────────────────────────────────────────────────────────

def precision_at_k(y_true_sorted, k):
    """
    Od top-k najrangiranijih, koliki je udio stvarno AI (label=1).
    """
    if k <= 0 or k > len(y_true_sorted): return 0.0
    return float(np.sum(y_true_sorted[:k] == 1)) / k


def recall_at_k(y_true_sorted, k, total_positives):
    """
    Od ukupnih AI primjera u test skupu, koliki postotak je u top-k.
    """
    if total_positives == 0: return 0.0
    return float(np.sum(y_true_sorted[:k] == 1)) / total_positives


# ─────────────────────────────────────────────────────────────────────────────
# GLAVNI PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Evaluacija na test skupu — precision@k, recall@k, AUC-PR")
    print("=" * 60)

    # Učitaj sve potrebno
    print("\n  Učitavam model, scaler i dataset...")
    with open(os.path.join(MODEL_DIR, "classifier.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "scaler.pkl"), "rb") as f:
        scaler = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "feature_names.pkl"), "rb") as f:
        feature_names = pickle.load(f)

    X, y, _, sources = ucitaj_dataset(DATASET_PATH)
    print(f"  Učitan dataset: {len(y)} primjera, "
          f"{int(np.sum(y == 0))} human, {int(np.sum(y == 1))} AI")

    # Rekreiraj isti test split
    X_test, y_test, sources_test = rekonstruiraj_test_split(X, y, sources)
    print(f"  Test skup:      {len(y_test)} primjera, "
          f"{int(np.sum(y_test == 0))} human, {int(np.sum(y_test == 1))} AI")

    # Normaliziraj i predikt
    X_test_scaled = scaler.transform(X_test)
    y_pred_proba  = model.predict_proba(X_test_scaled)[:, 1]

    # ─────────────────────────────────────────────────────────────────────
    # AUC-PR (Average Precision)
    # ─────────────────────────────────────────────────────────────────────
    auc_pr  = average_precision_score(y_test, y_pred_proba)
    auc_roc = roc_auc_score(y_test, y_pred_proba)

    print(f"\n  ┌─────────────────────────────────────────┐")
    print(f"  │  AGREGATNE METRIKE                      │")
    print(f"  ├─────────────────────────────────────────┤")
    print(f"  │  AUC-ROC:  {auc_roc:.4f}                   │")
    print(f"  │  AUC-PR:   {auc_pr:.4f}  ← traži profesor │")
    print(f"  └─────────────────────────────────────────┘")

    # ─────────────────────────────────────────────────────────────────────
    # PRECISION@K / RECALL@K
    # ─────────────────────────────────────────────────────────────────────
    # Sortiramo silazno po vjerojatnosti — top primjeri prvi
    sort_idx = np.argsort(-y_pred_proba)
    y_sorted     = y_test[sort_idx]
    proba_sorted = y_pred_proba[sort_idx]
    total_positives = int(np.sum(y_test == 1))

    k_values = [10, 20, 50, 100, 200, 500, 1000]
    k_values = [k for k in k_values if k <= len(y_test)]

    print(f"\n  Test skup ima ukupno {total_positives} AI primjera.")
    print(f"\n  ┌─────┬─────────────────┬──────────────┬──────────────┐")
    print(f"  │  k  │  Prag (proba)   │ Precision@k  │  Recall@k    │")
    print(f"  ├─────┼─────────────────┼──────────────┼──────────────┤")
    for k in k_values:
        p_at_k = precision_at_k(y_sorted, k)
        r_at_k = recall_at_k(y_sorted, k, total_positives)
        prag   = proba_sorted[k - 1]
        print(f"  │ {k:>3} │ {prag:>13.4f}   │ {p_at_k:>10.4f}   │ {r_at_k:>10.4f}   │")
    print(f"  └─────┴─────────────────┴──────────────┴──────────────┘")

    # ─────────────────────────────────────────────────────────────────────
    # SPREMI RAW PREDIKCIJE U CSV
    # ─────────────────────────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUTPUT_DIR, "test_predictions.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["y_true", "y_pred_proba", "source"])
        for i in range(len(y_test)):
            w.writerow([int(y_test[i]), float(y_pred_proba[i]), sources_test[i]])
    print(f"\n  Spremljeno {len(y_test)} predikcija u: {csv_path}")
    print(f"  Format: y_true (0=human, 1=AI), y_pred_proba (0.0-1.0), source")

    print(f"\n  Sad možeš dati ovaj CSV drugom chatu za diplomski rad —")
    print(f"  ima sve potrebno za precision@k, recall@k, AUC-PR krivulju.")


if __name__ == "__main__":
    main()
