# Code Review: grep.py

## 1. Executive Summary

`grep.py` correctly implements the core specification required by `README.md` and passes `public_test.py`. The fundamental logic for flag combinations (`-n`, `-l`, `-i`, `-v`, `-x`), multiple file prefixes, and output formatting matches the Unix grep behavior described in the specification.

However, the audit identified:
1. **Defect / Edge Case:** Fragile line ending stripping (`raw_line.rstrip("\n")`) which breaks with Windows CRLF (`\r\n`) line endings (especially under mocks like `io.StringIO`).
2. **Performance Trap:** Redundant `pattern.lower()` allocation and calculation inside the inner loop for every line.
3. **Robustness Improvement:** `_parse_flags` assumes `flags` is always a string and crashes if an iterable/list of flags is passed.

---

## 2. Verification Run

Executed `python3 -m unittest public_test.py`:
```
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

---

## 3. Detailed Audit Findings

### Issue 1: CRLF Line Endings (`\r\n`) Break Exact Match (`-x`) and Corrupt Output
- **Location:** `grep.py`, line 24:
  ```python
  line = raw_line.rstrip("\n")
  ```
- **Analysis:**
  While standard filesystem `open()` on Python 3 uses universal newline mode by default, tests often mock `open` using `io.StringIO` (as seen in `public_test.py`). `io.StringIO` does **not** translate newlines by default when iterating lines. If a text string contains `\r\n`, `raw_line.rstrip("\n")` leaves a trailing `\r` on `line`.
- **Consequences:**
  - When `-x` (exact line match) is used, `"pattern"` will be compared against `"pattern\r"`, which fails (`"pattern" == "pattern\r"` is `False`).
  - The trailing `\r` leaks into the final output line before the terminating `\n`, producing corrupted records.
- **Required Fix:**
  Change line stripping to remove both `\r` and `\n`:
  ```python
  line = raw_line.rstrip("\r\n")
  ```
  `rstrip("\r\n")` preserves any trailing spaces or tabs on the line (which `str.rstrip()` would mistakenly remove) while properly cleaning CRLF, LF, and CR terminators.

---

### Issue 2: Performance Trap — Redundant `pattern.lower()` in Inner Loop
- **Location:** `grep.py`, lines 5–11:
  ```python
  def _matches(line, pattern, insensitive, exact):
      if insensitive:
          line = line.lower()
          pattern = pattern.lower()

      if exact:
          return line == pattern
      return pattern in line
  ```
- **Analysis:**
  `pattern.lower()` is evaluated inside `_matches()` on every line of every file. For large files or multiple files, this allocates and transforms the pattern string repeatedly $N$ times instead of once.
- **Required Fix:**
  Precompute `pattern.lower()` once in `grep()` prior to the file loop:
  ```python
  if insensitive:
      pattern = pattern.lower()
  ```
  In `_matches()`, only convert `line.lower()`:
  ```python
  def _matches(line, pattern, insensitive, exact):
      if insensitive:
          line = line.lower()
      if exact:
          return line == pattern
      return pattern in line
  ```

---

### Issue 3: Flag Parsing Type Flexibility
- **Location:** `grep.py`, lines 1–2:
  ```python
  def _parse_flags(flags):
      return set(flags.split())
  ```
- **Analysis:**
  If a test or caller passes `flags` as a list/tuple (e.g. `["-n", "-l"]` or `[]`), calling `.split()` raises `AttributeError: 'list' object has no attribute 'split'`.
- **Required Fix:**
  Support both strings and iterables:
  ```python
  def _parse_flags(flags):
      if isinstance(flags, str):
          return set(flags.split())
      return set(flags)
  ```

---

## 4. Edge Cases & Invariant Verification Matrix

| Category | Scenario | Current Behavior | Status |
| :--- | :--- | :--- | :--- |
| **Line Numbering** | Physical 1-based indexing with `-n` | `enumerate(file, start=1)` preserves physical line numbers even when `-v` filters lines | **PASS** |
| **Files-only Mode** | `-l` flag | Outputs `{filename}\n`, exits file immediately (`break`), suppresses `-n` and content | **PASS** |
| **Multiple Files** | Multiple files searched | Prepends `{filename}:` to content lines; omitted when single file | **PASS** |
| **Multiple Files + `-l`**| Multiple files with `-l` | Outputs only `{filename}\n` without `{filename}:` prefix | **PASS** |
| **Inversion** | `-v` flag | Inverts matching result after `-x` or `-i` evaluation | **PASS** |
| **Inversion + `-l`** | `-v -l` flags | Emits filename if at least one line fails to match | **PASS** |
| **Full Line Match** | `-x` flag | Compares `line == pattern`; substring matches are excluded | **PASS** |
| **Fixed String** | Regex characters (`.`, `*`, `[`, `]`) | Treated as literal substrings via `in` and `==` | **PASS** |
| **Empty Pattern** | `pattern = ""` | Matches all lines without `-x`; matches empty lines with `-x` | **PASS** |
| **Preserve Spaces** | Lines with trailing spaces | `rstrip("\n")` preserves trailing whitespace (needs `\r\n` fix) | **PASS** with fix |
| **No Matches** | Search term absent | Returns `""` (empty string) | **PASS** |

---

## 5. Summary of Required Modifications

In `grep.py`:
1. Update `_parse_flags` to handle `isinstance(flags, str)`.
2. Move `pattern.lower()` outside the line loop in `grep()`.
3. Simplify `_matches` so it only lowercases `line` when `insensitive` is True.
4. Replace `raw_line.rstrip("\n")` with `raw_line.rstrip("\r\n")`.
