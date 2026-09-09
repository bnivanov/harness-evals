# Code Review: `grep.py`

## 1. Executive Summary

- **Public Test Suite Status**: `python3 -m unittest public_test.py` **PASSED** (Ran 1 test in 0.000s, exit code 0).
- **Overall Quality**: The implementation in `grep.py` is clean, concise, and correctly adheres to the primary Unix `grep` specification described in [README.md](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/README.md) and the testing harness in [public_test.py](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/public_test.py).
- **Key Findings**:
  1. *Minor Performance Trap*: `pattern.lower()` is evaluated redundantly on every line in every file when `-i` is active.
  2. *Minor Algorithmic Inefficiency*: `_line_body()` is invoked twice for every matching line.
  3. *Portability / Edge-Case Delimiter Risk*: `_line_body()` only strips `\n`, which leaves a trailing `\r` if CRLF (`\r\n`) lines are encountered in `io.StringIO` mocks or Windows line endings, causing whole-line matching (`-x`) to fail.
  4. *Flag Tokenization Limitation*: Flag parsing assumes space-separated flags (e.g., `"-n -l"`), but does not support clustered shorthand flags (e.g., `"-nl"`).

---

## 2. Specification & Contract Compliance Audit

| Requirement | Specification | Status | Notes |
|---|---|---|---|
| **Public API** | `grep(pattern, flags, files)` returning `str` | **Compliant** | Defined as expected. Returns `""` on no matches. |
| **Mockable I/O** | Calls `open(filename)` as global in `grep` module | **Compliant** | Compatible with `@mock.patch("grep.open", ...)` in test harnesses. |
| **Context Management** | Use `with open(...)` | **Compliant** | Safely manages file descriptors with automatic closure. |
| **Streaming Iteration** | Iterate lines lazily without reading whole file into memory | **Compliant** | Uses `enumerate(file_handle, start=1)` iterator. |
| **Line Numbering (`-n`)** | 1-based, decimal, no padding | **Compliant** | Correctly uses `start=1`. Formatted as `str(line_number)`. |
| **File Listing (`-l`)** | Only filenames of files with $\ge 1$ match | **Compliant** | Appends `filename + "\n"` and executes `break` to next file. |
| **Precedence: `-l` over `-n`** | `-l` suppresses line content and line numbers | **Compliant** | Evaluated before line prefixing; suppresses `-n`. |
| **Case Insensitivity (`-i`)** | Case-insensitive match, preserve original case in output | **Compliant** | Compares `.lower()` while preserving `body` for output. |
| **Invert Matching (`-v`)** | Inverts line match condition | **Compliant** | Returns `not matched if flags["invert"] else matched`. |
| **Whole Line Match (`-x`)** | Matches pattern against entire line content | **Compliant** | Compares `body == pattern`. |
| **Prefix Formatting** | Multiple files: `file:`, Multiple + `-n`: `file:num:`, Single + `-n`: `num:` | **Compliant** | Joined with `:` cleanly; colons placed correctly without extra spaces. |
| **Output Delimiters** | Every output record ends with `\n` | **Compliant** | Strips trailing newline from raw line and re-appends `\n`. |

---

## 3. In-Depth Audit Findings

### 3.1 Performance Traps & Redundant Computation

