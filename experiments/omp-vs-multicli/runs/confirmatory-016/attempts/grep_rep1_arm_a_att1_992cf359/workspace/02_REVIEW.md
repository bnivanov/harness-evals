# Code Review: `grep.py`

## 1. Executive Summary

- **Public Test Suite Status**: PASSED (`python3 -m unittest public_test.py` ran 1 test in 0.000s, OK).
- **Comprehensive Functional Audit**: Core logic conforms to the Exercism `grep` specification and Unix `grep` semantics. Single-file and multi-file outputs, line numbering, flag precedence, case-insensitivity, whole-line matching, and match inversion behave accurately.
- **Key Areas for Improvement**:
  1. **Performance Trap**: Redundant `pattern.lower()` computation and string allocation on every line in inner matching loop.
  2. **Type Robustness**: `flags.split()` assumes `flags` is always `str`; unhandled if passed as a `list`/`tuple` of flags.
  3. **Line Ending Edge Case**: Standalone carriage return `\r` (classic Mac line endings) is unhandled in `_line_body`.

---

## 2. Findings and Audits

### Finding 1 (Performance Trap): Redundant `pattern.lower()` in Inner Loop

- **Location**: `grep.py:9-13` in `_matches(body, pattern, ignore_case, whole_line, invert)`.
- **Description**:
  ```python
  if ignore_case:
      body = body.lower()
      pattern = pattern.lower()
  ```
  `pattern` is invariant throughout the execution of `grep`. When `-i` is active, calling `pattern.lower()` on every line of every file repeatedly allocates and recomputes the lowered pattern string $N$ times (where $N$ is total line count).
- **Severity**: Low/Medium (Performance trap on large inputs).
- **Required Fix**:
  Compute `lowered_pattern = pattern.lower() if ignore_case else pattern` once in `grep()` before iterating over files and lines. In `_matches`, only lower `body` when `ignore_case` is True, comparing directly against `pattern`.

---

### Finding 2 (Robustness / Edge Case): `flags` Type Handling

- **Location**: `grep.py:35`
- **Description**:
  ```python
  active_flags = set(flags.split())
  ```
  `flags.split()` expects `flags` to be a string (e.g., `"-n -i"` or `""`). If a caller passes `flags` as a list or tuple of flag strings (e.g., `["-n", "-i"]`), this raises `AttributeError: 'list' object has no attribute 'split'`.
- **Severity**: Low.
- **Required Fix**:
  Normalize flags safely:
  ```python
  active_flags = set(flags.split() if isinstance(flags, str) else flags)
  ```

---

### Finding 3 (Edge Case): Line Ending Normalization (`\r`)

- **Location**: `grep.py:1-6` in `_line_body(raw_line)`.
- **Description**:
  ```python
  def _line_body(raw_line):
      if raw_line.endswith("\r\n"):
          return raw_line[:-2]
      if raw_line.endswith("\n"):
          return raw_line[:-1]
      return raw_line
  ```
  While standard Python `open()` in universal newline mode normalizes `\r\n` and `\r` to `\n`, mock streams or raw inputs opened with explicit newline settings might contain standalone `\r`.
- **Severity**: Minor Edge Case.
- **Required Fix**:
  ```python
  def _line_body(raw_line):
      if raw_line.endswith("\r\n"):
          return raw_line[:-2]
      if raw_line.endswith(("\n", "\r")):
          return raw_line[:-1]
      return raw_line
  ```

---

## 3. Invariant and Correctness Audit

| Check | Status | Verification Detail |
|---|---|---|
| **Line numbering (1-based)** | PASS | `enumerate(input_file, start=1)` produces 1-based indices. |
| **Flag precedence (`-l` vs `-n`)** | PASS | `if list_files:` block executes and short-circuits via `continue`, suppressing `-n` and line formatting. |
| **Short-circuit on `-l`** | PASS | First matching line triggers `result.append(filename + "\n")` followed by `break`, avoiding scanning remainder of the file. |
| **Multiple files prefixing** | PASS | `multiple_files = len(files) > 1`. Filename prefix added only when `multiple_files=True` and not in `-l` mode. |
| **Output line termination** | PASS | All matched lines and file entries in `result` terminate with `\n`. Empty result returns `""`. |
| **Empty pattern (`""`)** | PASS | `"" in body` is True for all lines; with `-x`, `body == ""` matches only empty lines; `-v` inverts correctly. |
| **Empty file handling** | PASS | Empty file yields 0 iterations; no lines emitted; with `-l` and/or `-v`, no false match occurs. |
| **Resource management** | PASS | Files are opened using `with open(filename) as input_file:`, guaranteeing prompt descriptor release. |
| **Deterministic ordering** | PASS | Files processed strictly in order of `files` argument; lines processed strictly in stream order. |

---

## 4. Recommended Fix Implementation

```python
def _line_body(raw_line):
    if raw_line.endswith("\r\n"):
        return raw_line[:-2]
    if raw_line.endswith(("\n", "\r")):
        return raw_line[:-1]
    return raw_line


def _matches(body, pattern, ignore_case, whole_line, invert):
    if ignore_case:
        body = body.lower()

    if whole_line:
        matched = body == pattern
    else:
        matched = pattern in body

    return not matched if invert else matched


def _format_line(filename, line_number, body, multiple_files, with_numbers):
    prefix = []
    if multiple_files:
        prefix.append(filename)
    if with_numbers:
        prefix.append(str(line_number))

    if prefix:
        return ":".join(prefix) + ":" + body + "\n"
    return body + "\n"


def grep(pattern, flags, files):
    active_flags = set(flags.split() if isinstance(flags, str) else flags)
    ignore_case = "-i" in active_flags
    invert = "-v" in active_flags
    whole_line = "-x" in active_flags
    list_files = "-l" in active_flags
    with_numbers = "-n" in active_flags
    multiple_files = len(files) > 1

    target_pattern = pattern.lower() if ignore_case else pattern
    result = []

    for filename in files:
        with open(filename) as input_file:
            if list_files:
                for raw_line in input_file:
                    body = _line_body(raw_line)
                    if _matches(body, target_pattern, ignore_case, whole_line, invert):
                        result.append(filename + "\n")
                        break
                continue

            for line_number, raw_line in enumerate(input_file, start=1):
                body = _line_body(raw_line)
                if _matches(body, target_pattern, ignore_case, whole_line, invert):
                    result.append(
                        _format_line(
                            filename,
                            line_number,
                            body,
                            multiple_files,
                            with_numbers,
                        )
                    )

    return "".join(result)
```
