import os
import csv
import time

from datasets import load_dataset

from feature_extraction import extract_all_features


# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURACIJA
# ─────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR  = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "dataset.csv")

# Koliko primjera uzeti po datasetu (None = sve)
# Za prvi brzi test stavi npr. 500, za pravo treniranje None
MAX_SAMPLES_PER_DATASET = None


# ─────────────────────────────────────────────────────────────────────────────
# PARSERI ZA SVAKI DATASET
# Svaki dataset ima svoju strukturu — ove funkcije je normaliziraju
# u isti format: lista rječnika s ključevima "code", "label", "language"
# ─────────────────────────────────────────────────────────────────────────────

def parse_aigcodeset(max_samples=None):
    print("  Skidanje AIGCodeSet dataseta...")
    try:
        ds = load_dataset("basakdemirok/AIGCodeSet", split="train")
    except Exception as e:
        print(f"  [GREŠKA] Nije moguće skinuti AIGCodeSet: {e}")
        return []

    primjeri = []
    for row in ds:
        # Izvuci kod — provjeri moguće nazive kolona
        code = row.get("code") or row.get("source_code") or row.get("content") or ""
        if not code or not code.strip():
            continue

        # Odredi oznaku — sve što nije "human" je AI
        raw_label = str(row.get("label", "")).lower()
        if "human" in raw_label:
            label = 0  # ljudski kod
        else:
            label = 1  # AI generirani kod

        primjeri.append({
            "code":     code,
            "label":    label,
            "language": "python",   # AIGCodeSet je samo Python
            "source":   "AIGCodeSet",
        })

        if max_samples and len(primjeri) >= max_samples:
            break

    human_count = sum(1 for p in primjeri if p["label"] == 0)
    ai_count    = sum(1 for p in primjeri if p["label"] == 1)
    print(f"  Učitano {len(primjeri)} primjera "
          f"({human_count} human, {ai_count} AI)")
    return primjeri


def parse_ai_code_detection(max_samples=None):
    print("  Skidanje ai-code-detection dataseta...")
    try:
        ds = load_dataset("serafeimdossas/ai-code-detection", split="train")
    except Exception as e:
        print(f"  [GREŠKA] Nije moguće skinuti ai-code-detection: {e}")
        return []

    primjeri = []
    for row in ds:
        code = row.get("code") or row.get("solution") or row.get("content") or ""
        if not code or not code.strip():
            continue

        raw_label = str(row.get("label", "")).lower()
        if "human" in raw_label:
            label = 0
        else:
            label = 1

        primjeri.append({
            "code":     code,
            "label":    label,
            "language": "python",
            "source":   "ai-code-detection",
        })

        if max_samples and len(primjeri) >= max_samples:
            break

    human_count = sum(1 for p in primjeri if p["label"] == 0)
    ai_count    = sum(1 for p in primjeri if p["label"] == 1)
    print(f"  Učitano {len(primjeri)} primjera "
          f"({human_count} human, {ai_count} AI)")
    return primjeri


# ─────────────────────────────────────────────────────────────────────────────
# IZVLAČENJE ZNAČAJKI I SPREMANJE U CSV
# ─────────────────────────────────────────────────────────────────────────────

