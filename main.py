from feature_extraction import extract_all_features


# ─────────────────────────────────────────────────────────────────────────────
# UČITAVANJE MODELA
# ─────────────────────────────────────────────────────────────────────────────

MODEL_NAME = "Salesforce/codegen-350M-mono"


def ucitaj_model():
   
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        print(f"  Učitavam model '{MODEL_NAME}'...")
        print("  (Pri prvom pokretanju ovo može potrajati par minuta.)\n")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model     = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,   # float32 radi na CPU bez GPU-a
        )
        model.eval()   # isključi dropout — samo inferenca, ne treniranje

        num_params = sum(p.numel() for p in model.parameters()) // 1_000_000
        print(f"  Model učitan ({num_params}M parametara).\n")
        return model, tokenizer

    except ImportError:
        print("  [UPOZORENJE] transformers ili torch nisu instalirani.")
        print("  Pokreni: pip install transformers torch\n")
        return None, None

    except Exception as e:
        print(f"  [UPOZORENJE] Model nije mogao biti učitan: {e}\n")
        return None, None


# ─────────────────────────────────────────────────────────────────────────────
# UNOS KODA
# ─────────────────────────────────────────────────────────────────────────────

def ucitaj_kod() -> str:
   
    print("Zalijepi kod ispod, a kad završiš pritisni Enter dva puta:\n")
    linije = []
    prazni_zaredom = 0

    while True:
        linija = input()
        if linija == "":
            prazni_zaredom += 1
            if prazni_zaredom >= 2:
                break
            linije.append(linija)
        else:
            prazni_zaredom = 0
            linije.append(linija)

    return "\n".join(linije).strip()