#### Finding 1: Repeated `pattern.lower()` evaluation inside inner loop
- **Location**: [`_line_matches`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/grep.py#L18-L24)
- **Issue**:
  ```python
  if flags["ignore_case"]:
      body = body.lower()
      pattern = pattern.lower()
  ```
  `pattern.lower()` is re-executed for every line of every file being searched. If searching through large files (e.g., $10^5$ lines), this allocates and transforms the pattern string $10^5$ times unnecessarily.
- **Severity**: Low / Performance trap.
- **Fix**: Precompute the search pattern once before the file iteration loop in `grep()` (or prepare `pattern_to_match = pattern.lower() if parsed_flags["ignore_case"] else pattern`).

#### Finding 2: Double extraction of line body
- **Location**: [`_line_matches`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/grep.py#L19) and [`grep`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/grep.py#L48)
- **Issue**: `_line_body(raw_line)` is called inside `_line_matches()`, and then called again immediately on line 48 in `grep()` to format the prefix.
- **Severity**: Minor optimization.
- **Fix**: Extract `body = _line_body(raw_line)` once at the top of the line iteration loop and pass `body` directly into `_line_matches(body, pattern, parsed_flags)`.

---

### 3.2 Edge Cases & Algorithmic Flaws

#### Finding 3: CRLF (`\r\n`) handling in `_line_body`
- **Location**: [`_line_body`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/grep.py#L12-L15)
- **Issue**:
  ```python
  def _line_body(raw_line):
      if raw_line.endswith("\n"):
          return raw_line[:-1]
      return raw_line
  ```
  While Python's standard `open()` translates `\r\n` to `\n` in universal newlines mode, mock objects such as `io.StringIO` initialized with CRLF strings (or raw binary streams) retain `\r\n`. Slicing `raw_line[:-1]` strips `\n` but leaves `\r`. Consequently:
  - `-x` (entire line match) will check `body == pattern` (e.g. `"line\r" == "line"`), which evaluates to `False`.
  - Emitted lines with trailing newline will end up with `\r\n` while other lines have `\n`.
  - Using `.rstrip()` or `.strip()` is dangerous because trailing spaces are part of the line content and required for `-x`.
- **Severity**: Edge case / Compatibility risk.
- **Fix**: Use `raw_line.removesuffix("\r\n").removesuffix("\n")` or `raw_line[:-2] if raw_line.endswith("\r\n") else (raw_line[:-1] if raw_line.endswith("\n") else raw_line)`.

#### Finding 4: Clustered CLI flags (e.g., `"-nx"`, `"-in"`)
- **Location**: [`_parse_flags`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/grep.py#L1-L9)
- **Issue**:
  ```python
  def _parse_flags(flags):
      tokens = flags.split()
      return {
          "line_numbers": "-n" in tokens,
          "filenames_only": "-l" in tokens,
          "ignore_case": "-i" in tokens,
          "invert": "-v" in tokens,
          "entire_line": "-x" in tokens,
      }
  ```
  `"-n" in tokens` checks for exact token matches. Canonical Exercism Python test suites pass space-delimited flags like `"-n -i"`, which works. However, standard Unix CLI `grep` allows bundling single-letter flags (e.g., `"-nl"`, `"-ivx"`). Any clustered flag string is ignored by `_parse_flags`.
- **Severity**: Minor / Non-standard input format limitation.
- **Fix**: Optionally check if any token starts with `"-"` and contains the flag character:
  `"n" in token for token in tokens if token.startswith("-")`.

---

### 3.3 Off-by-One Audit

- **Line numbering**: Line numbers use `enumerate(file_handle, start=1)`. The first line in a file is numbered `1`. Verified: **No off-by-one error**.
- **String slicing**: `raw_line[:-1]` removes exactly the trailing `\n`. Verified: **No off-by-one error**.
- **Multi-file condition**: `len(files) > 1` triggers prefixing for 2 or more files. When `len(files) == 1`, no filename prefix is attached (unless `-l` is passed, which prints the file name alone). Verified: **No off-by-one error**.

---

## 4. Required & Recommended Fixes

Below is the recommended refactoring of [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_6et0bm0l/grep.py) to resolve the identified performance trap and edge cases:

```python
def _parse_flags(flags):
    tokens = flags.split()
    return {
        "line_numbers": any("n" in t for t in tokens if t.startswith("-")),
        "filenames_only": any("l" in t for t in tokens if t.startswith("-")),
        "ignore_case": any("i" in t for t in tokens if t.startswith("-")),
        "invert": any("v" in t for t in tokens if t.startswith("-")),
        "entire_line": any("x" in t for t in tokens if t.startswith("-")),
    }


def _line_body(raw_line):
    # Strip \r\n or \n without stripping legitimate trailing spaces
    return raw_line.removesuffix("\r\n").removesuffix("\n")


def _line_matches(body, pattern, flags):
    if flags["ignore_case"]:
        body = body.lower()

    if flags["entire_line"]:
        matched = body == pattern
    else:
        matched = pattern in body

    return not matched if flags["invert"] else matched


def grep(pattern, flags, files):
    parsed_flags = _parse_flags(flags)
    multiple_files = len(files) > 1
    # Pre-fold pattern once outside the line loops
    search_pattern = pattern.lower() if parsed_flags["ignore_case"] else pattern
    results = []

    for filename in files:
        with open(filename) as file_handle:
            for line_number, raw_line in enumerate(file_handle, start=1):
                body = _line_body(raw_line)
                if not _line_matches(body, search_pattern, parsed_flags):
                    continue

                if parsed_flags["filenames_only"]:
                    results.append(filename + "\n")
                    break

                prefix = []
                if multiple_files:
                    prefix.append(filename)
                if parsed_flags["line_numbers"]:
                    prefix.append(str(line_number))

                if prefix:
                    results.append(":".join(prefix) + ":" + body + "\n")
                else:
                    results.append(body + "\n")

    return "".join(results)
```

---

## 5. Verification Matrix

The following test matrix was audited and validated against the implementation logic:

| Scenario | Pattern | Flags | Files | Expected Behavior | Audit Result |
|---|---|---|---|---|---|
| Single file, 1 match | `"Agamemnon"` | `""` | `["iliad.txt"]` | `Of Atreus, Agamemnon, King of men.\n` | PASS |
| Single file, several matches | `"may"` | `""` | `["midsummer-night.txt"]` | 3 lines without prefix | PASS |
| Single file, no match | `"Zorba"` | `""` | `["iliad.txt"]` | `""` | PASS |
| Line numbers | `"Achilles"` | `"-n"` | `["iliad.txt"]` | `1:...` and `8:...` | PASS |
| Case insensitive | `"ACHILLES"` | `"-i"` | `["iliad.txt"]` | Matches 2 lines, outputs original case | PASS |
| Entire line | `"With loss..."` | `"-x"` | `["paradise-lost.txt"]` | Exact match only; partial fails | PASS |
| Invert | `"Of"` | `"-v"` | `["paradise-lost.txt"]` | All lines not containing `"Of"` | PASS |
| Filenames only | `"Achilles"` | `"-l"` | `["iliad.txt"]` | `"iliad.txt\n"` | PASS |
| `-n` + `-l` precedence | `"Achilles"` | `"-n -l"`| `["iliad.txt"]` | `"iliad.txt\n"` (`-l` wins over `-n`) | PASS |
| `-i` + `-x` combination | lower pattern | `"-i -x"`| `["paradise-lost.txt"]` | Matches full line case-insensitively | PASS |
| `-v` + `-x` combination | full pattern | `"-v -x"`| `["paradise-lost.txt"]` | All lines except exact match | PASS |
| `-l` + `-v` combination | `"Achilles"` | `"-l -v"`| `["iliad.txt"]` | `"iliad.txt\n"` | PASS |
| Multiple files, 1 match | `"Agamemnon"` | `""` | 3 files | `"iliad.txt:Of Atreus..."` | PASS |
| Multiple files, several matches | `"may"` | `""` | 3 files | `"midsummer-night.txt:..."` | PASS |
| Multiple files, `-n` | `"that"` | `"-n"` | 3 files | `file:line:content\n` | PASS |
| Multiple files, `-l` | `"who"` | `"-l"` | 3 files | Matching files listed once each | PASS |
| Literal regex characters | `"hello.world"`| `""` | `["regex-chars.txt"]` | Fixed string match (`.` not wildcard) | PASS |
| Empty file | `"anything"` | `""` / `"-v"` / `"-l"` | `["empty.txt"]` | `""` (no lines emitted) | PASS |
| Missing trailing newline | `"hello"` | `""` | `["no-newline.txt"]` | Emits `"hello world\n"` | PASS |
