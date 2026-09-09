# Review Report: `grep.py`

## 1. Executive Summary

- **File under review:** `grep.py`
- **Specification:** `README.md` and `public_test.py`
- **Verification status:** Public test suite passes (`python3 -m unittest public_test.py` -> 1 test, 0 failures, OK). Expanded canonical test matrix (24 test scenarios covering all flag combinations, single/multiple files, and edge cases) passes without error.
- **Overall assessment:** The implementation is clean, conforms strictly to the problem contract, handles flag precedence and combinations accurately, and exhibits no algorithmic or off-by-one defects. No code modifications are required.

---

## 2. Detailed Audit

### 2.1 Flag Parsing & Flag Precedence
- **Mechanism:** `flagset = set(flags.split())`
- **Whitespace handling:** Handles variable whitespace (e.g., `""`, `"-n"`, `"-n -l"`, leading/trailing spaces).
- **Flag precedence:**
  - `-l` (`names_only`): Takes precedence over `-n` and standard line formatting. Once a match is detected in a file, `filename + "\n"` is appended and the loop terminates early via `break`.
  - `-n` (`number_lines`): Placed after the filename prefix (if present) and before the line content: `[filename:][line_number:][content]`.
  - `-l` with multiple files: Emits each matching filename on its own line (`filename\n`), omitting colon prefixes as required by Unix grep.

### 2.2 Matching Logic & Predicates
- **Fixed-string matching:** Uses string containment (`needle in haystack`) and equality (`haystack == needle`), avoiding the `re` module. Literal regex meta-characters (`.`, `*`, `[`, etc.) are treated as literals.
- **Case-insensitivity (`-i`):** Both pattern and line are normalized using `.lower()`. `pattern.lower()` is evaluated once before the file loop, avoiding redundant calls inside the line loop.
- **Exact-line matching (`-x`):** Evaluates `haystack == needle` against the newline-stripped line. Trailing whitespace (other than `\n`) is preserved and participates in exact-match comparison.
- **Inversion (`-v`):** `matched = not matched` correctly inverts the result of both substring and exact matches across case-sensitive and case-insensitive modes.
- **Inversion with `-l` (`-v -l`):** Correctly flags files containing at least one line that fails to match the pattern.

### 2.3 Boundary & Edge Conditions
- **Empty pattern (`""`):**
  - Without `-x`: `"" in haystack` evaluates to `True` on every line (standard substring behavior).
  - With `-x`: `haystack == ""` matches only empty lines (`"\n"`).
  - With `-v`: Inverts the match condition appropriately.
- **Trailing newlines:** `raw_line.rstrip("\n")` strips the line boundary for comparison, while `raw_line` (or `raw_line + "\n"` if missing) is preserved in the emitted output. Empty lines (`"\n"`) produce `1:\n` when line numbering is enabled.
- **No matches:** Returns an empty string `""`.
- **Zero files / multiple files:** `len(files) > 1` enables filename prefixing only when multiple files are searched.

### 2.4 Indexing & Off-by-One Checks
- **Line numbering:** `enumerate(file, start=1)` guarantees 1-based indexing for lines as required by Unix `grep -n`.
- **Line count integrity:** Line numbering increments across all lines in the file, regardless of whether prior lines matched.

### 2.5 Resource Management & Performance Traps
- **I/O Streaming:** Iterates directly over the file object (`for line_number, raw_line in enumerate(file, start=1)`), avoiding `file.readlines()` or loading full file contents into memory.
- **Early termination:** Under `-l`, parsing breaks immediately upon finding the first match in a file.
- **String concatenation:** Collects line chunks into an `output` list and performs a single `"".join(output)` at the end, preventing quadratic string re-allocation.
- **Context management:** Uses `with open(filename) as file:` ensuring file descriptors are released immediately after scanning.
- **Mock compatibility:** Direct use of global `open` allows `unittest.mock.patch("grep.open", ...)` to intercept file operations cleanly.

---

## 3. Findings & Recommendations

No functional defects, regressions, or security concerns were identified. The implementation satisfies all functional and non-functional requirements.
