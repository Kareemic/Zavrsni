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
)
from sklearn.preprocessing import StandardScaler

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
    "n_estimators":  300,    # broj stabala — više = stabilnije, ali sporije
    "max_depth":     None,   # bez ograničenja dubine (stabla rastu do čistih listova)
    "min_samples_leaf": 2,   # svaki list mora imati min. 2 primjera (smanjuje overfitting)
    "class_weight": "balanced",  # kompenzira neuravnotežene klase (više human nego AI)
    "random_state":  42,
    "n_jobs":       -1,      # koristi sve dostupne CPU jezgre
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

    # 3. Treniranje Random Foresta
    print("\n  Treniram Random Forest...")
    model = RandomForestClassifier(**RF_PARAMS)
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

    # 5. Cross-validation — pouzdanija procjena jer trenira/testira 5 puta
    print("\n  5-fold cross-validation (može potrajati minutu)...")
    X_scaled_full = scaler.transform(X)
    cv_scores = cross_val_score(
        model, X_scaled_full, y,
        cv=5, scoring="f1", n_jobs=-1
    )
    print(f"  CV F1 scores: {[f'{s:.3f}' for s in cv_scores]}")
    print(f"  CV F1 prosjek: {cv_scores.mean():.3f} "
          f"(±{cv_scores.std():.3f})")

    # Top 10 najvažnijih značajki
    importances = model.feature_importances_
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

    with open(MODEL_PATH,    "wb") as f: pickle.dump(model,         f)
    with open(SCALER_PATH,   "wb") as f: pickle.dump(scaler,        f)
    with open(FEATURES_PATH, "wb") as f: pickle.dump(feature_names, f)

    print(f"\n  Model spremljen u:          {MODEL_PATH}")
    print(f"  Scaler spremljen u:         {SCALER_PATH}")
    print(f"  Nazivi značajki spremljeni: {FEATURES_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# PREDIKCIJA — koristi se iz web aplikacije
# ─────────────────────────────────────────────────────────────────────────────

def ucitaj_model():
    """
    Učitava model, scaler i nazive značajki s diska.
    Poziva se jednom pri pokretanju web servera.

    Vraća:
        (model, scaler, feature_names) ili (None, None, None) ako model ne postoji.
    """
    if not all(os.path.exists(p) for p in [MODEL_PATH, SCALER_PATH, FEATURES_PATH]):
        return None, None, None

    with open(MODEL_PATH,    "rb") as f: model         = pickle.load(f)
    with open(SCALER_PATH,   "rb") as f: scaler        = pickle.load(f)
    with open(FEATURES_PATH, "rb") as f: feature_names = pickle.load(f)

    return model, scaler, feature_names



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
    num_fns  = features.get("num_functions", 1)
    if num_docs > 0 and num_fns > 0:
        doc_coverage = num_docs / num_fns
        if doc_coverage >= 0.9:
            dodaj(
                f"Every function in the submission includes a formal docstring "
                f"({num_docs} of {num_fns} functions documented). "
                f"Complete docstring coverage is a strong marker of AI-generated code; "
                f"students rarely document all functions unless explicitly required.",
                "high", "num_docstrings"
            )
        elif doc_coverage >= 0.5:
            dodaj(
                f"More than half of the functions include docstrings "
                f"({num_docs} of {num_fns}), which is above the student average.",
                "medium", "num_docstrings"
            )

    # ── STRUKTURNE ZNAČAJKE ────────────────────────────────────────────────

    avg_fn_len = features.get("avg_function_length", 0)
    if avg_fn_len > 20:
        dodaj(
            f"Functions are notably long on average ({avg_fn_len:.0f} lines). "
            f"AI models tend to produce complete, self-contained implementations; "
            f"students more often break logic across multiple smaller functions "
            f"or leave parts incomplete.",
            "medium", "avg_function_length"
        )
    elif avg_fn_len > 0 and avg_fn_len < 5:
        dodaj(
            f"Functions are very short on average ({avg_fn_len:.1f} lines), "
            f"which may indicate a human programmer's incremental coding style.",
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

    trailing = features.get("trailing_whitespace_ratio", 0)
    if trailing > 0.15:
        dodaj(
            f"A notable proportion of lines contain trailing whitespace "
            f"({trailing * 100:.0f}%), which is typical of code edited by hand "
            f"and inconsistent with AI-generated output.",
            "positive", "trailing_whitespace_ratio"
        )

    op_cons = features.get("operator_spacing_consistency", 0)
    if op_cons > 0.95:
        dodaj(
            f"Spacing around operators is perfectly consistent throughout the submission. "
            f"AI models apply style conventions uniformly; human programmers "
            f"occasionally deviate, particularly under time pressure.",
            "medium", "operator_spacing_consistency"
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
            model=None, scaler=None, feature_names=None) -> dict:
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
        model, scaler, feature_names = ucitaj_model()

    if model is None:
        return {
            "ai_probability":     None,
            "verdict":            "Model nije dostupan",
            "detected_language":  None,
            "top_features":       [],
            "all_features":       {},
            "error": "Model nije treniran. Pokreni: python classifier.py"
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

    # Tumačenje
    if ai_prob >= 0.80:
        verdict = "Vjerojatno AI"
    elif ai_prob >= 0.60:
        verdict = "Moguće AI"
    elif ai_prob >= 0.40:
        verdict = "Nejasno"
    elif ai_prob >= 0.20:
        verdict = "Moguće čovječji"
    else:
        verdict = "Vjerojatno čovječji"

    # Top 5 značajki koje su doprinijele odluci
    importances = model.feature_importances_
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
