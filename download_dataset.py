"""
download_dataset.py
===================
Automatski skida besplatne datasete s HuggingFacea,
izvlači značajke i sprema u CSV za treniranje klasifikatora.

Pokretanje:
  pip install datasets
  python download_dataset.py
"""

import os
import csv
import time

from datasets import load_dataset
from feature_extraction import extract_all_features

OUTPUT_DIR  = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "dataset.csv")


# ─────────────────────────────────────────────────────────────────────────────
# POMOĆNA FUNKCIJA: prepoznavanje labela
# ─────────────────────────────────────────────────────────────────────────────

def parsiraj_label(raw_value) -> int:
    """
    Prepoznaje label bez obzira na format u datasetu.

    Podržani formati:
      - Integer:  0 → human,  1 → AI
      - String:   "human", "human-written", "Human_written" → human
                  sve ostalo → AI
      - Boolean:  False → human, True → AI

    Vraća:
        0 za human, 1 za AI
    """
    # Integer ili integer u stringu
    if isinstance(raw_value, (int, float)):
        return int(raw_value)

    # Boolean
    if isinstance(raw_value, bool):
        return 1 if raw_value else 0

    # String — normaliziramo i tražimo ključne riječi
    s = str(raw_value).lower().strip()

    # Eksplicitni integer u stringu
    if s in ("0",):  return 0
    if s in ("1",):  return 1

    # Opisni stringovi
    if any(k in s for k in ("human", "person", "manual", "real")):
        return 0  # human

    return 1  # AI (sve ostalo: model nazivi, "ai", "generated", itd.)


def debug_labeli(ds, dataset_name, n=5):
    """Ispiše prvih n labela da vidimo format."""
    print(f"  DEBUG {dataset_name} — prvih {n} labela:")
    for i, row in enumerate(ds):
        if i >= n: break
        raw = row.get("label", row.get("is_generated", row.get("source", "?")))
        print(f"    [{i}] raw='{raw}' ({type(raw).__name__}) → {parsiraj_label(raw)}")


# ─────────────────────────────────────────────────────────────────────────────
# PARSERI
# ─────────────────────────────────────────────────────────────────────────────

def parse_aigcodeset(max_samples=None):
    """
    AIGCodeSet — 4.755 human + 2.828 AI Python primjera.
    Generirani modeli: CodeLlama, Codestral, Gemini.
    """
    print("  Skidanje AIGCodeSet...")
    try:
        ds = load_dataset("basakdemirok/AIGCodeSet", split="train")
    except Exception as e:
        print(f"  [GREŠKA] {e}"); return []

    # Debug: prvih par labela da vidimo format
    debug_labeli(ds, "AIGCodeSet")

    primjeri = []
    for row in ds:
        code = (row.get("code") or row.get("source_code") or
                row.get("content") or "")
        if not code.strip(): continue

        # Probaj sve moguće kolone za label
        raw = (row.get("label") if row.get("label") is not None
               else row.get("is_generated") if row.get("is_generated") is not None
               else row.get("type", "1"))

        label = parsiraj_label(raw)

        primjeri.append({
            "code": code, "label": label,
            "language": "python", "source": "AIGCodeSet"
        })
        if max_samples and len(primjeri) >= max_samples: break

    h = sum(1 for p in primjeri if p["label"] == 0)
    a = sum(1 for p in primjeri if p["label"] == 1)
    print(f"  Učitano {len(primjeri)} ({h} human, {a} AI)")

    if h == 0:
        print("  UPOZORENJE: niti jedan human primjer nije prepoznat!")
        print("  Provjeri debug output iznad — možda je kolona drukčija.")

    return primjeri


def parse_ai_code_detection(max_samples=None):
    """
    ai-code-detection — 5.684 human + 6.143 AI Python primjera.
    Rosetta Code + CodeNet programski zadaci.
    """
    print("  Skidanje ai-code-detection...")
    try:
        ds = load_dataset("serafeimdossas/ai-code-detection", split="train")
    except Exception as e:
        print(f"  [GREŠKA] {e}"); return []

    debug_labeli(ds, "ai-code-detection")

    primjeri = []
    for row in ds:
        code = (row.get("code") or row.get("solution") or
                row.get("content") or "")
        if not code.strip(): continue

        raw = (row.get("label") if row.get("label") is not None
               else row.get("is_generated", "1"))
        label = parsiraj_label(raw)

        primjeri.append({
            "code": code, "label": label,
            "language": "python", "source": "ai-code-detection"
        })
        if max_samples and len(primjeri) >= max_samples: break

    h = sum(1 for p in primjeri if p["label"] == 0)
    a = sum(1 for p in primjeri if p["label"] == 1)
    print(f"  Učitano {len(primjeri)} ({h} human, {a} AI)")
    return primjeri


def parse_mbpp(max_samples=None):
    """MBPP — 374 Python zadataka pisanih od programera."""
    print("  Skidanje MBPP (human Python)...")
    try:
        ds = load_dataset("google-research-datasets/mbpp", split="train")
    except Exception as e:
        print(f"  [GREŠKA] {e}"); return []

    primjeri = []
    for row in ds:
        code = row.get("code") or ""
        if not code.strip(): continue
        primjeri.append({
            "code": code, "label": 0,
            "language": "python", "source": "MBPP"
        })
        if max_samples and len(primjeri) >= max_samples: break

    print(f"  Učitano {len(primjeri)} MBPP primjera (sve human)")
    return primjeri


