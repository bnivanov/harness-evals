# Code Review: `grep.py`

## Executive Summary
`grep.py` implements the Exercism `grep` specification cleanly and passes the test suite (`public_test.py`). The core logic for flag parsing, line matching, inversion, and output formatting conforms to the functional requirements specified in `README.md`.

This review identifies opportunities for performance optimization, newline robustness, and edge-case resilience.

---

## Verification
- Test command executed: `python3 -m unittest public_test.py`
- Result: **PASS** (1 test ran in 0.000s)

---

## Detailed Audit

### 1. Performance Traps
- **Redundant Case Folding in Loop (`_matches`):**
  - **Issue:** In `_matches(text, pattern, ignore_case, whole_line)`, when `ignore_case` is `True`, `pattern.lower()` is evaluated for every line of every file processed. For large files or multi-file searches with thousands of lines, this causes millions of redundant string allocations and case-folding operations.
  - **Remedy:** Pre-compute `pattern = pattern.lower()` once in `grep()` before iterating over `files`, and only lower-case `text` in the line loop.

### 2. Line-Ending Robustness (CRLF / Windows Newlines)
- **Stripping Trailing Newlines:**
  - **Issue:** The line stripping currently uses:
    ```python
    text = raw_line[:-1] if raw_line.endswith("\n") else raw_line
    ```
    If input lines have CRLF endings (`\r\n`) (e.g. mock streams or files opened without newline translation), stripping only the trailing `\n` leaves a residual `\r` at the end of `text`. This causes `-x` (whole-line match) to fail when comparing `"pattern"` against `"pattern\r"`.
  - **Remedy:** Strip `\r\n` before `\n`, or use:
    ```python
    if raw_line.endswith("\r\n"):
        text = raw_line[:-2]
    elif raw_line.endswith("\n"):
        text = raw_line[:-1]
    else:
        text = raw_line
    ```
    *(Note: Avoid `.rstrip("\r\n")` because that would also strip intentional trailing spaces or multiple trailing newlines).*

### 3. Algorithmic Correctness & Flag Precedence
- **Flag Parsing (`_parse_flags`):**
  - Uses `set(flags.split())`, correctly handling any whitespace variation, empty flag strings, duplicate flags, and flag ordering.
- **Precedence of `-l`:**
  - When `-l` is set, matching immediately appends `filename + "\n"` and breaks out of reading the file. This correctly suppresses line contents and line numbers (`-n`), and prevents duplicate file listings.
- **Inversion Logic (`-v`):**
  - The check `if matched == invert: continue` is concise, correct, and behaves as expected across all flag combinations (`-v -x`, `-v -i`, `-v -l`, etc.).
- **Prefix Ordering:**
  - Single file: `{line}` or `{line_number}:{line}`.
  - Multiple files: `{filename}:{line}` or `{filename}:{line_number}:{line}`.
  - Matches the requirement: *"placing the number after the filename (if present)"*.
- **Line Numbering:**
  - 1-based indexing using `enumerate(..., start=1)` counts physical lines, including non-matching lines when `-v` is active.

### 4. Edge Cases Audited
| Edge Case | Status | Notes |
|-----------|--------|-------|
| Empty pattern (`""`) | Pass | Matches all lines without `-x`; matches empty lines with `-x`. |
| Empty file | Pass | Loop over file does not execute; no output generated. |
| File without trailing newline | Pass | Handled by `else raw_line`; output record receives `\n`. |
| Zero matching lines | Pass | Returns `""`. |
| Pattern with regex metacharacters (`.*+?[]^$`) | Pass | Handled as literal fixed strings via `in` and `==`. |
| `-l` with `-n` | Pass | `-l` takes precedence; line numbers suppressed. |
| `-l` with multiple files | Pass | Outputs each matching filename without `filename:` prefix. |

---

## Recommended Fixes
Apply the following optimizations and guards in `grep.py`:

1. **Hoist `pattern.lower()` outside the loop:**
   ```python
   def grep(pattern, flags, files):
       number_lines, list_files, ignore_case, invert, whole_line = _parse_flags(flags)
       if ignore_case:
           pattern = pattern.lower()
       ...
   ```
2. **Support both `\r\n` and `\n` line endings cleanly:**
   ```python
   if raw_line.endswith("\r\n"):
       text = raw_line[:-2]
   elif raw_line.endswith("\n"):
       text = raw_line[:-1]
   else:
       text = raw_line
   ```
