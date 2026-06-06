"""
feature_extraction.py
=====================
Višejezično izvlačenje značajki iz programskog koda.

Podržani jezici: Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, Ruby

Organizirano po načinima detekcije:
  1. Stilska detekcija     – komentari, imenovanje, formatiranje
  2. Strukturna detekcija  – AST analiza, složenost, tok kontrole
  3. Statistička detekcija – perplexity pomoću jezičnog modela

Glavna funkcija:
    extract_all_features(code, language=None, filename=None) -> dict
"""

import re
import math
from collections import Counter
from tree_sitter import Language, Parser

from language_config import (
    get_config,
    detect_language_from_code,
    detect_language_from_extension,
)


# ─────────────────────────────────────────────────────────────────────────────
# POMOĆNE FUNKCIJE
# ─────────────────────────────────────────────────────────────────────────────

def _safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Dijeljenje koje ne puca na nuli."""
    return a / b if b != 0 else default


def _get_lines(code: str) -> list:
    """Vraća sve linije koda kao listu stringova."""
    return code.splitlines()


def _build_tree(code: str, ts_module):
    """
    Parsira kod pomoću Tree-sitter i vraća stablo.
    Koristi modul specifičan za jezik (npr. tree_sitter_python).
    Vraća None ako parsiranje ne uspije.
    """
    try:
        lang = Language(ts_module.language())
        parser = Parser(lang)
        return parser.parse(code.encode("utf-8", errors="replace"))
    except Exception:
        return None


def _walk_tree(node) -> list:
    """
    Prolazi kroz cijelo Tree-sitter stablo i vraća listu svih čvorova.
    Ekvivalent ast.walk() iz Pythonovog standardnog modula.
    """
    result = [node]
    for child in node.children:
        result.extend(_walk_tree(child))
    return result


def _count_node_types(all_nodes: list, type_names: list) -> int:
    """Broji koliko se puta pojavljuje bilo koji od zadanih tipova čvorova."""
    if not type_names:
        return 0
    return sum(1 for n in all_nodes if n.type in type_names)


def _get_node_depth(node, current: int = 0) -> int:
    """Rekurzivno računa maksimalnu dubinu stabla."""
    if not node.children:
        return current
    return max(_get_node_depth(child, current + 1) for child in node.children)


# ─────────────────────────────────────────────────────────────────────────────
# NAČIN 1: STILSKA DETEKCIJA
# ─────────────────────────────────────────────────────────────────────────────

def extract_style_features(code: str, lang_config: dict) -> dict:
    """
    Izvlači stilske značajke iz koda.

    Radi za sve jezike jer:
      - komentare prepoznaje regex obrascem iz lang_config
        (svaki jezik ima drugu sintaksu komentara)
      - identifikatore uzima iz Tree-sitter stabla
        (tree-sitter radi za sve podržane jezike)
      - formatiranje gleda direktno po linijama
        (potpuno universalno — vrijedi za sve jezike)

    Parametri:
        code (str):         Izvorni kod kao string.
        lang_config (dict): Konfiguracija jezika iz language_config.py.

    Vraća:
        dict: Stilske značajke s float/int vrijednostima.
    """
    lines = _get_lines(code)
    total_lines = len(lines) if lines else 1

    # ── KOMENTARI ──────────────────────────────────────────────────────────
    # Svaki jezik ima drugačiji simbol — Python koristi #, Java/JS koriste //
    # Regex obrazac je definiran u language_config.py za svaki jezik.

    inline_pat = lang_config["inline_comment"]
    comment_lines = [l for l in lines if re.match(inline_pat, l)]
    num_comment_lines = len(comment_lines)

    # Prosječna duljina komentara u riječima
    comment_words_total = sum(
        len(re.sub(inline_pat, "", l).strip().split())
        for l in comment_lines
    )
    avg_comment_length_words = _safe_divide(comment_words_total, num_comment_lines)

    # Blok komentari: /* ... */ u Java/JS/C, =begin...=end u Ruby
    num_block_comments = 0
    if lang_config["block_comment"]:
        start, end = lang_config["block_comment"]
        num_block_comments = len(re.findall(
            re.escape(start) + r"[\s\S]*?" + re.escape(end),
            code
        ))

    # Ukupan udio komentara u znakovima
    total_comment_chars = sum(len(l) for l in comment_lines)
    comment_to_code_ratio = _safe_divide(total_comment_chars, max(len(code), 1))

    # Dokumentacijski komentari (docstring, JSDoc, Javadoc...)
    num_docstrings = 0
    if lang_config.get("docstring_pattern"):
        num_docstrings = len(re.findall(lang_config["docstring_pattern"], code))

    # ── IMENOVANJE (iz Tree-sitter stabla) ────────────────────────────────
    # Tree-sitter za svaki jezik daje čvorove tipa "identifier"
    # koji sadrže nazive varijabli, funkcija, argumenata itd.

    identifier_names = []
    function_names = []

    tree = _build_tree(code, lang_config["ts_module"])
    if tree:
        all_nodes = _walk_tree(tree.root_node)
        id_types = lang_config["node_types"].get("identifier", ["identifier"])
        fn_types = lang_config["node_types"].get("function", [])

        # Skupljamo sve identifikatore
        for node in all_nodes:
            if node.type in id_types and node.text:
                name = node.text.decode("utf-8", errors="replace")
                if len(name) >= 1:
                    identifier_names.append(name)

        # Skupljamo nazive funkcija — tražimo "identifier" dijete
        # unutar čvora koji označava funkciju
        for node in all_nodes:
            if node.type in fn_types:
                for child in node.children:
                    if child.type in id_types and child.text:
                        fn_name = child.text.decode("utf-8", errors="replace")
                        function_names.append(fn_name)
                        break

    avg_identifier_length = _safe_divide(
        sum(len(n) for n in identifier_names), len(identifier_names)
    )
    avg_function_name_length = _safe_divide(
        sum(len(n) for n in function_names), len(function_names)
    )

    # Jednoslovna imena (i, x, n, k...) — čovječji kod ih ima više
    single_char_count = sum(1 for n in identifier_names if len(n) == 1)
    single_char_ratio = _safe_divide(single_char_count, len(identifier_names))

    # Leksička raznolikost: visoka = raznovrsni nazivi (čovjek), niska = AI ponavlja obrasce
    lexical_diversity = _safe_divide(
        len(set(identifier_names)), len(identifier_names)
    )

    # Konvencije imenovanja
    def is_snake_case(n):
        return "_" in n and n == n.lower() and not n.startswith("_")

    def is_camel_case(n):
        return (len(n) > 1 and not n.startswith("_")
                and n[0].islower() and any(c.isupper() for c in n)
                and "_" not in n)

    def is_pascal_case(n):
        return (len(n) > 1 and n[0].isupper()
                and any(c.islower() for c in n) and "_" not in n)

    total_ids = max(len(identifier_names), 1)
    snake_count  = sum(1 for n in identifier_names if is_snake_case(n))
    camel_count  = sum(1 for n in identifier_names if is_camel_case(n))
    pascal_count = sum(1 for n in identifier_names if is_pascal_case(n))

    snake_ratio = _safe_divide(snake_count, total_ids)
    camel_ratio = _safe_divide(camel_count, total_ids)

    # Konzistentnost imenovanja: 1.0 = svi identifikatori u istom stilu (tipično AI)
    naming_consistency = _safe_divide(
        max(snake_count, camel_count, pascal_count), total_ids
    )

    # ── FORMATIRANJE (potpuno universalno za sve jezike) ───────────────────

    non_empty_lines = [l for l in lines if l.strip()]
    empty_line_ratio = _safe_divide(total_lines - len(non_empty_lines), total_lines)

    line_lengths = [len(l) for l in non_empty_lines] if non_empty_lines else [0]
    avg_line_length = _safe_divide(sum(line_lengths), len(line_lengths))
    max_line_length = max(line_lengths) if line_lengths else 0

    # Tabovi vs razmaci za uvlačenje
    tab_lines = sum(1 for l in lines if l.startswith("\t"))
    uses_tabs = int(tab_lines > len(lines) * 0.1)

    # Trailing whitespace — razmaci na kraju linije
    trailing_ws = sum(1 for l in lines if l != l.rstrip())
    trailing_ws_ratio = _safe_divide(trailing_ws, total_lines)

    # Konzistentnost razmaka oko operatora (= == != < >...)
    with_space    = len(re.findall(r"\s[=!<>]=?\s", code))
    without_space = len(re.findall(r"[^\s=!<>][=!<>]=[^\s=]", code))
    operator_consistency = _safe_divide(
        max(with_space, without_space), with_space + without_space
    )

    return {
        # Komentari
        "num_comment_lines":            num_comment_lines,
        "comment_ratio":                _safe_divide(num_comment_lines, total_lines),
        "avg_comment_length_words":     avg_comment_length_words,
        "comment_to_code_ratio":        comment_to_code_ratio,
        "num_block_comments":           num_block_comments,
        "num_docstrings":               num_docstrings,
        # Imenovanje
        "avg_identifier_length":        avg_identifier_length,
        "avg_function_name_length":     avg_function_name_length,
        "single_char_name_ratio":       single_char_ratio,
        "lexical_diversity":            lexical_diversity,
        "snake_case_ratio":             snake_ratio,
        "camel_case_ratio":             camel_ratio,
        "naming_consistency":           naming_consistency,
        # Formatiranje
        "total_lines":                  total_lines,
        "empty_line_ratio":             empty_line_ratio,
        "avg_line_length":              avg_line_length,
        "max_line_length":              max_line_length,
        "uses_tabs":                    uses_tabs,
        "trailing_whitespace_ratio":    trailing_ws_ratio,
        "operator_spacing_consistency": operator_consistency,
    }


# ─────────────────────────────────────────────────────────────────────────────
# NAČIN 2: STRUKTURNA DETEKCIJA
# ─────────────────────────────────────────────────────────────────────────────

def extract_structural_features(code: str, lang_config: dict) -> dict:
    """
    Izvlači strukturne značajke iz koda pomoću Tree-sitter AST analize.

    Tree-sitter radi za sve podržane jezike — jedina razlika su nazivi
    čvorova (npr. "function_definition" u Pythonu vs "method_declaration"
    u Javi), a to je riješeno kroz lang_config["node_types"].

    Parametri:
        code (str):         Izvorni kod kao string.
        lang_config (dict): Konfiguracija jezika iz language_config.py.

    Vraća:
        dict: Strukturne značajke, ili rječnik nula ako parsiranje ne uspije.
    """
    empty_result = {k: 0 for k in [
        "ast_depth", "ast_node_count", "unique_node_type_ratio",
        "num_functions", "avg_function_length", "max_function_length",
        "avg_args_per_function", "num_classes", "num_imports",
        "num_if_statements", "num_for_loops", "num_while_loops",
        "num_try_blocks", "num_lambdas",
        "max_nesting_depth", "avg_nesting_depth",
        "cyclomatic_complexity_approx",
    ]}

    tree = _build_tree(code, lang_config["ts_module"])
    if tree is None:
        return empty_result

    root = tree.root_node
    all_nodes = _walk_tree(root)
    nt = lang_config["node_types"]

    # ── AST STABLO ─────────────────────────────────────────────────────────

    ast_depth = _get_node_depth(root)
    ast_node_count = len(all_nodes)
    node_type_counts = Counter(n.type for n in all_nodes)
    unique_node_type_ratio = _safe_divide(len(node_type_counts), ast_node_count)

    # ── FUNKCIJE ───────────────────────────────────────────────────────────

    function_nodes = [n for n in all_nodes if n.type in nt.get("function", [])]
    num_functions = len(function_nodes)

    # Duljina svake funkcije u linijama koda
    function_lengths = [
        fn.end_point[0] - fn.start_point[0] + 1
        for fn in function_nodes
    ]
    avg_function_length = _safe_divide(sum(function_lengths), len(function_lengths))
    max_function_length = max(function_lengths) if function_lengths else 0

    # Broj parametara po funkciji
    args_counts = []
    for fn in function_nodes:
        for child in fn.children:
            if child.type in ("parameters", "formal_parameters",
                              "parameter_list", "argument_list"):
                params = [c for c in child.children
                          if c.type not in ("(", ")", ",", "self")]
                args_counts.append(len(params))
                break
    avg_args_per_function = _safe_divide(sum(args_counts), len(args_counts))

    # ── KLASE I IMPORTI ────────────────────────────────────────────────────

    num_classes = _count_node_types(all_nodes, nt.get("class", []))
    num_imports = _count_node_types(all_nodes, nt.get("import", []))

    # ── TOK KONTROLE ───────────────────────────────────────────────────────

    num_if      = _count_node_types(all_nodes, nt.get("if", []))
    num_for     = _count_node_types(all_nodes, nt.get("for", []))
    num_while   = _count_node_types(all_nodes, nt.get("while", []))
    num_try     = _count_node_types(all_nodes, nt.get("try", []))
    num_lambdas = _count_node_types(all_nodes, nt.get("lambda", []))

    # ── DUBINA UGNIJEŽĐENOSTI ──────────────────────────────────────────────

    nesting_types = set(
        nt.get("if", []) + nt.get("for", []) +
        nt.get("while", []) + nt.get("function", [])
    )

    def collect_depths(node, depth=0):
        depths = []
        for child in node.children:
            if child.type in nesting_types:
                depths.append(depth + 1)
                depths.extend(collect_depths(child, depth + 1))
            else:
                depths.extend(collect_depths(child, depth))
        return depths

    nesting_depths = collect_depths(root)
    max_nesting_depth = max(nesting_depths) if nesting_depths else 0
    avg_nesting_depth = _safe_divide(sum(nesting_depths), len(nesting_depths))

    # ── APROKSIMACIJA CIKLOMATSKE SLOŽENOSTI ──────────────────────────────
    # CC ≈ 1 + broj grananja, dijeljeno brojem funkcija
    # Standardna aproksimacija koja radi za sve jezike.

    total_branches = 1 + num_if + num_for + num_while + num_try
    cyclomatic_approx = (
        _safe_divide(total_branches, num_functions)
        if num_functions > 0
        else float(total_branches)
    )

    # ── NORMALIZACIJA PO VELIČINI KODA ────────────────────────────────────
    # Apsolutni brojevi (num_if, num_for...) ovise o veličini koda.
    # Dijeljenjem s brojem nepraznih linija dobivamo gustoću koja je
    # usporediva između kratkih i dugih kodova.
    # Npr. 3 if-a u 10 linija (0.30) vs 3 if-a u 100 linija (0.03)
    # — apsolutni broj je isti, ali gustoća govori pravu priču.

    lines_all = _get_lines(code)
    non_empty = max(sum(1 for l in lines_all if l.strip()), 1)

    if_density       = _safe_divide(num_if,        non_empty)
    for_density      = _safe_divide(num_for,       non_empty)
    while_density    = _safe_divide(num_while,     non_empty)
    try_density      = _safe_divide(num_try,       non_empty)
    function_density = _safe_divide(num_functions, non_empty)
    class_density    = _safe_divide(num_classes,   non_empty)
    import_density   = _safe_divide(num_imports,   non_empty)
    lambda_density   = _safe_divide(num_lambdas,   non_empty)

    # Broj AST čvorova po liniji — AI kod ima predvidljive strukture
    ast_nodes_per_line = _safe_divide(ast_node_count, non_empty)

    # ── ENTROPIJA KODA ────────────────────────────────────────────────────
    # Entropija mjeri raznolikost i nepredvidljivost koda.
    # Visoka entropija = raznolik, nepredvidljiv kod = vjerojatno čovjek
    # Niska entropija  = ponavljajući, predvidljiv kod = možda AI
    #
    # Formula: H = -sum(p * log2(p)) za svaki jedinstveni element

    import math as _math
    from collections import Counter as _Counter

    # Entropija znakova — distribucija pojedinih znakova u kodu
    char_counts = _Counter(code)
    total_chars = len(code) if code else 1
    char_entropy = -sum(
        (c / total_chars) * _math.log2(c / total_chars)
        for c in char_counts.values()
    )

    # Entropija tokena — raznolikost na razini imenskih jedinica i simbola
    # Bolji signal od entropije znakova jer gleda smislene jezične jedinice
    tokens = re.findall(r"[a-zA-Z_]\w*|[0-9]+|[^\w\s]", code)
    token_counts = _Counter(tokens)
    total_tokens = len(tokens) if tokens else 1
    token_entropy = -sum(
        (c / total_tokens) * _math.log2(c / total_tokens)
        for c in token_counts.values()
    )

    return {
        # AST metrike (neovisne o veličini)
        "ast_depth":                    ast_depth,
        "unique_node_type_ratio":       unique_node_type_ratio,
        "ast_nodes_per_line":           ast_nodes_per_line,
        # Funkcije (prosjeci su već neovisni o veličini)
        "avg_function_length":          avg_function_length,
        "max_function_length":          max_function_length,
        "avg_args_per_function":        avg_args_per_function,
        # Gustoće — normalizirane po nepraznim linijama koda
        "function_density":             function_density,
        "class_density":                class_density,
        "import_density":               import_density,
        "if_density":                   if_density,
        "for_density":                  for_density,
        "while_density":                while_density,
        "try_density":                  try_density,
        "lambda_density":               lambda_density,
        # Ugniježđenost i složenost (već neovisni o veličini)
        "max_nesting_depth":            max_nesting_depth,
        "avg_nesting_depth":            avg_nesting_depth,
        "cyclomatic_complexity_approx": cyclomatic_approx,
        # Entropija
        "char_entropy":                 char_entropy,
        "token_entropy":                token_entropy,
    }


# ─────────────────────────────────────────────────────────────────────────────
# NAČIN 3: STATISTIČKA DETEKCIJA (Perplexity)
# ─────────────────────────────────────────────────────────────────────────────

def extract_statistical_features(code: str, model=None, tokenizer=None) -> dict:
    """
    Računa perplexity koda pomoću jezičnog modela.

    Niski perplexity → model je "očekivao" kod → vjerojatno AI.
    Visoki perplexity → model je "iznenađen" → vjerojatno čovjek.

    Metoda je jezično-agnostična — isti model prima kod u bilo kojem jeziku.
    Ako model nije proslijeđen (None), vraća -1 i ostatak pipeline-a nastavlja
    normalno bez statističke značajke.
    """
    if model is None or tokenizer is None:
        return {"perplexity": -1.0, "model_available": 0}

    try:
        import torch

        inputs = tokenizer(
            code, return_tensors="pt", truncation=True, max_length=512
        )
        with torch.no_grad():
            outputs = model(inputs["input_ids"], labels=inputs["input_ids"])
            loss = outputs.loss

        perplexity = math.exp(loss.item())

    except Exception as e:
        print(f"  [UPOZORENJE] Perplexity nije izračunat: {e}")
        perplexity = -1.0

    return {"perplexity": perplexity, "model_available": 1}


# ─────────────────────────────────────────────────────────────────────────────
# KOMBINIRANA FUNKCIJA — ulazna točka
# ─────────────────────────────────────────────────────────────────────────────

def extract_all_features(
    code: str,
    language=None,
    filename=None,
    model=None,
    tokenizer=None,
) -> dict:
    """
    Izvlači SVE značajke iz koda u jednom pozivu.

    Jezik se određuje ovim redoslijedom:
      1. Argument language (ako je zadan)
      2. Nastavak datoteke iz filename (ako je zadan)
      3. Heuristike iz samog koda (automatska detekcija)

    Parametri:
        code (str):          Izvorni kod kao string.
        language (str|None): Naziv jezika (npr. "python", "java").
        filename (str|None): Ime datoteke (npr. "main.py").
        model:               (opcionalno) HuggingFace model za perplexity.
        tokenizer:           (opcionalno) HuggingFace tokenizator.

    Vraća:
        dict: Sve značajke + ključ "detected_language".
    """
    # Određivanje jezika
    if language is not None:
        detected_lang = language.lower()
    elif filename is not None:
        detected_lang = (detect_language_from_extension(filename)
                         or detect_language_from_code(code))
    else:
        detected_lang = detect_language_from_code(code)

    lang_config = get_config(detected_lang)

    # Izvlačenje značajki po metodama
    style_feats       = extract_style_features(code, lang_config)
    structural_feats  = extract_structural_features(code, lang_config)
    statistical_feats = extract_statistical_features(code, model, tokenizer)

    return {
        "detected_language": detected_lang,
        **style_feats,
        **structural_feats,
        **statistical_feats,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BRZI TEST — pokreni: python feature_extraction.py
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    test_cases = {
        "Python (AI)": ("python", '''
def calculate_average(numbers: list) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of an empty list.")
    total_sum = sum(numbers)
    count = len(numbers)
    return total_sum / count
'''),
        "Python (Human)": ("python", '''
def avg(nums):
    # quick avg
    return sum(nums) / len(nums)
'''),
        "JavaScript (AI)": ("javascript", '''
/**
 * Calculates the average of an array of numbers.
 */
function calculateAverage(numbers) {
    if (!numbers || numbers.length === 0) {
        throw new Error("Cannot calculate average of an empty array.");
    }
    const totalSum = numbers.reduce((acc, val) => acc + val, 0);
    return totalSum / numbers.length;
}
'''),
        "Java (AI)": ("java", '''
/**
 * Calculates the average of an integer array.
 */
public class Calculator {
    public static double calculateAverage(int[] numbers) {
        if (numbers == null || numbers.length == 0) {
            throw new IllegalArgumentException("Array must not be empty.");
        }
        int totalSum = 0;
        for (int currentNumber : numbers) {
            totalSum += currentNumber;
        }
        return (double) totalSum / numbers.length;
    }
}
'''),
    }

    KEY_FEATURES = [
        ("Prepoznat jezik",            "detected_language"),
        ("Omjer komentara",            "comment_ratio"),
        ("Broj docstringova",          "num_docstrings"),
        ("Prosj. duljina identif.",    "avg_identifier_length"),
        ("Prosj. duljina fun. naziva", "avg_function_name_length"),
        ("Jednoslovna imena",          "single_char_name_ratio"),
        ("Konzistentnost imenovanja",  "naming_consistency"),
        ("Broj funkcija",              "num_functions"),
        ("Prosj. duljina funkcije",    "avg_function_length"),
        ("Max ugniježđenost",          "max_nesting_depth"),
        ("Aproks. složenost (CC)",     "cyclomatic_complexity_approx"),
        ("Perplexity",                 "perplexity"),
    ]

    for label, (lang, code) in test_cases.items():
        print(f"\n{'═' * 55}")
        print(f"  {label}")
        print(f"{'═' * 55}")
        features = extract_all_features(code, language=lang)
        for display_name, key in KEY_FEATURES:
            val = features.get(key, "N/A")
            if isinstance(val, float):
                print(f"  {display_name:<32} {val:.4f}")
            else:
                print(f"  {display_name:<32} {val}")

    print(f"\n  Ukupno značajki: {len(features)}")


# ─────────────────────────────────────────────────────────────────────────────
# ANALIZA PO LINIJAMA — za prikaz sumnjivih linija u UI-u
# ─────────────────────────────────────────────────────────────────────────────

def analyze_lines(code: str, language: str = None, filename: str = None) -> list:
    """
    Analizira kod liniju po liniju i vraća listu sumnjivih linija.

    Svaki element liste je rječnik:
        {
            "line":  int,   # broj linije (1-based)
            "tone":  str,   # "red" = jak signal, "amber" = umjeren
            "note":  str,   # kratko objašnjenje (prikazuje se u UI-u)
        }

    Detektira sljedeće AI signale po liniji:
      - Docstringovi i formalni blok komentari (jak signal)
      - Jednolinijski komentari (umjeren signal)
      - Linije s dugačkim identifikatorima (umjeren signal)
      - Type anotacije (umjeren signal)
      - Try/except/raise/throw s formalnim porukama (umjeren signal)
      - Linije s višestrukim opisnim identifikatorima (jak signal)

    Parametri:
        code (str):          Izvorni kod kao string.
        language (str|None): Naziv jezika — ako None, automatski se detektira.
        filename (str|None): Ime datoteke — pomaže detekciji jezika.

    Vraća:
        list: Lista rječnika s anotacijama, sortirana po broju linije.
    """
    import re

    if language is None:
        if filename is not None:
            language = detect_language_from_extension(filename) or detect_language_from_code(code)
        else:
            language = detect_language_from_code(code)

    try:
        lang_config = get_config(language)
    except ValueError:
        lang_config = get_config("python")

    lines = code.splitlines()
    annotations = []
    in_docstring = False
    docstring_char = None

    inline_pat = lang_config.get("inline_comment", r"^\s*#")

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # ── DOCSTRINGOVI / BLOK KOMENTARI ─────────────────────────────────
        # Python docstringovi (""" ili ''')
        if language == "python":
            triple_count = stripped.count('"""') + stripped.count("'''")
            if not in_docstring and ('"""' in stripped or "'''" in stripped):
                docstring_char = '"""' if '"""' in stripped else "'''"
                # Ako se otvara i zatvara na istoj liniji → jednolinijski docstring
                if stripped.count(docstring_char) >= 2 and len(stripped) > 6:
                    annotations.append({
                        "line": i, "tone": "red",
                        "note": "Formal docstring — strong AI indicator"
                    })
                else:
                    in_docstring = True
                    annotations.append({
                        "line": i, "tone": "red",
                        "note": "Docstring block — strong AI indicator"
                    })
                continue
            elif in_docstring:
                annotations.append({
                    "line": i, "tone": "red",
                    "note": "Docstring content"
                })
                if docstring_char and docstring_char in stripped:
                    in_docstring = False
                continue

        # Javadoc / JSDoc blokovi (/** ... */)
        if language in ("java", "javascript", "typescript", "cpp", "c"):
            if stripped.startswith("/**") or stripped.startswith("* ") or stripped == "*/":
                annotations.append({
                    "line": i, "tone": "red",
                    "note": "Formal documentation comment — strong AI indicator"
                })
                continue

        # ── JEDNOLINIJSKI KOMENTARI ────────────────────────────────────────
        if re.match(inline_pat, line):
            # Gledamo duljinu komentara — kratki (#) ne flagiramo
            comment_text = re.sub(inline_pat, "", line).strip()
            word_count = len(comment_text.split())
            if word_count >= 4:
                annotations.append({
                    "line": i, "tone": "amber",
                    "note": f"Inline comment ({word_count} words) — elevated comment density"
                })
            continue

        # ── DUGAČKI IDENTIFIKATORI ─────────────────────────────────────────
        # VAŽNO: Prije analize, uklonimo sadržaj string literala s linije.
        # Bez ovoga, regex bi uhvatio i prirodne riječi unutar stringova
        # (npr. "Ucitajte red matrice") kao identifikatore — što je pogrešno.
        code_only = re.sub(r'"[^"]*"', '""', stripped)   # ukloni "..."
        code_only = re.sub(r"'[^']*'", "''", code_only)  # ukloni '...'
        code_only = re.sub(r"`[^`]*`", "``", code_only)       # ukloni `...`

        identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]{4,})\b', code_only)

        # Preskačemo rezervirane riječi i uobičajene kratke stdlib nazive
        reserved = {
            "return", "import", "function", "class", "interface", "public",
            "private", "static", "const", "false", "true", "none", "self",
            "print", "printf", "scanf", "range", "raise", "while", "break",
            "continue", "yield", "lambda", "assert", "except", "finally",
            "include", "define", "string", "vector", "struct", "unsigned",
            "length", "value", "write", "reads", "fopen", "fclose", "malloc",
            "sizeof", "stdio", "stdlib", "nullptr", "virtual", "override",
            "inline", "extern", "register", "volatile", "switch", "default",
        }
        real_ids = [x for x in identifiers if x.lower() not in reserved]

        if len(real_ids) >= 2:
            avg_len = sum(len(x) for x in real_ids) / len(real_ids)
            if avg_len >= 9:
                annotations.append({
                    "line": i, "tone": "red",
                    "note": f"Very long identifiers (avg {avg_len:.0f} chars) — AI naming pattern"
                })
                continue
            elif avg_len >= 7:
                annotations.append({
                    "line": i, "tone": "amber",
                    "note": f"Descriptive identifier names (avg {avg_len:.0f} chars)"
                })
                continue

        # ── TYPE ANOTACIJE (Python) ────────────────────────────────────────
        if language == "python":
            if re.search(r'\)\s*->\s*\w', stripped) or re.search(r':\s*(int|float|str|bool|list|dict|tuple|set|Optional|Union|List|Dict)\b', stripped):
                annotations.append({
                    "line": i, "tone": "amber",
                    "note": "Type annotation — uncommon in student code"
                })
                continue

        # ── TRY/EXCEPT/RAISE S PORUKAMA ────────────────────────────────────
        if re.match(r'^\s*(raise|throw)\s+\w*Error\s*\(', line) or \
           re.match(r'^\s*(raise|throw)\s+\w*Exception\s*\(', line):
            annotations.append({
                "line": i, "tone": "amber",
                "note": "Explicit exception with message — AI error handling pattern"
            })
            continue

        if re.match(r'^\s*(except|catch)\s*[\(\w]', line):
            annotations.append({
                "line": i, "tone": "amber",
                "note": "Exception handling — AI code often handles all edge cases"
            })
            continue

    # Makni previše sumnjivih linija — ako je >60% flagirano, to gubi smisao
    # Prikaži samo najsumnjivije linije (max 40% koda)
    total_nonblank = sum(1 for l in lines if l.strip())
    max_annotations = max(3, int(total_nonblank * 0.40))

    # Sortiraj: red prije amber, onda po broju linije
    priority = {"red": 0, "amber": 1}
    annotations.sort(key=lambda a: (priority.get(a["tone"], 2), a["line"]))
    annotations = annotations[:max_annotations]
    annotations.sort(key=lambda a: a["line"])

    return annotations