def procesiraj_i_spremi(primjeri: list, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    uspjesno = 0
    greske   = 0
    pisac    = None
    f        = None

    print(f"\n  Izvlačim značajke iz {len(primjeri)} primjera...")
    start_time = time.time()

    for i, primjer in enumerate(primjeri):

        # Ispis napretka svaki 100 primjera
        if i > 0 and i % 100 == 0:
            proteklo = time.time() - start_time
            preostalo = (proteklo / i) * (len(primjeri) - i)
            print(f"  [{i}/{len(primjeri)}] "
                  f"~{preostalo:.0f}s preostalo...", end="\r")

        try:
            # Izvuci sve značajke
            znacajke = extract_all_features(
                code=primjer["code"],
                language=primjer["language"],
            )

            # Dodaj oznaku i izvor uz značajke
            redak = {
                "label":  primjer["label"],
                **znacajke,
                "source": primjer["source"],
            }

            # Otvori CSV i piši zaglavlje samo pri prvom retku
            if pisac is None:
                f = open(output_path, "w", newline="", encoding="utf-8")
                pisac = csv.DictWriter(f, fieldnames=list(redak.keys()))
                pisac.writeheader()

            pisac.writerow(redak)
            uspjesno += 1

        except Exception as e:
            greske += 1
            if greske <= 5:   # ispiši samo prvih 5 grešaka
                print(f"\n  [UPOZORENJE] Greška na primjeru {i}: {e}")

    if f:
        f.close()

    trajanje = time.time() - start_time
    print(f"\n  Gotovo za {trajanje:.1f}s")
    print(f"  Uspješno: {uspjesno} / {len(primjeri)}")
    if greske:
        print(f"  Greške:   {greske} (preskočeni)")


# ─────────────────────────────────────────────────────────────────────────────
# STATISTIKA O DATASETU
# ─────────────────────────────────────────────────────────────────────────────

def ispisi_statistiku(csv_path: str) -> None:
    """
    Učita gotovi CSV i ispiše osnovnu statistiku:
    broj primjera, omjer klasa, raspodjela po sourceu.
    """
    if not os.path.exists(csv_path):
        print("  CSV ne postoji, nema statistike.")
        return

    redovi = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        redovi = list(reader)

    if not redovi:
        print("  CSV je prazan.")
        return

    ukupno    = len(redovi)
    human     = sum(1 for r in redovi if r["label"] == "0")
    ai        = sum(1 for r in redovi if r["label"] == "1")
    num_feats = len(redovi[0]) - 2   # -2 za label i source

    # Statistika po sourceu
    from collections import Counter
    sources = Counter(r["source"] for r in redovi)

    print(f"\n{'═' * 50}")
    print(f"  STATISTIKA DATASETA")
    print(f"{'═' * 50}")
    print(f"  Ukupno primjera:     {ukupno}")
    print(f"  Human (label=0):     {human}  ({100*human/ukupno:.1f}%)")
    print(f"  AI    (label=1):     {ai}  ({100*ai/ukupno:.1f}%)")
    print(f"  Broj značajki:       {num_feats}")
    print(f"\n  Po datasetu:")
    for source, count in sources.most_common():
        print(f"    {source:<30} {count}")
    print(f"\n  Spremljeno u: {csv_path}")
    print(f"{'═' * 50}\n")


# ─────────────────────────────────────────────────────────────────────────────
# GLAVNI PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Preuzimanje dataseta i izvlačenje značajki")
    print("=" * 50)

    print("\nKoji dataset želiš preuzeti?")
    print("  1 — AIGCodeSet (7.583 Python primjera)")
    print("  2 — ai-code-detection (Rosetta Code + CodeNet)")
    print("  3 — Oba spojena (preporučeno)")

    odabir = input("\nOdabir (1/2/3): ").strip()

    # Brzi test mod
    print("\nBrzi test mod? (uzima samo 200 primjera, brže za provjeru)")
    test_mod = input("(d/n, Enter za ne): ").strip().lower()
    max_s = 200 if test_mod in ("d", "da", "y", "yes") else MAX_SAMPLES_PER_DATASET

    # Skidanje odabranog dataseta
    print()
    svi_primjeri = []

    if odabir in ("1", "3"):
        svi_primjeri += parse_aigcodeset(max_samples=max_s)

    if odabir in ("2", "3"):
        svi_primjeri += parse_ai_code_detection(max_samples=max_s)

    if not svi_primjeri:
        print("\n  Nema primjera za procesiranje. Provjeri internetsku vezu.")
        return

    human_ukupno = sum(1 for p in svi_primjeri if p["label"] == 0)
    ai_ukupno    = sum(1 for p in svi_primjeri if p["label"] == 1)
    print(f"\n  Ukupno primjera za procesiranje: {len(svi_primjeri)}"
          f"  ({human_ukupno} human, {ai_ukupno} AI)")

    # Izvuci značajke i spremi CSV
    procesiraj_i_spremi(svi_primjeri, OUTPUT_FILE)

    # Ispiši statistiku
    ispisi_statistiku(OUTPUT_FILE)

    print("  Sljedeći korak: python classifier.py")


if __name__ == "__main__":
    main()