def ucitaj_iz_datoteke(putanja: str) -> str:
    
    try:
        with open(putanja, "r", encoding="utf-8") as f:
            sadrzaj = f.read()
        print(f"  Učitano {len(sadrzaj.splitlines())} linija iz '{putanja}'.")
        return sadrzaj
    except FileNotFoundError:
        print(f"\n  [GREŠKA] Datoteka '{putanja}' nije pronađena.")
        print(  "  Provjeri je li datoteka u istom folderu kao main.py.")
        return ""
    except Exception as e:
        print(f"\n  [GREŠKA] Problem pri čitanju datoteke: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# ISPIS REZULTATA
# ─────────────────────────────────────────────────────────────────────────────

def ispisi_znacajke(features: dict) -> None:
    
    jezik = features.get("detected_language", "nepoznat")
    print(f"\n{'═' * 55}")
    print(f"  Prepoznat jezik: {jezik.upper()}")
    print(f"{'═' * 55}")

    # ── Stilska detekcija ──────────────────────────────────────
    print("\n  [ STILSKA DETEKCIJA — komentari, imenovanje, formatiranje ]\n")

    stilske = [
        ("Broj linija s komentarom",        "num_comment_lines"),
        ("Udio komentara (%)",               "comment_ratio"),
        ("Prosj. duljina komentara (rij.)",  "avg_comment_length_words"),
        ("Udio komentara u znakovima",       "comment_to_code_ratio"),
        ("Broj blok komentara",              "num_block_comments"),
        ("Broj docstringova / JSDoc",        "num_docstrings"),
        ("Prosj. duljina identifikatora",    "avg_identifier_length"),
        ("Prosj. duljina naziva funkcija",   "avg_function_name_length"),
        ("Udio jednoslovnih naziva",         "single_char_name_ratio"),
        ("Leksička raznolikost naziva",      "lexical_diversity"),
        ("Udio snake_case stila",            "snake_case_ratio"),
        ("Udio camelCase stila",             "camel_case_ratio"),
        ("Konzistentnost imenovanja",        "naming_consistency"),
        ("Ukupno linija",                    "total_lines"),
        ("Udio praznih linija",              "empty_line_ratio"),
        ("Prosj. duljina linije (znakovi)",  "avg_line_length"),
        ("Max duljina linije",               "max_line_length"),
        ("Koristi tabove (1=da, 0=ne)",      "uses_tabs"),
        ("Udio linija s trailing space",     "trailing_whitespace_ratio"),
        ("Konzistentnost razmaka operatori", "operator_spacing_consistency"),
    ]

    for naziv, kljuc in stilske:
        val = features.get(kljuc, "N/A")
        if isinstance(val, float):
            print(f"    {naziv:<38} {val:.4f}")
        else:
            print(f"    {naziv:<38} {val}")

    # ── Strukturna detekcija ───────────────────────────────────
    print("\n  [ STRUKTURNA DETEKCIJA — AST, složenost, tok kontrole ]\n")

    strukturne = [
        ("Dubina AST stabla",                "ast_depth"),
        ("Broj čvorova u AST stablu",        "ast_node_count"),
        ("Raznolikost tipova čvorova",       "unique_node_type_ratio"),
        ("Broj funkcija / metoda",           "num_functions"),
        ("Prosj. duljina funkcije (linije)", "avg_function_length"),
        ("Max duljina funkcije (linije)",    "max_function_length"),
        ("Prosj. broj argumenata",           "avg_args_per_function"),
        ("Broj klasa",                       "num_classes"),
        ("Broj importa",                     "num_imports"),
        ("Broj if naredbi",                  "num_if_statements"),
        ("Broj for petlji",                  "num_for_loops"),
        ("Broj while petlji",                "num_while_loops"),
        ("Broj try/catch blokova",           "num_try_blocks"),
        ("Broj lambda izraza",               "num_lambdas"),
        ("Max dubina ugniježđenosti",        "max_nesting_depth"),
        ("Prosj. dubina ugniježđenosti",     "avg_nesting_depth"),
        ("Aproks. ciklomatska složenost",    "cyclomatic_complexity_approx"),
    ]

    for naziv, kljuc in strukturne:
        val = features.get(kljuc, "N/A")
        if isinstance(val, float):
            print(f"    {naziv:<38} {val:.4f}")
        else:
            print(f"    {naziv:<38} {val}")

    # ── Statistička detekcija ──────────────────────────────────
    print("\n  [ STATISTIČKA DETEKCIJA — perplexity ]\n")

    perp     = features.get("perplexity", -1.0)
    dostupan = features.get("model_available", 0)

    if dostupan == 0:
        print("    Model nije učitan — perplexity nije izračunat.")
    else:
        print(f"    {'Perplexity':<38} {perp:.4f}")

        # Grubo tumačenje perplexityja za CodeGEN-350M
        if perp < 5:
            tumacenje = "vrlo nizak → vjerojatno AI"
        elif perp < 20:
            tumacenje = "nizak → moguće AI"
        elif perp < 60:
            tumacenje = "srednji → nejasno"
        else:
            tumacenje = "visok → vjerojatno čovjek"
        print(f"    {'Tumačenje':<38} {tumacenje}")

    print(f"\n{'═' * 55}")
    print(f"  Ukupno izvučeno značajki: {len(features) - 1}")
    print(f"{'═' * 55}\n")


# ─────────────────────────────────────────────────────────────────────────────
# GLAVNI PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Ekstraktor značajki koda")
    print("  (za detekciju AI generiranog koda)")
    print("=" * 55)

    # Pitaj korisnika želi li učitati model za perplexity
    print("\nŽeliš li učitati model za izračun perplexityja?")
    print("  d — Da (skida ~700 MB pri prvom pokretanju)")
    print("  n — Ne (perplexity će biti preskočen)\n")
    odabir_model = input("Odabir (d/n): ").strip().lower()

    model, tokenizer = None, None
    if odabir_model in ("d", "da", "y", "yes"):
        model, tokenizer = ucitaj_model()

    # Način unosa koda
    print("\nNačin unosa koda:")
    print("  1 — Zalijepi kod direktno u terminal")
    print("  2 — Učitaj iz datoteke (npr. kod.txt)")

    while True:
        print()
        odabir = input("Odaberi način unosa (1 ili 2): ").strip()

        if odabir == "1":
            kod = ucitaj_kod()

        elif odabir == "2":
            putanja = input("Putanja do datoteke (Enter za 'kod.txt'): ").strip()
            if putanja == "":
                putanja = "kod.txt"
            kod = ucitaj_iz_datoteke(putanja)

        else:
            print("  Unesi 1 ili 2.")
            continue

        if not kod:
            print("  Kod je prazan. Pokušaj ponovno.")
            continue

        print("\nIzvlačim značajke...")
        znacajke = extract_all_features(kod, model=model, tokenizer=tokenizer)
        ispisi_znacajke(znacajke)

        odgovor = input("Želiš li analizirati još jedan isječak koda? (da/ne): ")
        if odgovor.strip().lower() not in ("da", "d", "yes", "y"):
            print("\nZatvaram program.")
            break


if __name__ == "__main__":
    main()