def parse_humaneval(max_samples=None):
    """HumanEval — 164 Python benchmark funkcija (human rješenja)."""
    print("  Skidanje HumanEval (human Python)...")
    try:
        ds = load_dataset("openai/openai_humaneval", split="test")
    except Exception as e:
        print(f"  [GREŠKA] {e}"); return []

    primjeri = []
    for row in ds:
        code = row.get("canonical_solution") or ""
        if not code.strip() or len(code.splitlines()) < 2: continue
        primjeri.append({
            "code": code, "label": 0,
            "language": "python", "source": "HumanEval"
        })
        if max_samples and len(primjeri) >= max_samples: break

    print(f"  Učitano {len(primjeri)} HumanEval primjera (sve human)")
    return primjeri


# ─────────────────────────────────────────────────────────────────────────────
# OBRADA I SPREMANJE
# ─────────────────────────────────────────────────────────────────────────────

def procesiraj_i_spremi(primjeri, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    uspjesno = greske = 0
    pisac = f = None
    start = time.time()
    print(f"\n  Izvlačim značajke iz {len(primjeri)} primjera...")

    for i, primjer in enumerate(primjeri):
        if i > 0 and i % 100 == 0:
            proteklo = time.time() - start
            preostalo = (proteklo / i) * (len(primjeri) - i)
            print(f"  [{i}/{len(primjeri)}]  ~{preostalo:.0f}s preostalo...", end="\r")
        try:
            znacajke = extract_all_features(
                code=primjer["code"],
                language=primjer["language"]
            )
            redak = {"label": primjer["label"], **znacajke, "source": primjer["source"]}
            if pisac is None:
                f = open(output_path, "w", newline="", encoding="utf-8")
                pisac = csv.DictWriter(f, fieldnames=list(redak.keys()))
                pisac.writeheader()
            pisac.writerow(redak)
            uspjesno += 1
        except Exception as e:
            greske += 1
            if greske <= 5:
                print(f"\n  [UPOZORENJE] Primjer {i}: {e}")

    if f: f.close()
    print(f"\n  Gotovo za {time.time()-start:.1f}s")
    print(f"  Uspješno: {uspjesno} / {len(primjeri)}")
    if greske: print(f"  Greške: {greske}")


def ispisi_statistiku(csv_path):
    if not os.path.exists(csv_path): return
    redovi = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    if not redovi: return
    ukupno = len(redovi)
    human  = sum(1 for r in redovi if r["label"] == "0")
    ai     = sum(1 for r in redovi if r["label"] == "1")
    from collections import Counter
    sources = Counter(r["source"] for r in redovi)

    print(f"\n{'═'*50}")
    print(f"  STATISTIKA DATASETA")
    print(f"{'═'*50}")
    print(f"  Ukupno:    {ukupno}")
    print(f"  Human (0): {human}  ({100*human/ukupno:.1f}%)")
    print(f"  AI    (1): {ai}  ({100*ai/ukupno:.1f}%)")
    print(f"  Značajki:  {len(redovi[0]) - 2}")
    print(f"\n  Po datasetu:")
    for src, cnt in sources.most_common():
        print(f"    {src:<35} {cnt}")
    print(f"  Omjer human:AI = 1:{ai//max(human,1):.1f}")
    print(f"\n  Spremljeno u: {csv_path}")
    print(f"{'═'*50}\n")


# ─────────────────────────────────────────────────────────────────────────────
# GLAVNI PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Preuzimanje dataseta i izvlačenje značajki")
    print("=" * 50)

    print("""
Koji dataset želiš preuzeti?

  1 — AIGCodeSet          (4.755 human + 2.828 AI)
  2 — ai-code-detection   (5.684 human + 6.143 AI)
  3 — Opcije 1 + 2        (preporučeno)
  4 — Sve + MBPP + HumanEval (najviše podataka)
""")

    odabir = input("Odabir (1/2/3/4): ").strip()

    print("\nBrzi test mod? (200 primjera, provjera parsera)")
    test_mod = input("(d/n, Enter za ne): ").strip().lower()
    max_s = 200 if test_mod in ("d", "da", "y", "yes") else None

    print()
    svi_primjeri = []

    if odabir in ("1", "3", "4"):
        svi_primjeri += parse_aigcodeset(max_samples=max_s)

    if odabir in ("2", "3", "4"):
        svi_primjeri += parse_ai_code_detection(max_samples=max_s)

    if odabir in ("4",):
        svi_primjeri += parse_mbpp(max_samples=max_s)
        svi_primjeri += parse_humaneval(max_samples=max_s)

    if not svi_primjeri:
        print("\n  Nema primjera. Provjeri internet i odabir.")
        return

    h = sum(1 for p in svi_primjeri if p["label"] == 0)
    a = sum(1 for p in svi_primjeri if p["label"] == 1)
    print(f"\n  Ukupno: {len(svi_primjeri)}  ({h} human, {a} AI)")

    if h == 0:
        print("\n  GREŠKA: Nijedan human primjer nije pronađen!")
        print("  Provjeri debug output iznad.")
        return

    omjer = a / max(h, 1)
    print(f"  Omjer AI:human = {omjer:.1f}:1")
    if omjer > 5:
        print("  UPOZORENJE: Dataset je nebalansiran (>5:1).")
        print("  classifier.py će primijeniti undersampling.")

    procesiraj_i_spremi(svi_primjeri, OUTPUT_FILE)
    ispisi_statistiku(OUTPUT_FILE)
    print("  Sljedeći korak: python classifier.py")


if __name__ == "__main__":
    main()
