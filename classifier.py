"""
classifier.py
=============
Trenira Random Forest klasifikator na datasetu izvučenih značajki,
evaluira ga i sprema na disk za korištenje u web aplikaciji.

Pokretanje (treniranje):
    python classifier.py

Korištenje iz drugog fajla (predikcija):
    from classifier import predict
    result = predict(code="def foo(x): return x", language="python")
    print(result["ai_probability"])   # npr. 0.73
    print(result["verdict"])          # "Vjerojatno AI"
    print(result["top_features"])     # koje značajke su bile ključne
"""

import os
import csv
import pickle
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
)
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV

from feature_extraction import extract_all_features


# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURACIJA
# ─────────────────────────────────────────────────────────────────────────────

DATASET_PATH  = os.path.join("data", "dataset.csv")
MODEL_DIR     = "model"
MODEL_PATH    = os.path.join(MODEL_DIR, "classifier.pkl")
SCALER_PATH   = os.path.join(MODEL_DIR, "scaler.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "feature_names.pkl")

# Kolone koje ne koristimo kao značajke za treniranje
IGNORED_COLUMNS = {"label", "source", "detected_language", "model_available"}

# Značajka perplexity je -1.0 kad model nije učitan — tretiramo kao missing
PERPLEXITY_MISSING = -1.0

# Random Forest parametri
RF_PARAMS = {
    "n_estimators":  300,
    "max_depth":     None,
    "min_samples_leaf": 2,
    # Dajemo veću kaznu za lažno pozitivne (nevin student označen kao AI)
    # {0: 1.0, 1: 0.8} znači da je greška na human klasi 1.25x skuplja od greške na AI klasi
    # "balanced" automatski kompenzira neravnotežu klasa
    # Human dobiva veći težinski faktor jer je manjina (29% vs 71%)
    "class_weight": "balanced",
    # Uz to koristimo max_features za bolju generalizaciju
    "max_features": "sqrt",
    "random_state":  42,
    "n_jobs":       -1,
}

# Prag ispod kojeg smatramo kod "premalog" za pouzdanu analizu
MINIMUM_LINES = 5

# Prag vjerojatnosti — konzervativniji pragovi smanjuju lažno pozitivne
THRESHOLDS = {
    "likely_ai":    0.80,   # gore → "Vjerojatno AI"
    "possible_ai":  0.65,   # gore → "Moguće AI"
    "unclear":      0.45,   # gore → "Nejasno"
    "possible_human": 0.25, # gore → "Moguće čovječji"
    # ispod → "Vjerojatno čovječji"
}


# ─────────────────────────────────────────────────────────────────────────────
# UČITAVANJE DATASETA
# ─────────────────────────────────────────────────────────────────────────────

def ucitaj_dataset(path: str):
    """
    Učitava dataset.csv i vraća feature matricu X i vektor oznaka y.

    Tretira -1.0 vrijednosti (perplexity bez modela) kao 0.0
    jer klasifikator ne smije vidjeti negativne vrijednosti kao signal.

    Parametri:
        path (str): Putanja do CSV datoteke.

    Vraća:
        X (np.ndarray):         Matrica značajki oblika (n_samples, n_features).
        y (np.ndarray):         Vektor oznaka (0=human, 1=ai).
        feature_names (list):   Nazivi stupaca koji odgovaraju stupcima X.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset nije pronađen na '{path}'.\n"
            f"Pokreni prvo: python download_dataset.py"
        )

    redovi = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            redovi.append(row)

    if not redovi:
        raise ValueError("Dataset je prazan.")

    # Odredi nazive značajki (svi stupci osim ignoriranih)
    sve_kolone = list(redovi[0].keys())
    feature_names = [c for c in sve_kolone if c not in IGNORED_COLUMNS]

    X_rows = []
    y_list = []

    for row in redovi:
        try:
            y_list.append(int(row["label"]))

            # Pretvori svaku značajku u float
            # Perplexity -1.0 → 0.0 (nije dostupan, ne smije biti signal)
            vrijednosti = []
            for feat in feature_names:
                val = float(row[feat])
                if feat == "perplexity" and val == PERPLEXITY_MISSING:
                    val = 0.0
                vrijednosti.append(val)

            X_rows.append(vrijednosti)

        except (ValueError, KeyError):
            continue   # preskoči neispravne retke

    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)

    print(f"  Učitano {len(y)} primjera, {len(feature_names)} značajki")
    print(f"  Human (0): {sum(y == 0)}  |  AI (1): {sum(y == 1)}")

    return X, y, feature_names


# ─────────────────────────────────────────────────────────────────────────────
# TRENIRANJE
# ─────────────────────────────────────────────────────────────────────────────

def treniraj(X, y, feature_names):
    """
    Trenira Random Forest klasifikator i vraća trenirani model zajedno
    sa scalerom i rezultatima evaluacije.

    Pipeline:
        1. Podijeli podatke 80% trening / 20% test
        2. Normalizira značajke (StandardScaler)
        3. Trenira Random Forest
        4. Evaluira na test skupu
        5. Pokreće 5-fold cross-validation za pouzdaniju procjenu

    Parametri:
        X (np.ndarray):       Matrica značajki.
        y (np.ndarray):       Vektor oznaka.
        feature_names (list): Nazivi značajki.

    Vraća:
        model:   Trenirani RandomForestClassifier.
        scaler:  Trenirani StandardScaler.
        metrics: Rječnik s metrikama evaluacije.
    """
    # 1. Podjela na trening i test skup
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
        # stratify=y osigurava da i trening i test imaju isti omjer klasa
    )
    print(f"\n  Trening: {len(y_train)} primjera")
    print(f"  Test:    {len(y_test)} primjera")

    # 2. Normalizacija — StandardScaler svaku značajku svede na
    #    srednju vrijednost 0 i standardnu devijaciju 1.
    #    VAŽNO: scaler se fitira SAMO na trening skupu,
    #    a transformira i trening i test (da ne bi "curilo" znanje)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # 3. Treniranje Random Foresta + kalibracija vjerojatnosti
    # CalibratedClassifierCV popravlja iskrivljene vjerojatnosti RF-a.
    # Bez kalibracije, RF može davati 60% za nešto što je zapravo 30%.
    # method='isotonic' je jači, ali treba više podataka (>1000 primjera — ok)
    print("\n  Treniram Random Forest + kalibriram vjerojatnosti...")
    base_model = RandomForestClassifier(**RF_PARAMS)
    model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
    model.fit(X_train_scaled, y_train)

    # 4. Evaluacija na test skupu
    y_pred      = model.predict(X_test_scaled)
    y_pred_prob = model.predict_proba(X_test_scaled)[:, 1]

    print("\n" + "─" * 50)
    print("  REZULTATI EVALUACIJE")
    print("─" * 50)
    print(classification_report(
        y_test, y_pred,
        target_names=["Human (0)", "AI (1)"],
        digits=3
    ))

    # Matrica zabune — pokazuje lažno pozitivne i lažno negativne
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"  Matrica zabune:")
    print(f"    Ispravno human:      {tn}  (true negative)")
    print(f"    Lažno označen AI:    {fp}  (false positive)")
    print(f"    Propušten AI:        {fn}  (false negative)")
    print(f"    Ispravno AI:         {tp}  (true positive)\n")

    # AUC-ROC — mjera kvalitete rankiranja (0.5=slučajno, 1.0=savršeno)
    auc = roc_auc_score(y_test, y_pred_prob)
    print(f"  AUC-ROC: {auc:.4f}")

    # 5. Pronalazi optimalni prag odluke koji maksimizira F1 za human klasu
    # Cilj: smanjiti lažno pozitivne (FP) čak i ako propustimo koji AI
    precisions, recalls, thresholds = precision_recall_curve(
        y_test, y_pred_prob, pos_label=0  # gledamo human klasu (0)
    )
    # Tražimo prag gdje je precision za human >= 0.85
    # (tj. kad kažemo "human", u barem 85% slučajeva stvarno je human)
    optimal_threshold = 0.5  # fallback
    for prec, rec, thr in zip(precisions, recalls, thresholds):
        if prec >= 0.85 and rec >= 0.30:
            optimal_threshold = thr
            break

    print(f"\n  Optimalni prag odluke za AI klasu: {1 - optimal_threshold:.2f}")
    print(f"  (Prag ispod kojeg klasificiramo kao Human)")

    # Spremi optimalni prag uz model
    threshold_path = os.path.join(MODEL_DIR, "threshold.pkl")
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(threshold_path, "wb") as f_thr:
        pickle.dump(float(1 - optimal_threshold), f_thr)

    # 6. Cross-validation s miješanjem — pouzdanija procjena
    # StratifiedKFold + shuffle sprječava situaciju gdje jedna fold
    # sadrži samo jedan tip podataka (npr. samo AIGCodeSet)
    from sklearn.model_selection import StratifiedKFold
    print("\n  5-fold cross-validation (može potrajati minutu)...")
    X_scaled_full = scaler.transform(X)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        model, X_scaled_full, y,
        cv=skf, scoring="f1", n_jobs=-1
    )
    print(f"  CV F1 scores: {[f'{s:.3f}' for s in cv_scores]}")
    print(f"  CV F1 prosjek: {cv_scores.mean():.3f} "
          f"(±{cv_scores.std():.3f})")

    # Top 10 najvažnijih značajki
    # CalibratedClassifierCV omotava base estimator, pa trebamo
    # dohvatiti feature_importances_ iz jednog od kalibriranih estimatora
    try:
        base_rf = model.calibrated_classifiers_[0].estimator
        importances = base_rf.feature_importances_
    except Exception:
        # Fallback ako struktura nije očekivana
        importances = np.zeros(len(feature_names))

    top_idx = np.argsort(importances)[::-1][:10]
    print("\n  Top 10 najvažnijih značajki:")
    for rank, idx in enumerate(top_idx, 1):
        print(f"    {rank:2}. {feature_names[idx]:<38} {importances[idx]:.4f}")

    metrics = {
        "auc_roc":    auc,
        "cv_f1_mean": cv_scores.mean(),
        "cv_f1_std":  cv_scores.std(),
        "true_negative":   int(tn),
        "false_positive":  int(fp),
        "false_negative":  int(fn),
        "true_positive":   int(tp),
    }

    return model, scaler, metrics


# ─────────────────────────────────────────────────────────────────────────────
# SPREMANJE MODELA
# ─────────────────────────────────────────────────────────────────────────────

def spremi_model(model, scaler, feature_names):
    """
    Sprema trenirani model, scaler i listu naziva značajki na disk.

    Sva tri fajla su potrebna za predikciju:
      - model     : donosi odluku
      - scaler    : normalizira ulaz na isti način kao pri treniranju
      - feature_names : osigurava da se značajke šalju u ispravnom redoslijedu

    Parametri:
        model:          Trenirani RandomForestClassifier.
        scaler:         Trenirani StandardScaler.
        feature_names:  Lista naziva značajki.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    THRESHOLD_PATH = os.path.join(MODEL_DIR, "threshold.pkl")

    with open(MODEL_PATH,     "wb") as f: pickle.dump(model,         f)
    with open(SCALER_PATH,    "wb") as f: pickle.dump(scaler,        f)
    with open(FEATURES_PATH,  "wb") as f: pickle.dump(feature_names, f)

    print(f"\n  Model spremljen u:          {MODEL_PATH}")
    print(f"  Scaler spremljen u:         {SCALER_PATH}")
    print(f"  Nazivi značajki spremljeni: {FEATURES_PATH}")
    if os.path.exists(THRESHOLD_PATH):
        with open(THRESHOLD_PATH, "rb") as f:
            thr = pickle.load(f)
        print(f"  Optimalni prag:             {thr:.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# PREDIKCIJA — koristi se iz web aplikacije
# ─────────────────────────────────────────────────────────────────────────────

def ucitaj_model():
    """
    Učitava model, scaler, nazive značajki i optimalni prag s diska.
    Poziva se jednom pri pokretanju web servera.

    Vraća:
        (model, scaler, feature_names, threshold) ili
        (None, None, None, 0.65) ako model ne postoji.
    """
    THRESHOLD_PATH = os.path.join(MODEL_DIR, "threshold.pkl")

    if not all(os.path.exists(p) for p in [MODEL_PATH, SCALER_PATH, FEATURES_PATH]):
        return None, None, None, 0.65

    with open(MODEL_PATH,    "rb") as f: model         = pickle.load(f)
    with open(SCALER_PATH,   "rb") as f: scaler        = pickle.load(f)
    with open(FEATURES_PATH, "rb") as f: feature_names = pickle.load(f)

    threshold = 0.65  # konzervativni default
    if os.path.exists(THRESHOLD_PATH):
        with open(THRESHOLD_PATH, "rb") as f:
            threshold = pickle.load(f)

    return model, scaler, feature_names, threshold



# ─────────────────────────────────────────────────────────────────────────────
# GENERIRANJE OBJAŠNJENJA
# ─────────────────────────────────────────────────────────────────────────────

def generate_explanations(features: dict, ai_prob: float) -> list:
    """
    Generira listu objašnjenja na engleskom jeziku koja opisuju
    zašto kod izgleda AI generiran ili čovječji.

    Svako objašnjenje je rječnik s:
      "text"     — rečenica objašnjenja
      "severity" — "high" | "medium" | "low" | "positive"
      "feature"  — naziv značajke na koju se objašnjenje odnosi

    Pragovi su kalibrirani na temelju tipičnih vrijednosti u
    AI-Detector i HMCorp datasetovima.

    Parametri:
        features (dict): Rječnik značajki iz extract_all_features().
        ai_prob (float): Vjerojatnost AI podrijetla (0.0 – 1.0).

    Vraća:
        list: Lista rječnika s objašnjenjima, sortirana po ozbiljnosti.
    """
    objasnjenja = []

    def dodaj(text, severity, feature):
        objasnjenja.append({"text": text, "severity": severity, "feature": feature})

    # ── IMENOVANJE ─────────────────────────────────────────────────────────

    avg_id_len = features.get("avg_identifier_length", 0)
    if avg_id_len > 7.5:
        dodaj(
            f"Identifier names are unusually long and descriptive "
            f"(average {avg_id_len:.1f} characters). "
            f"AI-generated code consistently favours verbose, self-documenting names "
            f"such as 'calculate_average_value' over typical student shorthand like 'avg'.",
            "high", "avg_identifier_length"
        )
    elif avg_id_len > 5.5:
        dodaj(
            f"Identifier names are moderately long (average {avg_id_len:.1f} characters), "
            f"which is slightly above the typical range for human-written student code.",
            "medium", "avg_identifier_length"
        )
    elif avg_id_len < 2.5 and avg_id_len > 0:
        dodaj(
            f"Identifier names are very short (average {avg_id_len:.1f} characters), "
            f"consistent with a human programmer's preference for concise variable names.",
            "positive", "avg_identifier_length"
        )

    naming_cons = features.get("naming_consistency", 0)
    if naming_cons > 0.85:
        dodaj(
            f"Naming convention is highly consistent throughout the submission "
            f"({naming_cons * 100:.0f}% of identifiers follow the same pattern). "
            f"Human programmers typically mix conventions, especially in longer submissions.",
            "high", "naming_consistency"
        )
    elif naming_cons < 0.3 and naming_cons > 0:
        dodaj(
            f"Naming convention varies across the submission, which is characteristic "
            f"of code written incrementally by a human programmer.",
            "positive", "naming_consistency"
        )

    single_char = features.get("single_char_name_ratio", 0)
    if single_char < 0.03 and features.get("num_functions", 0) > 1:
        dodaj(
            f"No single-character variable names were detected. "
            f"Human programmers routinely use short names such as 'i', 'x', or 'n' "
            f"in loops and helper functions; their absence is atypical.",
            "medium", "single_char_name_ratio"
        )
    elif single_char > 0.25:
        dodaj(
            f"A notable proportion of variables use single-character names "
            f"({single_char * 100:.0f}%), which is common in human-written code.",
            "positive", "single_char_name_ratio"
        )

    # ── KOMENTARI I DOCSTRINGOVI ───────────────────────────────────────────

    comment_ratio = features.get("comment_ratio", 0)
    if comment_ratio > 0.30:
        dodaj(
            f"Comment density is substantially above average — "
            f"{comment_ratio * 100:.0f}% of lines contain inline comments. "
            f"AI models tend to annotate nearly every logical step, "
            f"whereas students typically comment only non-obvious sections.",
            "high", "comment_ratio"
        )
    elif comment_ratio > 0.18:
        dodaj(
            f"Comment density ({comment_ratio * 100:.0f}% of lines) is higher than "
            f"typically observed in student submissions at this level.",
            "medium", "comment_ratio"
        )
    elif comment_ratio < 0.03:
        dodaj(
            f"Very few or no inline comments are present, which is more consistent "
            f"with human-written code at this stage of the course.",
            "positive", "comment_ratio"
        )

    num_docs = features.get("num_docstrings", 0)
    # Aproksimiramo broj funkcija iz function_density i total_lines
    # jer structural features sada vraćaju gustoće, ne apsolutne brojeve
    fn_density  = features.get("function_density", 0)
    total_lines = features.get("total_lines", 1)
    num_fns_est = max(1, round(fn_density * total_lines))

    if num_docs > 0:
        doc_coverage = num_docs / max(num_fns_est, 1)
        if num_docs >= 3 and doc_coverage >= 0.8:
            dodaj(
                f"Every function in the submission includes a formal docstring "
                f"({num_docs} docstrings detected). "
                f"Complete docstring coverage is a strong marker of AI-generated code; "
                f"students rarely document all functions unless explicitly required.",
                "high", "num_docstrings"
            )
        elif num_docs >= 2:
            dodaj(
                f"Multiple functions include docstrings ({num_docs} detected), "
                f"which is above the typical student average.",
                "medium", "num_docstrings"
            )

    # ── STRUKTURNE ZNAČAJKE ────────────────────────────────────────────────

    avg_fn_len = features.get("avg_function_length", 0)
    if avg_fn_len > 20:
        dodaj(
            f"Functions are notably long on average ({avg_fn_len:.0f} lines per function). "
            f"AI models tend to produce complete, self-contained implementations; "
            f"students more often break logic across multiple smaller functions "
            f"or leave parts incomplete.",
            "medium", "avg_function_length"
        )
    elif 0 < avg_fn_len < 6:
        dodaj(
            f"Functions are concise on average ({avg_fn_len:.1f} lines), "
            f"which is consistent with a human programmer's incremental coding style.",
            "positive", "avg_function_length"
        )

    try_density = features.get("try_density", 0)
    if try_density > 0.06:
        dodaj(
            f"The submission contains a relatively high density of try/except blocks. "
            f"Comprehensive error handling across all edge cases is a pattern "
            f"commonly exhibited by AI generators, which anticipate and handle "
            f"exceptions that students typically overlook.",
            "medium", "try_density"
        )

    nesting = features.get("max_nesting_depth", 0)
    if nesting > 5:
        dodaj(
            f"Code nesting reaches a depth of {int(nesting)} levels. "
            f"While not conclusive, deeply nested logic can reflect an AI model's "
            f"tendency to handle all conditional branches explicitly.",
            "medium", "max_nesting_depth"
        )

    # ── STATISTIČKA ANALIZA ────────────────────────────────────────────────

    token_entropy = features.get("token_entropy", 0)
    if token_entropy > 0 and token_entropy < 3.8:
        dodaj(
            f"Token entropy is low ({token_entropy:.2f}), indicating that the vocabulary "
            f"of the submission is repetitive and predictable. "
            f"This is consistent with language model output, which tends to reuse "
            f"the same phrasing and structural patterns.",
            "high", "token_entropy"
        )
    elif token_entropy > 5.5:
        dodaj(
            f"Token entropy is relatively high ({token_entropy:.2f}), suggesting "
            f"a diverse and varied vocabulary more typical of human authorship.",
            "positive", "token_entropy"
        )

    perplexity = features.get("perplexity", -1)
    if perplexity != -1 and perplexity > 0:
        if perplexity < 8:
            dodaj(
                f"The code's perplexity score is very low ({perplexity:.1f}), meaning "
                f"a language model finds the token sequence highly predictable. "
                f"This strongly suggests the code was generated by a similar model.",
                "high", "perplexity"
            )
        elif perplexity < 20:
            dodaj(
                f"Perplexity ({perplexity:.1f}) falls within a range that is "
                f"moderately consistent with AI-generated code.",
                "medium", "perplexity"
            )
        elif perplexity > 50:
            dodaj(
                f"Perplexity is high ({perplexity:.1f}), indicating the code "
                f"contains patterns that a language model would consider unexpected — "
                f"a characteristic of human authorship.",
                "positive", "perplexity"
            )

    # ── FORMATIRANJE ───────────────────────────────────────────────────────

    # ── FORMATIRANJE I CISTOCA KODA ────────────────────────────────────────

    trailing = features.get("trailing_whitespace_ratio", 0)
    if trailing > 0.15:
        dodaj(
            f"A notable proportion of lines contain trailing whitespace "
            f"({trailing * 100:.0f}%), which is typical of code edited by hand.",
            "positive", "trailing_whitespace_ratio"
        )
    elif trailing == 0.0:
        # JAK SIGNAL: NIJEDAN trailing whitespace - AI generira savrseno cisto
        dodaj(
            f"The code contains zero trailing whitespace across all lines. "
            f"Hand-edited code almost always contains some accidental trailing spaces; "
            f"a perfectly clean state is a strong indicator of programmatic generation.",
            "high", "trailing_whitespace_ratio"
        )
    elif trailing < 0.02:
        dodaj(
            f"Trailing whitespace is unusually rare ({trailing * 100:.1f}%). "
            f"Human-written code typically contains some accidental whitespace.",
            "medium", "trailing_whitespace_ratio"
        )

    op_cons = features.get("operator_spacing_consistency", 0)
    if op_cons >= 0.98:
        dodaj(
            f"Spacing around operators is perfectly consistent throughout the submission "
            f"({op_cons * 100:.0f}%). AI models apply style conventions uniformly; "
            f"human programmers occasionally deviate, especially under time pressure.",
            "high", "operator_spacing_consistency"
        )
    elif op_cons > 0.90:
        dodaj(
            f"Operator spacing is highly consistent ({op_cons * 100:.0f}%).",
            "medium", "operator_spacing_consistency"
        )

    empty_ratio = features.get("empty_line_ratio", 0)
    if 0.05 <= empty_ratio <= 0.20:
        dodaj(
            f"The code uses well-spaced empty lines ({empty_ratio * 100:.0f}%) "
            f"to separate logical blocks. AI tends to apply this pattern systematically.",
            "medium", "empty_line_ratio"
        )

    # ── DUZINA LINIJA ──────────────────────────────────────────────────────

    avg_line = features.get("avg_line_length", 0)
    if avg_line > 60:
        dodaj(
            f"Lines are notably long on average ({avg_line:.0f} characters). "
            f"AI models often produce dense, single-line expressions; "
            f"human code tends to break logic across multiple shorter lines.",
            "high", "avg_line_length"
        )
    elif avg_line > 40:
        dodaj(
            f"Average line length ({avg_line:.0f} characters) is moderately high.",
            "medium", "avg_line_length"
        )

    max_line = features.get("max_line_length", 0)
    if max_line > 100:
        dodaj(
            f"One or more lines exceed {max_line:.0f} characters. "
            f"Very long single lines are common in AI-generated code "
            f"which prioritizes correctness over readability.",
            "medium", "max_line_length"
        )

    # ── STRUKTURNI OBRASCI ─────────────────────────────────────────────────

    for_d = features.get("for_density", 0)
    if_d  = features.get("if_density", 0)
    total_branch_density = for_d + if_d + features.get("while_density", 0)

    if for_d > 0.08:
        dodaj(
            f"The code contains a high density of for-loops "
            f"({for_d * 100:.1f}% of lines). AI generators tend to express logic "
            f"through explicit iteration even when alternatives exist.",
            "medium", "for_density"
        )

    if total_branch_density > 0.25:
        dodaj(
            f"Branching constructs (if/for/while) account for "
            f"{total_branch_density * 100:.0f}% of lines. AI-generated code "
            f"frequently exhibits dense control flow with explicit handling of every case.",
            "high", "control_flow_density"
        )

    # ── AST STRUKTURA ──────────────────────────────────────────────────────

    ast_depth = features.get("ast_depth", 0)
    if ast_depth >= 10:
        dodaj(
            f"Abstract syntax tree depth reaches {int(ast_depth)} levels. "
            f"AI tends to construct deeply nested expressions and produce "
            f"more uniformly structured code than student submissions.",
            "medium", "ast_depth"
        )

    ast_per_line = features.get("ast_nodes_per_line", 0)
    if ast_per_line > 8:
        dodaj(
            f"The code contains {ast_per_line:.1f} AST nodes per line on average, "
            f"indicating dense and complex expressions per statement — "
            f"a pattern typical of AI-generated solutions.",
            "medium", "ast_nodes_per_line"
        )

    unique_nodes = features.get("unique_node_type_ratio", 0)
    if unique_nodes < 0.30:
        dodaj(
            f"Only {unique_nodes * 100:.0f}% of AST node types are unique — "
            f"the code reuses the same structural patterns repeatedly. "
            f"AI-generated code often has lower structural diversity.",
            "medium", "unique_node_type_ratio"
        )

    # ── DUZINA IDENTIFIKATORA — DODATNE RAZINE ────────────────────────────

    # Moderate avg_identifier_length (4.5 - 5.5) signaliziraju umjereno opisno imenovanje
    if 4.5 <= avg_id_len < 5.5:
        dodaj(
            f"Identifier names average {avg_id_len:.1f} characters — "
            f"moderately descriptive, more verbose than typical student shorthand "
            f"but less so than fully AI-generated names.",
            "medium", "avg_identifier_length"
        )

    fn_name_len = features.get("avg_function_name_length", 0)
    if fn_name_len >= 15:
        dodaj(
            f"Function names average {fn_name_len:.0f} characters. "
            f"Verbose function naming (e.g. 'calculate_average_value') is a strong "
            f"marker of AI generation; students typically choose much shorter names.",
            "high", "avg_function_name_length"
        )

    # ── LEKSICKA RAZNOLIKOST ──────────────────────────────────────────────

    lex_div = features.get("lexical_diversity", 0)
    if lex_div < 0.40 and lex_div > 0:
        dodaj(
            f"Lexical diversity is low ({lex_div:.2f}) — the code reuses "
            f"the same vocabulary repeatedly. AI tends toward repetitive, "
            f"templated phrasing across the codebase.",
            "medium", "lexical_diversity"
        )

    # Ako nema signala, dodaj neutralnu poruku
    if not objasnjenja:
        if ai_prob > 0.5:
            dodaj(
                "No single dominant signal was identified; the classification is based "
                "on a combination of subtle stylistic and structural patterns.",
                "medium", "combined"
            )
        else:
            dodaj(
                "No strong AI-generation markers were detected. "
                "The submission's style and structure are consistent with human authorship.",
                "positive", "combined"
            )

    # Sortiraj: high → medium → positive/low
    priority = {"high": 0, "medium": 1, "low": 2, "positive": 3}
    objasnjenja.sort(key=lambda x: priority.get(x["severity"], 2))

    return objasnjenja


def predict(code: str, language: str = None, filename: str = None,
            model=None, scaler=None, feature_names=None, threshold: float = None) -> dict:
    """
    Analizira isječak koda i vraća procjenu vjerojatnosti AI podrijetla.

    Ako model/scaler/feature_names nisu proslijeđeni, automatski ih učita s diska.

    Parametri:
        code (str):          Izvorni kod za analizu.
        language (str):      Programski jezik (opcionalno, automatska detekcija).
        filename (str):      Ime datoteke (opcionalno, pomaže detekciji jezika).
        model:               Učitani model (opcionalno, za višekratnu upotrebu).
        scaler:              Učitani scaler (opcionalno).
        feature_names (list):Lista naziva značajki (opcionalno).

    Vraća:
        dict s ključevima:
            "ai_probability"  – float 0.0-1.0, vjerojatnost AI podrijetla
            "verdict"         – string s tumačenjem rezultata
            "detected_language" – prepoznati programski jezik
            "top_features"    – lista (naziv, vrijednost) top 5 značajki
            "all_features"    – rječnik svih izvučenih značajki
            "error"           – string s greškom, ili None ako je sve OK
    """
    # Učitaj model ako nije proslijeđen
    if model is None:
        model, scaler, feature_names, threshold = ucitaj_model()
    else:
        threshold = 0.65  # konzervativni default ako je model proslijeđen direktno

    if model is None:
        return {
            "ai_probability":     None,
            "verdict":            "Model nije dostupan",
            "detected_language":  None,
            "top_features":       [],
            "all_features":       {},
            "error": "Model nije treniran. Pokreni: python classifier.py"
        }

    # Provjera minimalne duljine — kratki kodovi nemaju dovoljno signala
    # za pouzdanu analizu i skloni su lažno pozitivnim rezultatima
    meaningful_lines = len([l for l in code.splitlines() if l.strip()])
    if meaningful_lines < MINIMUM_LINES:
        return {
            "ai_probability":    None,
            "verdict":           "Premalo koda za analizu",
            "detected_language": None,
            "top_features":      [],
            "all_features":      {},
            "error": (
                f"Analiza zahtijeva najmanje {MINIMUM_LINES} nepraznih linija koda. "
                f"Predani isječak ima {meaningful_lines} "
                f"({'liniju' if meaningful_lines == 1 else 'linije' if meaningful_lines < 5 else 'linija'})."
            )
        }

    # Izvuci značajke
    sve_znacajke = extract_all_features(
        code=code, language=language, filename=filename
    )

    # Složi feature vektor u TOČNO isti redosljed kao pri treniranju
    feature_vector = []
    for feat in feature_names:
        val = sve_znacajke.get(feat, 0.0)
        if feat == "perplexity" and val == PERPLEXITY_MISSING:
            val = 0.0
        feature_vector.append(float(val))

    X = np.array([feature_vector], dtype=np.float32)
    X_scaled = scaler.transform(X)

    # Predikcija
    ai_prob = float(model.predict_proba(X_scaled)[0][1])

    # Tumačenje — koristimo optimalni prag pronađen pri treniranju
    # Sve iznad threshold-a ide prema "AI", sve ispod prema "Human"
    ai_cutoff = threshold  # npr. 0.68 pronađen automatski
    if ai_prob >= min(ai_cutoff + 0.15, 0.90):
        verdict = "Vjerojatno AI"
    elif ai_prob >= ai_cutoff:
        verdict = "Moguće AI"
    elif ai_prob >= ai_cutoff - 0.20:
        verdict = "Nejasno"
    elif ai_prob >= ai_cutoff - 0.40:
        verdict = "Moguće čovječji"
    else:
        verdict = "Vjerojatno čovječji"

    # Top 5 značajki koje su doprinijele odluci
    # Dohvati importances iz base estimatora unutar CalibratedClassifierCV
    try:
        base_rf = model.calibrated_classifiers_[0].estimator
        importances = base_rf.feature_importances_
    except Exception:
        importances = np.ones(len(feature_names)) / len(feature_names)
    top_idx = np.argsort(importances)[::-1][:5]
    top_features = [
        {
            "name":       feature_names[i],
            "value":      round(feature_vector[i], 4),
            "importance": round(float(importances[i]), 4),
        }
        for i in top_idx
    ]

    # Generiraj objašnjenja zašto je kod klasificiran ovako
    objasnjenja = generate_explanations(sve_znacajke, ai_prob)

    return {
        "ai_probability":    round(ai_prob, 4),
        "verdict":           verdict,
        "detected_language": sve_znacajke.get("detected_language", "nepoznat"),
        "top_features":      top_features,
        "all_features":      sve_znacajke,
        "explanations":      objasnjenja,
        "error":             None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GLAVNI PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Treniranje klasifikatora")
    print("=" * 50)

    # Učitaj dataset
    print(f"\n  Učitavam dataset iz '{DATASET_PATH}'...")
    X, y, feature_names = ucitaj_dataset(DATASET_PATH)

    # ── UNDERSAMPLING ──────────────────────────────────────────────────────
    # Balansiramo klase uzimanjem max 3x više human primjera nego AI.
    # Bez ovoga model s 63:1 omjerom gotovo uvijek predviđa human.
    # Cilj: human ≈ 2-3x AI → model nauči obje klase jednako dobro.

    n_ai    = int(np.sum(y == 1))
    n_human = int(np.sum(y == 0))
    target_human = min(n_human, n_ai * 3)   # max 3x više human nego AI

    if n_human > target_human:
        print(f"\n  Undersampling: {n_human} → {target_human} human primjera")
        print(f"  (zadržavamo svih {n_ai} AI + {target_human} human = "
              f"{n_ai + target_human} ukupno, omjer {target_human//n_ai}:1)")

        rng = np.random.default_rng(42)
        human_idx = np.where(y == 0)[0]
        ai_idx    = np.where(y == 1)[0]

        # Nasumično uzimamo target_human primjera iz human klase
        chosen_human = rng.choice(human_idx, size=target_human, replace=False)

        # Spajamo s AI primjerima i miješamo
        all_idx = np.concatenate([chosen_human, ai_idx])
        rng.shuffle(all_idx)

        X = X[all_idx]
        y = y[all_idx]
        print(f"  Nakon undersamplinga: Human={int(np.sum(y==0))}, "
              f"AI={int(np.sum(y==1))}, Ukupno={len(y)}")
    # ──────────────────────────────────────────────────────────────────────

    # Treniraj
    model, scaler, metrics = treniraj(X, y, feature_names)

    # Spremi
    spremi_model(model, scaler, feature_names)

    # Brzi test predikcije
    print("\n" + "─" * 50)
    print("  BRZI TEST PREDIKCIJE")
    print("─" * 50)

    test_kodovi = {
        "AI Python": '''
def calculate_fibonacci(n: int) -> list:
    """
    Generate a Fibonacci sequence up to n terms.

    Args:
        n: The number of terms to generate.

    Returns:
        A list containing the Fibonacci sequence.
    """
    if n <= 0:
        raise ValueError("Number of terms must be positive.")
    fibonacci_sequence = [0, 1]
    for i in range(2, n):
        next_value = fibonacci_sequence[i - 1] + fibonacci_sequence[i - 2]
        fibonacci_sequence.append(next_value)
    return fibonacci_sequence[:n]
''',
        "Human Python": '''
def fib(n):
    # quick fib
    a, b = 0, 1
    res = []
    for _ in range(n):
        res.append(a)
        a, b = b, a+b
    return res
''',
    }

    for naziv, kod in test_kodovi.items():
        rezultat = predict(kod, model=model, scaler=scaler,
                          feature_names=feature_names)
        prob = rezultat["ai_probability"]
        verdict = rezultat["verdict"]
        lang = rezultat["detected_language"]
        print(f"\n  [{naziv}]")
        print(f"    Jezik:           {lang}")
        print(f"    AI vjerojatnost: {prob:.1%}")
        print(f"    Zaključak:       {verdict}")
        print(f"    Ključne značajke:")
        for feat in rezultat["top_features"]:
            print(f"      {feat['name']:<35} vrijednost={feat['value']:.4f}")

    print("\n" + "=" * 50)
    print("  Treniranje završeno.")
    print("  Sljedeći korak: python app.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
