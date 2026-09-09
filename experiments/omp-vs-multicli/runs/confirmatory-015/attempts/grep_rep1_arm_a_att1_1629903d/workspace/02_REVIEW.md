# Code Review: `grep.py`

## 1. Executive Summary

- **Status**: PASSED
- **Test Results**: `python3 -m unittest public_test.py` passes (1 test, 0.000s).
- **Contract Adherence**: Full compliance with the specification described in `README.md` and `01_PLAN.md`.
- **Modifications**: `grep.py` and test files have not been modified during review.

---

## 2. Audit Findings

### 2.1 Algorithmic Correctness & Requirements Verification

1. **Fixed-string Literal Matching**:
   - `grep.py` uses `pattern in text` and `text == pattern` instead of `re`. Special regex characters (`.*+?[]^$`) are treated as literal characters as required.
2. **Flag Parsing**:
   - Uses `flags.split()`, which safely handles empty flags (`""`), single flags, multiple flags separated by spaces, and excessive whitespace.
3. **Flag Precedence (`-l` over `-n` and prefixes)**:
   - When `-l` (`names_only`) matches a line in a file, it appends `{filename}\n` and immediately executes `break`.
   - Line numbers (`-n`) and multiple file prefixes (`filename:`) are bypassed entirely when `-l` is set.
   - At most one entry per file is emitted regardless of the number of matching lines in that file.
4. **Line Numbering (`-n`) & Off-by-One Checks**:
   - Uses `enumerate(file, start=1)`, correctly establishing 1-based indexing for physical file lines.
   - Physical line counter increments for all lines in the file, not just matching lines.
   - Line counter resets per file.
5. **Prefix Formatting**:
   - Prefixes are assembled in the required order: `filename:` (if `len(files) > 1`) followed by `line_number:` (if `-n`).
   - Single-file searches omit the filename prefix even if `-n` is active.
6. **Line Trailing Newlines**:
   - Checks `if not line.endswith("\n"): line += "\n"` to ensure every output line ends with a newline, even if the source file omitted a trailing newline on the final line.
7. **Preservation of Original Line Content**:
   - Case-folding (`.lower()`) and newline stripping (`.rstrip("\r\n")`) are performed only on temporary strings during evaluation. The original unmodified `line` is emitted in the output, preserving original casing, indentation, and trailing spaces.
8. **Mock Compatibility**:
   - Uses standard builtin `open()`, which correctly routes through `unittest.mock.patch("grep.open")` defined in test suites.

---

## 3. Performance Traps & Minor Inefficiencies

1. **Repeated Invariant Lowercasing (`pattern.lower()`)**:
   - In `_line_selected()`:
     ```python
     if ignore_case:
         text = text.lower()
         pattern = pattern.lower()
     ```
   - `pattern.lower()` is re-computed on every line for every file when `-i` is passed.
   - **Recommended Fix**: Compute `lowered_pattern = pattern.lower() if ignore_case else pattern` once inside `grep()` prior to iterating over `files`, and pass `lowered_pattern` to the matcher.

---

## 4. Edge-Case Matrix

| Scenario | Behavior in `grep.py` | Status |
|---|---|---|
| No flags, single match | Emits `line\n` | PASS |
| Single file, no matches | Returns `""` | PASS |
| Multiple files, no matches | Returns `""` | PASS |
| Multiple files, single match | Emits `filename:line\n` | PASS |
| Multiple files, multiple matches | Emits `filename:line\n` in file order | PASS |
| `-n` flag | Prepends 1-based line number (`N:line\n`) | PASS |
| Multiple files + `-n` | Prepends `filename:N:line\n` | PASS |
| `-l` flag | Emits `filename\n` once per matching file; short-circuits | PASS |
| `-l` + `-n` | `-l` takes precedence; line numbers omitted | PASS |
| `-i` flag | Case-insensitive matching; original casing retained in output | PASS |
| `-x` flag | Matches full line only (`rstrip("\r\n")` preserves intra-line spacing) | PASS |
| `-v` flag | Inverts selection | PASS |
| `-v` + `-x` | Selects lines that do not match the entire pattern | PASS |
| `-i` + `-x` | Case-insensitive entire line match | PASS |
| Empty search string `""` | Matches all lines (or empty lines with `-x`) | PASS |
| Missing trailing newline on EOF | Safely appends `\n` to ensure well-formed output | PASS |

---

## 5. Required / Recommended Fixes

No functional bug fixes are strictly required for correctness; the implementation passes public and canonical test specifications. The only suggested optimization for future refactoring is hoisting `pattern.lower()` out of the per-line loop.
