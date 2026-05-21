import re
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_java
import tree_sitter_cpp
import tree_sitter_c
import tree_sitter_go
import tree_sitter_rust
import tree_sitter_ruby
import tree_sitter_typescript


LANGUAGE_CONFIGS: dict = {

    # ── Python ────────────────────────────────────────────────────────────
    "python": {
        "ts_module": tree_sitter_python,
        "extensions": [".py"],
        "inline_comment": r"^\s*#",
        "block_comment": None,
        "docstring_pattern": r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'',
        "node_types": {
            "function":   ["function_definition"],
            "class":      ["class_definition"],
            "if":         ["if_statement"],
            "for":        ["for_statement"],
            "while":      ["while_statement"],
            "try":        ["try_statement"],
            "import":     ["import_statement", "import_from_statement"],
            "identifier": ["identifier"],
            "lambda":     ["lambda"],
        },
    },

    # ── JavaScript ────────────────────────────────────────────────────────
    "javascript": {
        "ts_module": tree_sitter_javascript,
        "extensions": [".js", ".mjs", ".cjs"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": r"/\*\*[\s\S]*?\*/",
        "node_types": {
            "function":   ["function_declaration", "arrow_function",
                           "function_expression", "method_definition"],
            "class":      ["class_declaration", "class"],
            "if":         ["if_statement"],
            "for":        ["for_statement", "for_in_statement"],
            "while":      ["while_statement"],
            "try":        ["try_statement"],
            "import":     ["import_statement"],
            "identifier": ["identifier"],
            "lambda":     ["arrow_function"],
        },
    },

    # ── TypeScript ────────────────────────────────────────────────────────
    "typescript": {
        "ts_module": tree_sitter_typescript,
        "extensions": [".ts"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": r"/\*\*[\s\S]*?\*/",
        "node_types": {
            "function":   ["function_declaration", "arrow_function",
                           "function_expression", "method_definition"],
            "class":      ["class_declaration"],
            "if":         ["if_statement"],
            "for":        ["for_statement", "for_in_statement"],
            "while":      ["while_statement"],
            "try":        ["try_statement"],
            "import":     ["import_statement"],
            "identifier": ["identifier"],
            "lambda":     ["arrow_function"],
        },
    },

    # ── Java ──────────────────────────────────────────────────────────────
    "java": {
        "ts_module": tree_sitter_java,
        "extensions": [".java"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": r"/\*\*[\s\S]*?\*/",
        "node_types": {
            "function":   ["method_declaration", "constructor_declaration"],
            "class":      ["class_declaration", "interface_declaration",
                           "enum_declaration"],
            "if":         ["if_statement"],
            "for":        ["for_statement", "enhanced_for_statement"],
            "while":      ["while_statement"],
            "try":        ["try_statement"],
            "import":     ["import_declaration"],
            "identifier": ["identifier"],
            "lambda":     ["lambda_expression"],
        },
    },

    # ── C ─────────────────────────────────────────────────────────────────
    "c": {
        "ts_module": tree_sitter_c,
        "extensions": [".c", ".h"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": r"/\*\*[\s\S]*?\*/",
        "node_types": {
            "function":   ["function_definition"],
            "class":      ["struct_specifier", "union_specifier"],
            "if":         ["if_statement"],
            "for":        ["for_statement"],
            "while":      ["while_statement"],
            "try":        [],
            "import":     ["preproc_include"],
            "identifier": ["identifier"],
            "lambda":     [],
        },
    },

    # ── C++ ───────────────────────────────────────────────────────────────
    "cpp": {
        "ts_module": tree_sitter_cpp,
        "extensions": [".cpp", ".cc", ".cxx", ".hpp"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": r"/\*\*[\s\S]*?\*/",
        "node_types": {
            "function":   ["function_definition"],
            "class":      ["class_specifier", "struct_specifier"],
            "if":         ["if_statement"],
            "for":        ["for_statement", "for_range_loop"],
            "while":      ["while_statement"],
            "try":        ["try_statement"],
            "import":     ["preproc_include"],
            "identifier": ["identifier"],
            "lambda":     ["lambda_expression"],
        },
    },

    # ── Go ────────────────────────────────────────────────────────────────
    "go": {
        "ts_module": tree_sitter_go,
        "extensions": [".go"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": None,
        "node_types": {
            "function":   ["function_declaration", "method_declaration"],
            "class":      ["type_declaration"],
            "if":         ["if_statement"],
            "for":        ["for_statement"],
            "while":      ["for_statement"],
            "try":        [],
            "import":     ["import_declaration"],
            "identifier": ["identifier"],
            "lambda":     ["func_literal"],
        },
    },

    # ── Rust ──────────────────────────────────────────────────────────────
    "rust": {
        "ts_module": tree_sitter_rust,
        "extensions": [".rs"],
        "inline_comment": r"^\s*//",
        "block_comment": ("/*", "*/"),
        "docstring_pattern": r"///.*",
        "node_types": {
            "function":   ["function_item"],
            "class":      ["struct_item", "impl_item", "trait_item"],
            "if":         ["if_expression"],
            "for":        ["for_expression"],
            "while":      ["while_expression"],
            "try":        ["match_expression"],
            "import":     ["use_declaration"],
            "identifier": ["identifier"],
            "lambda":     ["closure_expression"],
        },
    },

    # ── Ruby ──────────────────────────────────────────────────────────────
    "ruby": {
        "ts_module": tree_sitter_ruby,
        "extensions": [".rb"],
        "inline_comment": r"^\s*#",
        "block_comment": ("=begin", "=end"),
        "docstring_pattern": None,
        "node_types": {
            "function":   ["method", "singleton_method"],
            "class":      ["class", "module"],
            "if":         ["if", "unless"],
            "for":        ["for"],
            "while":      ["while", "until"],
            "try":        ["begin"],
            "import":     [],
            "identifier": ["identifier"],
            "lambda":     ["lambda"],
        },
    },

}


def get_config(language: str) -> dict:
    key = language.lower().strip()
    if key not in LANGUAGE_CONFIGS:
        supported = ", ".join(sorted(LANGUAGE_CONFIGS.keys()))
        raise ValueError(
            f"Jezik '{language}' nije podržan.\n"
            f"Podržani jezici: {supported}"
        )
    return LANGUAGE_CONFIGS[key]


def detect_language_from_extension(filename: str):

    filename = filename.lower()
    for lang, config in LANGUAGE_CONFIGS.items():
        for ext in config["extensions"]:
            if filename.endswith(ext):
                return lang
    return None


def detect_language_from_code(code: str) -> str:
   
    scores = {lang: 0 for lang in LANGUAGE_CONFIGS}

    # Python
    if re.search(r"\bdef\s+\w+\s*\(", code):       scores["python"] += 3
    if re.search(r'"""', code):                     scores["python"] += 2
    if re.search(r"\bself\b", code):                scores["python"] += 2
    if re.search(r"\bprint\s*\(", code):            scores["python"] += 1
    if re.search(r":\s*$", code, re.MULTILINE):     scores["python"] += 1

    # Java
    if re.search(r"\bpublic\s+class\b", code):      scores["java"] += 4
    if re.search(r"\bSystem\.out\b", code):         scores["java"] += 3
    if re.search(r"\bpublic\s+static\b", code):     scores["java"] += 2
    if re.search(r"\bvoid\s+main\b", code):         scores["java"] += 2

    # JavaScript
    if re.search(r"\bconst\s+\w+\s*=", code):      scores["javascript"] += 2
    if re.search(r"=>\s*[{(]", code):               scores["javascript"] += 3
    if re.search(r"\bconsole\.log\b", code):        scores["javascript"] += 3

    # TypeScript
    if re.search(r":\s*(string|number|boolean|void)\b", code):
        scores["typescript"] += 4
    if re.search(r"\binterface\s+\w+", code):       scores["typescript"] += 4

    # C / C++
    if re.search(r"#include\s*[<\"]", code):
        scores["cpp"] += 3
        scores["c"] += 3
    if re.search(r"\bstd::", code):                 scores["cpp"] += 4
    if re.search(r"\bcout\b", code):                scores["cpp"] += 4
    if re.search(r"\bcin\b", code):                 scores["cpp"] += 4
    if re.search(r"\busing\s+namespace\b", code):   scores["cpp"] += 4
    if re.search(r"\btemplate\s*<", code):          scores["cpp"] += 3
    if re.search(r"\bvector\s*<", code):            scores["cpp"] += 3
    if re.search(r"\bstring\b", code) and re.search(r"#include", code):
        scores["cpp"] += 2
    if re.search(r"\bprintf\s*\(", code):           scores["c"] += 3
    if re.search(r"\bscanf\s*\(", code):            scores["c"] += 3
    if re.search(r"\bmalloc\s*\(", code):           scores["c"] += 3

    # Go
    if re.search(r"\bfunc\s+\w+\s*\(", code):      scores["go"] += 4
    if re.search(r"\bpackage\s+\w+", code):         scores["go"] += 4
    if re.search(r"\bfmt\.Print", code):            scores["go"] += 3

    # Rust
    if re.search(r"\bfn\s+\w+\s*\(", code):        scores["rust"] += 4
    if re.search(r"\blet\s+mut\b", code):           scores["rust"] += 4
    if re.search(r"\bprintln!\s*\(", code):         scores["rust"] += 3

    # Ruby
    if re.search(r"\bdef\s+\w+", code) and re.search(r"\bend\b", code):
        scores["ruby"] += 3
    if re.search(r"\bputs\s+", code):              scores["ruby"] += 3

    best = max(scores, key=lambda l: scores[l])
    return best if scores[best] > 0 else "python"
