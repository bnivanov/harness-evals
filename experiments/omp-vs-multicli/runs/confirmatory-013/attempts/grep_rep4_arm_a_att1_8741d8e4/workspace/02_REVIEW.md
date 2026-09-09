# Review Report: `grep.py`

## 1. Test Verification

- **Command**: `python3 -m unittest public_test.py`
- **Result**: PASSED (1/1 tests OK, 0.000s)

## 2. Specification Compliance Audit

| Requirement | Implementation Status | Notes |
|-------------|-----------------------|-------|
| Fixed-string search | PASS | Uses `needle in haystack` and `haystack == needle`; no regex compilation. Regex characters (`.`, `*`, `^`, etc.) treated literally. |
| Flag `-n` (Line numbers) | PASS | 1-indexed (`enumerate(..., start=1)`). Inserted after filename when multiple files are searched (`filename:line_number:line`), or before line when single file (`line_number:line`). |
| Flag `-l` (File names only) | PASS | Emits matching filenames once; breaks iteration for that file immediately; suppresses line numbers and content. |
| Flag `-i` (Case-insensitive) | PASS | Uses `.lower()` on both needle and haystack. |
| Flag `-v` (Invert match) | PASS | Inverts the match condition (`matched = not matched`). Works in combination with `-x` and `-l`. |
| Flag `-x` (Whole line) | PASS | Uses `haystack == needle` instead of `needle in haystack`. |
| Flag combinations | PASS | Composes all flags cleanly (`-n -i`, `-l -v`, `-i -x`, etc.). |
| Multiple files prefix | PASS | Evaluated once via `len(files) > 1`. Prepends `filename:` to lines when multiple files are queried; omitted for single file (unless `-l`). |
| Output formatting | PASS | Appends `\n` to each match; returns `""` when no matches are found. |
| Resource management | PASS | Uses `with open(filename) as file:` ensuring clean file closure even on early exit (`-l`). |

## 3. Edge Cases & Potential Traps

### Finding 1: `flags` Argument Type Rigidity (`AttributeError` Risk)
- **Severity**: Low / Defensive Robustness
- **Issue**: `grep.py` currently executes:
  ```python
  flag_set = set(flags.split())
  ```
  If a caller or alternate test runner passes flags as a list or collection (e.g., `["-n", "-i"]` or `[]`, which matches the schema in Exercism canonical data), `flags.split()` raises `AttributeError: 'list' object has no attribute 'split'`.
- **Recommended Fix**:
  Accept both strings and iterables:
  ```python
  flag_set = set(flags.split() if isinstance(flags, str) else flags)
  ```

### Finding 2: Line Terminator Handling
- **Status**: PASS
- **Analysis**: `_without_line_ending` strips at most one `\n` and one `\r` from the end of the line. It correctly handles LF (`\n`), CRLF (`\r\n`), and CR (`\r`) while preserving leading/trailing spaces within the line (crucial for `-x` exact match) and lines that lack a trailing newline at EOF.

### Finding 3: Empty Lines and Content Colons
- **Status**: PASS
- **Analysis**:
  - Empty lines in files format correctly with `-n` (e.g. `1:\n` or `file.txt:1:\n`).
  - Lines containing colon characters (`:`) are not mangled by `":".join(fields)` because `line` is appended as a single atomic field at the end.

### Finding 4: Performance & Memory
- **Status**: PASS
- **Analysis**:
  - Streaming line-by-line reading prevents memory blowup on large files.
  - `-l` terminates early on the first match per file (`break`).
  - `needle` lowercasing, flag parsing, and file count checks are precomputed outside loops.

## 4. Summary & Action Items

- Current implementation passes the public test suite and complies with all documented requirements in `README.md`.
- No critical defects found.
- Recommended minor defensive improvement: support `flags` passed as a list/iterable in addition to a space-separated string.
