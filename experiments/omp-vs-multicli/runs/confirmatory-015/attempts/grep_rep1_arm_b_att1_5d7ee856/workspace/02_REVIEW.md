# 02_REVIEW.md: Code Review and Audit Report for `grep.py`

## 1. Executive Summary

This review audits the initial state of [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/grep.py) against the problem specifications in [`README.md`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/README.md), the test suite in [`public_test.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/public_test.py), and the implementation design in [`01_PLAN.md`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/01_PLAN.md).

### Current State of `grep.py`
The existing [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/grep.py) is an unimplemented stub:
```python
def grep(pattern, flags, files):
    pass
```

### Test Execution Result
Running `python3 -m unittest public_test.py` produces:
```text
F
======================================================================
FAIL: test_one_file_one_match_no_flags (public_test.GrepTest.test_one_file_one_match_no_flags)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../unittest/mock.py", line 1439, in patched
    return func(*newargs, **newkeywargs)
  File ".../public_test.py", line 55, in test_one_file_one_match_no_flags
    self.assertMultiLineEqual(
        grep("Agamemnon", "", ["iliad.txt"]), "Of Atreus, Agamemnon, King of men.\n"
    )
AssertionError: None is not an instance of <class 'str'> : First argument is not a string

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
```

**Root Cause**: The function returns `None` because of the `pass` statement, whereas the test expects a `str` return value ending with a newline.

---

## 2. Specification & Contract Analysis

### 2.1 Function Signature
```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```
- `pattern`: String literal to search for (fixed-string comparison, **not** regular expressions).
- `flags`: String containing zero or more space-separated command flags (e.g. `""`, `"-n"`, `"-n -i"`, `"-l"`).
- `files`: Non-empty list of file names to search.
- **Return value**: Single string containing all matched records concatenated, each ending in `\n`. If there are no matches, it must return an empty string (`""`).

### 2.2 Flags Specification
| Flag | Name | Semantics |
|---|---|---|
| `-n` | Line Numbers | Prepend 1-based line number and `:` to each matching line in content mode (`[file:][line_no:]line`). |
| `-l` | Files With Matches | Output only the file names of files containing at least one match, followed by `\n`. Suppresses line content and line numbers. |
| `-i` | Case-Insensitive | Perform case-insensitive string matching. |
| `-v` | Invert Match | Select non-matching lines instead of matching lines. |
| `-x` | Match Entire Line | Only consider a match if the search pattern equals the entire line body (excluding trailing newline). |

### 2.3 Mocking Requirements in `public_test.py`
In [`public_test.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/public_test.py):
```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
@mock.patch("io.StringIO", name="StringIO", wraps=io.StringIO)
```
- The test mocks `open` within the `grep` module namespace (`grep.open`).
- **Requirement**: `grep.py` must use Python's builtin `open(...)` directly in its module scope (e.g., `with open(filename) as handle:`). Do not use `pathlib.Path`, `builtins.open`, or `io.open`, as they will bypass this mock.

---

## 3. Detailed Audit: Edge Cases, Flaws, and Traps

