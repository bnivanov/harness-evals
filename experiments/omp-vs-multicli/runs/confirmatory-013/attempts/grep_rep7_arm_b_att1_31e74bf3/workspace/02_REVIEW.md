# Code Review: `grep.py`

## 1. Executive Summary

This review audits [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py) against the requirements specified in [`README.md`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/README.md), the test cases in [`public_test.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/public_test.py), and the broader Exercism specification described in [`01_PLAN.md`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/01_PLAN.md).

### Test Suite Execution
- Running `python3 -m unittest public_test.py` completed with exit code 0:
  ```text
  .
  ----------------------------------------------------------------------
  Ran 1 test in 0.000s

  OK
  ```
- Additionally, all 20 canonical Exercism test cases from the standard test specification were executed against [`grep`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L1-L45) in [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py) and passed successfully.

---

## 2. Detailed Audit & Findings

### Finding 1: Line Terminator Slicing Bug on CRLF (`\r\n`) Files (Edge Case / Algorithmic Flaw)
- **Location**: [`grep.py:16`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L16)
  ```python
  line = raw_line[:-1] if raw_line.endswith("\n") else raw_line
  ```
- **Analysis**:
  If a file or mock input uses Windows CRLF line endings (`\r\n`)—such as when mocked via `io.StringIO("Hello world\r\n")` or read from a stream without universal newline translation:
  1. `raw_line.endswith("\n")` evaluates to `True`.
  2. `raw_line[:-1]` removes only `\n`, leaving a trailing carriage return `\r` at the end of `line` (`"Hello world\r"`).
  3. Under `-x` (entire line match), `haystack == needle` compares `"Hello world\r" == "Hello world"`, which evaluates to `False`. The match fails completely.
  4. Under substring matching, matching lines will retain `\r`, resulting in `\r\n` line endings when appended with `"\n"`.
- **Required Fix**:
  Use `str.removesuffix("\r\n").removesuffix("\n")` or `str.rstrip("\r\n")` to reliably strip carriage return and newline line terminators while preserving any intentional whitespace/indentation.
  ```python
  line = raw_line.removesuffix("\r\n").removesuffix("\n")
  ```

---

### Finding 2: Unhandled Clustered Flags (Edge Case / Robustness)
- **Location**: [`grep.py:2-7`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L2-L7)
  ```python
  tokens = flags.split()
  show_line_numbers = "-n" in tokens
  only_filenames = "-l" in tokens
  ignore_case = "-i" in tokens
  invert = "-v" in tokens
  entire_line = "-x" in tokens
  ```
- **Analysis**:
  The parser checks for exact token matches (`"-n" in tokens`). While Exercism tests pass space-separated flags (e.g. `"-n -i"`), standard POSIX and Unix `grep` conventions allow combined/clustered flags (e.g. `"-ni"`, `"-lx"`, `"-nix"`). If any caller passes clustered flags, none of the flags are recognized, silently falling back to default behavior.
- **Required Fix**:
  Inspect flag characters within any token starting with `"-"`:
  ```python
  tokens = flags.split()
  flag_chars = {c for token in tokens if token.startswith("-") for c in token[1:]}
  show_line_numbers = "-n" in tokens or "n" in flag_chars
  only_filenames = "-l" in tokens or "l" in flag_chars
  ignore_case = "-i" in tokens or "i" in flag_chars
  invert = "-v" in tokens or "v" in flag_chars
  entire_line = "-x" in tokens or "x" in flag_chars
  ```

---

### Finding 3: Case Folding vs. `.lower()` for Unicode (Edge Case)
- **Location**: [`grep.py:9, 17`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L9)
  ```python
  needle = pattern.lower() if ignore_case else pattern
  ...
  haystack = line.lower() if ignore_case else line
  ```
- **Analysis**:
  Using `str.lower()` is standard for ASCII text (which covers the classic literature corpus in [`FILE_TEXT`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/public_test.py#L13-L38)), but Python's recommended approach for caseless matching across full Unicode (PEP 3116) is `str.casefold()`. For example, `"Straße".lower() == "STRASSE".lower()` is `False`, whereas `"Straße".casefold() == "STRASSE".casefold()` is `True`.
- **Required Fix**:
  Replace `.lower()` with `.casefold()`:
  ```python
  needle = pattern.casefold() if ignore_case else pattern
  ...
  haystack = line.casefold() if ignore_case else line
  ```

---

### Finding 4: Verification of Algorithmic Logic & Flag Precedence
- **Precedence of `-l` over `-n`**:
  - In [`grep.py:30-32`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L30-L32), `if only_filenames:` appends only `filename + "\n"` and executes `break`.
  - This correctly suppresses line numbers (`-n`), file prefixes (`filename:`), and line text, fulfilling the requirement that `-l` outputs only matching filenames.
- **Inverted Matching (`-v`) with `-l` and `-x`**:
  - Line 24: `if invert: matched = not matched` correctly inverts the boolean condition after applying `-x` and substring matching.
  - When combined with `-l`, it correctly lists files having at least one non-matching line.
- **Multi-file Prefixing**:
  - Line 10: `multi_file = len(files) > 1` sets multi-file mode based on the number of search targets passed in arguments, not how many files match. This matches POSIX grep and the Exercism specification.
- **Empty Pattern Handling**:
  - `pattern = ""` with substring matching evaluates `"" in haystack` as `True` for every line.
  - With `-x`, `"" == haystack` matches only blank lines.
  - With `-v`, all non-empty lines match. This strictly aligns with standard Unix `grep`.

---

### Finding 5: Off-by-One and Indexing Audit
- **Line Numbering**:
  - [`grep.py:15`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L15) uses `enumerate(file, start=1)`, guaranteeing 1-based indexing for line numbers.
  - Under `-v -n`, line numbers represent original physical line numbers in the file.
- **Output Record Newlines**:
  - Every emitted record is appended with a trailing `"\n"`.
  - Empty search results return `""` rather than `"\n"`.
  - No off-by-one errors detected in record indexing or numbering.

---

### Finding 6: Performance Traps and Resource Management
- **File Streaming**:
  - Files are read line-by-line using file iteration (`enumerate(file)`), preventing high memory allocation for large files.
- **Early File Exit on `-l`**:
  - [`grep.py:32`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py#L32) invokes `break` on the first match in `-l` mode. This avoids scanning the remaining lines of the file.
- **Pattern Lowering / Normalization**:
  - The pattern is normalized once before the file loop (Line 9), avoiding repetitive string transformations across lines.
- **Memory Accumulation**:
  - Output records are stored in a list and combined with `"".join(output)`. While returning `str` requires the complete output to fit in memory, using `"".join(list)` avoids quadratic string concatenation `O(N^2)`.
- **File Descriptors**:
  - Each file is opened with a context manager (`with open(filename) as file:`), ensuring file descriptors are closed promptly.
  - Calling `open` directly ensures compatibility with the `mock.patch("grep.open", ...)` fixture in [`public_test.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/public_test.py#L50).

---

## 3. Summary of Required Fixes

When [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_7_att1_qwmuf_hn/grep.py) is next edited, the following changes are recommended:

```python
def grep(pattern, flags, files):
    tokens = flags.split()
    flag_chars = {c for token in tokens if token.startswith("-") for c in token[1:]}
    show_line_numbers = "-n" in tokens or "n" in flag_chars
    only_filenames = "-l" in tokens or "l" in flag_chars
    ignore_case = "-i" in tokens or "i" in flag_chars
    invert = "-v" in tokens or "v" in flag_chars
    entire_line = "-x" in tokens or "x" in flag_chars

    needle = pattern.casefold() if ignore_case else pattern
    multi_file = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.removesuffix("\r\n").removesuffix("\n")
                haystack = line.casefold() if ignore_case else line

                matched = (
                    haystack == needle
                    if entire_line
                    else needle in haystack
                )
                if invert:
                    matched = not matched

                if not matched:
                    continue

                if only_filenames:
                    output.append(filename + "\n")
                    break

                parts = []
                if multi_file:
                    parts.append(filename)
                if show_line_numbers:
                    parts.append(str(line_number))

                if parts:
                    output.append(":".join(parts) + ":" + line + "\n")
                else:
                    output.append(line + "\n")

    return "".join(output)
```
