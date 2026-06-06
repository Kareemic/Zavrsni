"""
app.py
======
Flask backend za web aplikaciju za detekciju AI generiranog koda.

Pokretanje:
    python app.py

API rute:
    GET  /api/health              — provjera radi li server
    POST /api/analyze             — analiza jednog isječka koda
    POST /api/analyze-batch       — analiza više isječaka odjednom
    POST /api/similarity          — međusobna sličnost više kodova

React frontend šalje zahtjeve na ove rute i prikazuje rezultate.
"""

import os
import json
import difflib
import warnings
warnings.filterwarnings("ignore")

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from classifier import predict, ucitaj_model
from feature_extraction import extract_all_features, analyze_lines


# ─────────────────────────────────────────────────────────────────────────────
# INICIJALIZACIJA
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# Putanja do buildan React aplikacije (postoji samo u produkciji)
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# CORS dopušta React frontendu (localhost:3000) da komunicira s ovim serverom
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Učitaj model jednom pri pokretanju servera
# (Ne učitavamo za svaki zahtjev — to bi bilo presporo)
print("Učitavam model...")
MODEL, SCALER, FEATURE_NAMES, THRESHOLD = ucitaj_model()

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
    """
    Računa sličnost između dva isječka koda kao broj između 0.0 i 1.0.

    Koristi SequenceMatcher koji gleda zajednične podnizove.
    0.0 = potpuno različiti kodovi
    1.0 = identični kodovi

    Ovo je korisno za otkrivanje je li više studenata koristilo isti AI prompt —
    tada će njihovi kodovi biti međusobno neobično slični.
    """
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
        "threshold":     round(THRESHOLD, 3) if THRESHOLD else 0.65,
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
        threshold=THRESHOLD,
    )

    # Dodaj anotacije sumnjivih linija za prikaz u code editoru
    rezultat["line_annotations"] = analyze_lines(
        code=kod,
        language=jezik,
        filename=datoteka,
    )

    return jsonify(rezultat)


@app.route("/api/analyze-batch", methods=["POST"])
def analyze_batch():
    """
    Analizira više isječaka koda — streaming verzija.

    Umjesto da čeka sve rezultate pa ih pošalje odjednom (što uzrokuje
    timeout kod velikog broja fajlova), šalje svaki rezultat čim je gotov
    kao Server-Sent Events (SSE) stream.

    Frontend čita stream liniju po liniju i ažurira UI u realnom vremenu.

    Format streama — svaka linija je JSON objekt jedne od ove dvije vrste:
        {"type": "result", "data": { ...rezultat za jedan fajl... }}
        {"type": "summary", "data": { ...ukupna statistika... }}
    """
    podaci = request.get_json(silent=True)
    if not podaci:
        return greska("Zahtjev mora sadržavati JSON tijelo.")

    submissions = podaci.get("submissions", [])
    if not submissions:
        return greska("Polje 'submissions' je prazno.")

    def generate():
        rezultati = []

        for sub in submissions:
            sub_id   = sub.get("id", "nepoznat")
            kod      = sub.get("code", "").strip()
            jezik    = sub.get("language")
            datoteka = sub.get("filename")

            if not kod:
                rez = {"id": sub_id, "error": "Prazni kod."}
            else:
                try:
                    rez = predict(
                        code=kod,
                        language=jezik,
                        filename=datoteka,
                        model=MODEL,
                        scaler=SCALER,
                        feature_names=FEATURE_NAMES,
                        threshold=THRESHOLD,
                    )
                    rez["id"] = sub_id
                    rez["line_annotations"] = analyze_lines(
                        code=kod,
                        language=jezik,
                        filename=datoteka,
                    )
                except Exception as e:
                    rez = {"id": sub_id, "error": str(e)}

            rezultati.append(rez)

            # Pošalji rezultat odmah — ne čekamo ostale
            yield json.dumps({"type": "result", "data": rez},
                             ensure_ascii=False) + "\n"

        # Na kraju pošalji summary
        probs = [
            r["ai_probability"]
            for r in rezultati
            if r.get("ai_probability") is not None
        ]
        summary = {
            "total":             len(rezultati),
            "high_risk":         sum(1 for p in probs if p >= 0.70),
            "medium_risk":       sum(1 for p in probs if 0.40 <= p < 0.70),
            "low_risk":          sum(1 for p in probs if p < 0.40),
            "avg_ai_probability": round(sum(probs) / len(probs), 4) if probs else 0.0,
        }
        yield json.dumps({"type": "summary", "data": summary},
                         ensure_ascii=False) + "\n"

    from flask import stream_with_context
    return app.response_class(
        stream_with_context(generate()),
        mimetype="application/x-ndjson",
        headers={
            "X-Accel-Buffering": "no",      # isključi nginx buffering ako postoji
            "Cache-Control":     "no-cache",
        }
    )


@app.route("/api/similarity", methods=["POST"])
def similarity():
    """
    Računa međusobnu sličnost između više kodova i vraća matricu sličnosti.

    Ovo otkriva je li više studenata predalo gotovo identičan kod
    — što sugerira korištenje istog AI prompta.

    Zahtjev (JSON):
        {
            "submissions": [
                {"id": "student_01", "code": "..."},
                {"id": "student_02", "code": "..."},
                ...
            ]
        }

    Odgovor (JSON):
        {
            "ids": ["student_01", "student_02", ...],
            "matrix": [
                [1.00, 0.87, 0.12, ...],   ← sličnost student_01 s ostalima
                [0.87, 1.00, 0.15, ...],
                ...
            ],
            "suspicious_pairs": [
                {
                    "id_a":       "student_01",
                    "id_b":       "student_02",
                    "similarity": 0.87
                },
                ...
            ]
        }

    suspicious_pairs sadrži sve parove sa sličnošću > 0.70
    (konfigurabilno, trenutno 70%).
    """
    podaci = request.get_json(silent=True)
    if not podaci:
        return greska("Zahtjev mora sadržavati JSON tijelo.")

    submissions = podaci.get("submissions", [])
    if len(submissions) < 2:
        return greska("Potrebna su najmanje 2 koda za usporedbu.")

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
# SERVIRANJE REACT FRONTENDA (produkcija)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """
    Servira buildan React app za sve rute koje nisu /api/*.
    Potrebno za client-side routing (React Router).
    """
    if os.path.isdir(FRONTEND_BUILD):
        target = os.path.join(FRONTEND_BUILD, path)
        if path and os.path.exists(target):
            return send_from_directory(FRONTEND_BUILD, path)
        return send_from_directory(FRONTEND_BUILD, "index.html")
    return jsonify({"error": "Frontend nije buildан. Pokreni: cd frontend && npm run build"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "=" * 50)
    print("  AI Code Detector — Backend")
    print("=" * 50)
    print(f"  Server pokrenut na: http://localhost:{port}")
    print("  API rute:")
    print("    GET  /api/health")
    print("    POST /api/analyze")
    print("    POST /api/analyze-batch")
    print("    POST /api/similarity")
    print("\n  Zaustavi server s Ctrl+C")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
