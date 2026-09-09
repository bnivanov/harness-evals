# 02_REVIEW.md — Code Review of grep.py

## 1. Executive Summary

- **Public Test Suite (`public_test.py`)**: PASS (`Ran 1 test in 0.000s, OK`).
- **Exercism Grep Specification**: The core logic implements all requirements from `README.md` (`-n`, `-l`, `-i`, `-v`, `-x`, and multi-file prefixing).
- **Integrity**: `grep.py` and `public_test.py` were inspected without modification.

---

## 2. Findings and Audits

### Finding 1: Performance Trap — Invariant Lowercasing Inside Inner Loop
- **Severity**: Performance
- **Location**: `grep.py:12-15` (`_matches`)
- **Problem**:
  ```python
  def _matches(text, pattern, insensitive, exact, invert):
      if insensitive:
          text = text.lower()
          pattern = pattern.lower()
  ```
  `_matches` is invoked for every line in every file. When `-i` is active, `pattern.lower()` is repeatedly computed on each iteration, creating a new string object every line. For a 100,000-line file, this performs 100,000 redundant allocations.
- **Required Fix**: Pre-process `pattern` once in `grep()` before iterating over files and lines:
  ```python
  if insensitive:
      pattern = pattern.casefold()
  ```
  Inside the per-line check, only transform `text`:
  ```python
  if insensitive:
      text = text.casefold()
  ```

---

### Finding 2: Correctness / Edge Case — Trailing `\r` with CRLF Line Endings
- **Severity**: Correctness / Portability
- **Location**: `grep.py:45`
- **Problem**:
  ```python
  text = raw_line.rstrip("\n")
  ```
  If a file or mock input uses Windows CRLF (`\r\n`) line endings (common across cross-platform checkouts or in `io.StringIO` mocks that bypass universal newlines), `raw_line.rstrip("\n")` strips only `\n`, leaving a trailing `\r` on `text`.
  Consequently:
  - Exact matching (`-x`): `"hello" == "hello\r"` evaluates to `False`, failing legitimate whole-line matches.
  - Substring matching: May introduce false mismatches or unexpected matches when pattern anchors or ends with specific characters.
- **Required Fix**: Strip `\r\n`:
  ```python
  text = raw_line.rstrip("\r\n")
  ```
  Or use:
  ```python
  text = raw_line.removesuffix("\r\n").removesuffix("\n")
  ```

---

### Finding 3: Robustness — Flag Parameter Type
- **Severity**: Robustness
- **Location**: `grep.py:1-2` (`_parse_flags`)
- **Problem**:
  ```python
  def _parse_flags(flags):
      options = set(flags.split())
  ```
  While standard Python Exercism tests supply `flags` as a space-delimited string (e.g. `""`, `"-n"`, `"-n -l"`), the Exercism problem-specification schema defines `flags` as an array of strings (e.g. `["-n", "-l"]`). If a caller passes a list or tuple of flags directly, `flags.split()` raises `AttributeError: 'list' object has no attribute 'split'`.
- **Required Fix**: Support both `str` and general iterables:
  ```python
  def _parse_flags(flags):
      options = set(flags.split()) if isinstance(flags, str) else set(flags)
  ```

---

### Finding 4: Robustness — `files` Argument as Generator/Iterator
- **Severity**: Robustness
- **Location**: `grep.py:39`
- **Problem**:
  ```python
  multiple_files = len(files) > 1
  ```
  If `files` is provided as an iterator or generator (such as `Path.glob()` or `(f for f in files)`), `len(files)` raises `TypeError: object of type 'generator' has no len()`.
- **Required Fix**: Ensure `files` is materialized as a list or tuple:
  ```python
  file_list = list(files)
  multiple_files = len(file_list) > 1
  ```

---

### Finding 5: Unicode Caseless Matching
- **Severity**: Code Quality / Best Practice
- **Location**: `grep.py:14-15`
- **Problem**: `str.lower()` does not handle all caseless matches in Unicode (e.g., German lowercase `'ß'` mapping to `'ss'`).
- **Required Fix**: Use `str.casefold()` instead of `str.lower()` for caseless text processing.

---

## 3. Off-by-One and Logic Audit

1. **Line Numbering**:
   - Uses `enumerate(file, start=1)`. Correct 1-based indexing; no off-by-one errors.
2. **Prefix Formatting**:
   - Order: `[filename:]` then `[lineno:]` then line content.
   - When both `multiple_files` and `-n` are set: `filename:lineno:content\n`.
   - Single file with `-n`: `lineno:content\n`.
   - Multiple files without `-n`: `filename:content\n`.
   - Single file without flags: `content\n`.
   - Matches specification exactly.
3. **`-l` Precedence and Short-Circuiting**:
   - When `-l` matches a line, `output.append(filename + "\n")` executes and `break` terminates the file loop.
   - Ignores `-n` formatting and line content as specified.
   - Does not duplicate filenames when multiple lines in the same file match.
   - Immediately stops reading remaining lines of that file (optimal early termination).
4. **`-v` (Invert) Logic**:
   - Evaluated as `not matched if invert else matched`.
   - Combined with `-x`: matches all lines where `text != pattern`.
   - Combined with empty lines: empty line with non-empty pattern is retained under `-v`.
   - Correctly matches GNU grep behavior.
5. **Missing Final Newline**:
   - `line = raw_line if raw_line.endswith("\n") else raw_line + "\n"` guarantees every emitted record ends with `\n`.
6. **Built-in `open` Mock Compatibility**:
   - Uses standard builtin `open(...)` within `grep.py`, maintaining compatibility with `unittest.mock.patch("grep.open", ...)` in test harnesses.

---

## 4. Recommended Target Refactoring

```python
def _parse_flags(flags):
    options = set(flags.split()) if isinstance(flags, str) else set(flags)
    return (
        "-n" in options,
        "-l" in options,
        "-i" in options,
        "-v" in options,
        "-x" in options,
    )


def _matches(text, pattern, exact, invert):
    if exact:
        matched = text == pattern
    else:
        matched = pattern in text
    return not matched if invert else matched


def _format_line(filename, lineno, raw_line, multiple_files, number):
    line = raw_line if raw_line.endswith("\n") else raw_line + "\n"
    prefix = ""
    if multiple_files:
        prefix += f"{filename}:"
    if number:
        prefix += f"{lineno}:"
    return prefix + line


def grep(pattern, flags, files):
    number, list_files, insensitive, invert, exact = _parse_flags(flags)
    file_list = list(files)
    multiple_files = len(file_list) > 1

    if insensitive:
        pattern = pattern.casefold()

    output = []

    for filename in file_list:
        with open(filename) as file:
            for lineno, raw_line in enumerate(file, start=1):
                text = raw_line.rstrip("\r\n")
                if insensitive:
                    text = text.casefold()

                if not _matches(text, pattern, exact, invert):
                    continue

                if list_files:
                    output.append(filename + "\n")
                    break

                output.append(
                    _format_line(
                        filename,
                        lineno,
                        raw_line,
                        multiple_files,
                        number,
                    )
                )

    return "".join(output)
```
