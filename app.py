import os
import json
import difflib
import warnings
warnings.filterwarnings("ignore")

from flask import Flask, request, jsonify
from flask_cors import CORS

from classifier import predict, ucitaj_model
from feature_extraction import extract_all_features


# ─────────────────────────────────────────────────────────────────────────────
# INICIJALIZACIJA
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# CORS dopušta React frontendu (localhost:3000) da komunicira s ovim serverom
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Učitaj model jednom pri pokretanju servera
# (Ne učitavamo za svaki zahtjev — to bi bilo presporo)
print("Učitavam model...")
MODEL, SCALER, FEATURE_NAMES = ucitaj_model()

if MODEL is None:
    print("UPOZORENJE: Model nije pronađen.")
    print("Pokreni prvo: python classifier.py")
else:
    print(f"Model učitan ({len(FEATURE_NAMES)} značajki).")


# ─────────────────────────────────────────────────────────────────────────────
# POMOĆNE FUNKCIJE
# ─────────────────────────────────────────────────────────────────────────────

def greska(poruka: str, status: int = 400):
    """Vraća JSON odgovor s greškom."""
    return jsonify({"error": poruka}), status


def izracunaj_slicnost(kod_a: str, kod_b: str) -> float:
    return difflib.SequenceMatcher(None, kod_a.strip(), kod_b.strip()).ratio()


# ─────────────────────────────────────────────────────────────────────────────
# RUTE
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """
    Provjera radi li server i je li model učitan.

    React frontend poziva ovo pri pokretanju da provjeri
    može li komunicirati sa serverom.

    Odgovor:
        {
            "status": "ok",
            "model_loaded": true,
            "feature_count": 40
        }
    """
    return jsonify({
        "status":        "ok",
        "model_loaded":  MODEL is not None,
        "feature_count": len(FEATURE_NAMES) if FEATURE_NAMES else 0,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analizira jedan isječak koda i vraća procjenu AI podrijetla.

    Zahtjev (JSON):
        {
            "code":     "def foo(x): return x",   ← obavezno
            "language": "python",                  ← opcionalno
            "filename": "main.py"                  ← opcionalno
        }

    Odgovor (JSON):
        {
            "ai_probability":    0.73,
            "verdict":           "Vjerojatno AI",
            "detected_language": "python",
            "top_features": [
                {"name": "avg_identifier_length", "value": 8.5, "importance": 0.084},
                ...
            ],
            "all_features": { ... },
            "error": null
        }
    """
    podaci = request.get_json(silent=True)
    if not podaci:
        return greska("Zahtjev mora sadržavati JSON tijelo.")

    kod = podaci.get("code", "").strip()
    if not kod:
        return greska("Polje 'code' je obavezno i ne smije biti prazno.")

    if len(kod) > 100_000:
        return greska("Kod je predugačak. Maksimalno 100.000 znakova.")

    jezik   = podaci.get("language")
    datoteka = podaci.get("filename")

    rezultat = predict(
        code=kod,
        language=jezik,
        filename=datoteka,
        model=MODEL,
        scaler=SCALER,
        feature_names=FEATURE_NAMES,
    )

    return jsonify(rezultat)


@app.route("/api/analyze-batch", methods=["POST"])
def analyze_batch():
   
    podaci = request.get_json(silent=True)
    if not podaci:
        return greska("Zahtjev mora sadržavati JSON tijelo.")

    submissions = podaci.get("submissions", [])
    if not submissions:
        return greska("Polje 'submissions' je prazno.")

    if len(submissions) > 200:
        return greska("Maksimalno 200 kodova po zahtjevu.")

    rezultati = []
    for sub in submissions:
        sub_id  = sub.get("id", "nepoznat")
        kod     = sub.get("code", "").strip()
        jezik   = sub.get("language")
        datoteka = sub.get("filename")

        if not kod:
            rezultati.append({
                "id":    sub_id,
                "error": "Prazni kod."
            })
            continue

        rez = predict(
            code=kod,
            language=jezik,
            filename=datoteka,
            model=MODEL,
            scaler=SCALER,
            feature_names=FEATURE_NAMES,
        )
        rez["id"] = sub_id
        rezultati.append(rez)

    # Sažetak za tablični prikaz
    probs = [
        r["ai_probability"]
        for r in rezultati
        if r.get("ai_probability") is not None
    ]

    summary = {
        "total":    len(rezultati),
        "high_risk":   sum(1 for p in probs if p >= 0.70),
        "medium_risk": sum(1 for p in probs if 0.40 <= p < 0.70),
        "low_risk":    sum(1 for p in probs if p < 0.40),
        "avg_ai_probability": round(sum(probs) / len(probs), 4) if probs else 0.0,
    }

    return jsonify({"results": rezultati, "summary": summary})


@app.route("/api/similarity", methods=["POST"])
def similarity():
    podaci = request.get_json(silent=True)
    if not podaci:
        return greska("Zahtjev mora sadržavati JSON tijelo.")

    submissions = podaci.get("submissions", [])
    if len(submissions) < 2:
        return greska("Potrebna su najmanje 2 koda za usporedbu.")

    if len(submissions) > 100:
        return greska("Maksimalno 100 kodova po zahtjevu.")

    ids   = [s.get("id", f"kod_{i}") for i, s in enumerate(submissions)]
    codes = [s.get("code", "") for s in submissions]
    n     = len(codes)

    # Izgradi n×n matricu sličnosti
    # matrix[i][j] = sličnost između koda i i koda j
    matrica = [[0.0] * n for _ in range(n)]
    sumnjivi_parovi = []

    for i in range(n):
        for j in range(n):
            if i == j:
                matrica[i][j] = 1.0
            elif j > i:
                sim = izracunaj_slicnost(codes[i], codes[j])
                matrica[i][j] = round(sim, 4)
                matrica[j][i] = round(sim, 4)

                # Označi kao sumnjivo ako je sličnost > 70%
                if sim > 0.70:
                    sumnjivi_parovi.append({
                        "id_a":       ids[i],
                        "id_b":       ids[j],
                        "similarity": round(sim, 4),
                    })

    # Sortiraj sumnjive parove po sličnosti (najsličniji prvi)
    sumnjivi_parovi.sort(key=lambda x: x["similarity"], reverse=True)

    return jsonify({
        "ids":              ids,
        "matrix":           matrica,
        "suspicious_pairs": sumnjivi_parovi,
    })


# ─────────────────────────────────────────────────────────────────────────────
# POKRETANJE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  AI Code Detector — Backend")
    print("=" * 50)
    print("  Server pokrenut na: http://localhost:5000")
    print("  API rute:")
    print("    GET  /api/health")
    print("    POST /api/analyze")
    print("    POST /api/analyze-batch")
    print("    POST /api/similarity")
    print("\n  Zaustavi server s Ctrl+C")
    print("=" * 50 + "\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,    
    )