### 3.1 Algorithmic Correctness & Fixed-String Matching
- **Literal substring vs regex**: Standard Unix `grep` uses regular expressions, but the specification explicitly states: *"Your task is to implement a simplified `grep` command, which supports searching for fixed strings."*
  - Do **not** use the `re` module.
  - Characters such as `.`, `*`, `[`, `]`, `?`, `+`, `^`, `$`, `\`, and `(` must be matched literally via Python `in` or `==`.
- **Case folding (`-i`)**:
  - Comparison must normalize both pattern and line body with `.lower()`.
  - For consistency and performance, `pattern.lower()` should be computed **once** before iterating over files.

### 3.2 Off-By-One Errors
- **Line numbering (`-n`)**:
  - Line numbers are **1-based** (line 1 is the first line of the file).
  - Use `enumerate(handle, start=1)`. Using the default `start=0` is a common off-by-one bug.
  - Line numbers must track the **physical file line number**, not the match index (i.e. skipping non-matching lines must not pause or alter the line counter).
- **Newline removal and stripping**:
  - Using `line.strip()` or `line.rstrip()` without arguments is a serious bug: it removes leading/trailing spaces or tabs, breaking exact full-line matching (`-x`) on lines with indentation or trailing whitespace.
  - Using `line[:-1]` unconditionally can drop the last character of a file if the final line does not end in `\n`.
  - Safe removal of trailing newline:
    ```python
    body = raw.removesuffix("\r\n").removesuffix("\n")
    ```
    or
    ```python
    body = raw[:-1] if raw.endswith("\n") else raw
    ```

### 3.3 Edge Cases
1. **Empty Pattern (`pattern = ""`):**
   - Normal mode: `"" in body` evaluates to `True`, so every line in every file matches.
   - Entire line (`-x`): `body == ""` is `True` only for empty lines.
   - Inverted (`-v`): Inverts the above predicates.
2. **Empty File (0 bytes):**
   - Iteration yields 0 lines.
   - Even with `-v`, an empty file yields zero matches (no lines fail to match).
   - Even with `-l` or `-l -v`, an empty file outputs nothing.
3. **Missing Trailing Newline at EOF:**
   - If the last line of a file does not terminate in `\n`, the output record must still be properly newline-terminated:
     ```python
     if not raw.endswith("\n"):
         raw += "\n"
     ```
4. **Flag Interaction `-l` with other flags:**
   - `-l` takes complete precedence over `-n` and file/line formatting.
   - Even if `-n` is set (`-n -l`), output is strictly `"{filename}\n"`.
   - When `-l` is set and a file has a match, the loop should immediately emit `"{filename}\n"` and `break` to the next file.
   - If multiple lines match in the same file, the filename must only appear **once**.
5. **Single vs Multiple Files Prefixes:**
   - When `len(files) > 1`, prepend `"{filename}:"` to every matched line in content mode.
   - When `len(files) == 1`, do **not** prepend `"{filename}:"`.
   - The prefix decision is strictly governed by `len(files) > 1`, regardless of whether matches occurred across multiple files or only one file.
6. **Flag Formatting / Parsing:**
   - `flags` may be empty `""` (where `.split()` yields `[]`).
   - Flags may have leading, trailing, or multiple internal spaces (e.g. `"-n  -i"`). Using `flags.split()` handles any amount of whitespace.
   - Duplicate flags (e.g. `"-n -n"`) are safely handled by checking membership (`"-n" in flag_tokens`).
7. **Empty `files` List:**
   - If `files` is `[]`, the function should return `""`.

### 3.4 Performance Traps
1. **Repeated String Concatenation (`+=`):**
   - Repeatedly concatenating strings (`result += ...`) in a loop has $O(M^2)$ time complexity.
   - Solution: Collect output records in a list `out = []` and return `"".join(out)` ($O(M)$ time complexity).
2. **Redundant Case Normalization in Inner Loop:**
   - Calling `pattern.lower()` inside the inner line loop computes lowercase on every line.
   - Solution: Compute `needle = pattern.lower() if ignore_case else pattern` once outside all file loops.
3. **Full File Slurping:**
   - Avoid `handle.read().splitlines()` or `handle.readlines()`, which load entire files into memory.
   - Iterate lazily with `for line_no, raw in enumerate(handle, start=1):` for $O(1)$ stream memory overhead per line.
4. **Early Exit for `-l`:**
   - Break from the file reading loop immediately after the first match under `-l` to avoid reading remaining lines.

---

## 4. Required Fixes and Complete Implementation

The implementer agent must update [`grep.py`](file:///private/var/folders/z3/tpy284jj297ck601rpn41r1m0000gp/T/pilot_grep_arm_b_1_att1_dpmc40oa/grep.py) with the following robust, clean implementation:

```python
def grep(pattern, flags, files):
    flag_tokens = flags.split()
    list_only = "-l" in flag_tokens
    print_numbers = "-n" in flag_tokens
    ignore_case = "-i" in flag_tokens
    invert = "-v" in flag_tokens
    entire_line = "-x" in flag_tokens
    multi_file = len(files) > 1

    needle = pattern.lower() if ignore_case else pattern
    out = []

    for filename in files:
        with open(filename) as handle:
            for line_no, raw in enumerate(handle, start=1):
                body = raw.removesuffix("\r\n").removesuffix("\n")
                haystack = body.lower() if ignore_case else body
                positive = (haystack == needle) if entire_line else (needle in haystack)
                keep = (not positive) if invert else positive
                if not keep:
                    continue

                if list_only:
                    out.append(filename + "\n")
                    break

                if not raw.endswith("\n"):
                    raw = raw + "\n"

                prefix = ""
                if multi_file:
                    prefix += filename + ":"
                if print_numbers:
                    prefix += str(line_no) + ":"
                out.append(prefix + raw)

    return "".join(out)
```

### Verification Checklist for Implementer:
1. Ensure standard `open()` is called directly so mock patching functions properly.
2. Confirm `public_test.py` passes: `python3 -m unittest public_test.py`.
3. Verify that `grep.py` does not introduce external dependencies or import `re`.
