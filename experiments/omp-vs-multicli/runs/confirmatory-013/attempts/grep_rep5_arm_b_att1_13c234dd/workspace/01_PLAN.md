# Implementation Guide: `grep.py`

This document is the complete design for implementing `grep(pattern, flags, files)` in `grep.py`. It is derived from `README.md`, `public_test.py`, and the stub signature. Do not change tests. Implement only `grep.py`.

## 1. Problem summary

Implement a simplified, **fixed-string** `grep`:

1. Search for `pattern` in one or more files, in the given file order.
2. Collect lines that match (or, with `-v`, lines that do **not** match).
3. Return a **single string** of formatted output records, each ending with `\n`, in discovery order.

This is **not** regex grep. The pattern is a literal substring (or, with `-x`, a literal whole-line equality). Do not use `re`. Special characters in the pattern are ordinary characters.

## 2. Function contract

```python
def grep(pattern, flags, files):
    ...
```

| Parameter | Type in tests | Meaning |
|-----------|----------------|---------|
| `pattern` | `str` | Literal search string. May be empty. |
| `flags` | `str` | Space-separated short flags, e.g. `""`, `"-n"`, `"-n -i -x"`. |
| `files` | `list[str]` | File paths, one or more in the intended API. Process in list order. |

**Return type:** `str`. Never `None`, never a list.

- If there are matches (or inverted matches) to report, return their formatted lines concatenated.
- If there is nothing to report, return `""` (empty string, not `"\n"`).

The public test uses `assertMultiLineEqual`, so output must match **exactly**: prefixes, colons, line numbers, original line text, and trailing newlines.

## 3. File I/O constraint (critical)

`public_test.py` patches **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

Therefore:

- Open files with the builtin **`open(filename)`** (text mode is the default). A `with open(filename) as fh:` block is correct.
- Do **not** use `pathlib.Path.read_text`, `io.open` under another name, or pre-read files from disk. The mock never touches the real filesystem; unknown names raise `RuntimeError`.
- Do **not** import or call `open` in a way that bypasses the `grep` module global (e.g. `builtins.open` is not what the patch replaces unless you also used that name inside `grep.py`; using the unqualified builtin `open` inside `grep.py` is the required path because it becomes `grep.open` after function creation in CPython).
- Iterate the file object (or `readline` / `readlines`). Text mode uses universal newlines, so each yielded line is `content + "\n"` except a possible last line without a terminator.

Fixture files in tests always end with a final `\n`, so every line from `for line in fh` includes a trailing newline.

## 4. Architecture

Keep a small, linear pipeline. No classes are required.

```
parse_flags(flags)
        │
        ▼
for each filename in files (given order):
        │
        ├─ open(filename)
        ├─ for lineno, raw_line in enumerate(file, start=1):
        │       strip one trailing "\n" → text
        │       matched = line_matches(text, pattern, options)
        │       if invert: matched = not matched
        │       if matched:
        │           if -l: emit filename + "\n"; stop this file
        │           else:  emit format_record(...)
        ▼
join all emitted records → return str
```

Suggested internal helpers (names are not required):

- `_parse_flags(flags) -> dict` or a small namespace of booleans
- `_matches(line_text, pattern, ignore_case, entire_line) -> bool`
- `_format_line(filename, lineno, line_text, *, show_file, show_number) -> str`

A single function is also acceptable if it stays readable.

## 5. Flag parsing

`flags` is a **string**. Parse with `flags.split()` (splits on any whitespace, treats empty/`""` as no flags).

Recognized tokens:

| Token | Name | Effect |
|-------|------|--------|
| `-n` | line numbers | Prefix the 1-based line number and `:` |
| `-l` | files with matches | Output only the file name, once, if the file has ≥1 selected line |
| `-i` | ignore case | Compare pattern and line case-insensitively |
| `-v` | invert | Select lines that **fail** the match test |
| `-x` | entire line | Match only if the (stripped) line equals the pattern, not a substring |

Rules:

- Order of flags in the string does not matter.
- Duplicate flags are harmless (treat as present).
- Unknown tokens: ignore them (tests only pass the five flags above).
- Combined bunched flags like `-nix` are **not** part of the public tests; do not require support. Tests pass separate tokens: `"-n -i -x"`.
- Do not accept a list unless you also still accept a string. The stub and public test use a string. Implement string parsing as the source of truth.

Store flags as booleans, e.g.:

```python
parts = flags.split()
ignore_case = "-i" in parts
invert      = "-v" in parts
entire_line = "-x" in parts
line_number = "-n" in parts
files_only  = "-l" in parts
```

Membership in the split list is enough; no need for a `set` unless you prefer it.

## 6. Matching algorithm

Work on the line **without** its trailing newline.

```python
text = raw_line.rstrip("\n")
```

Use only `rstrip("\n")`, not `strip()`, so leading/trailing spaces remain part of the line (they matter for `-x` and for substring search).

### 6.1 Case folding

If `-i`:

- Compare using case-folded copies, e.g. `pattern.lower()` and `text.lower()`.
- Do **not** mutate the text used for output. Output always uses the original file line (minus you re-adding `\n` as specified below).

ASCII case folding via `str.lower()` is sufficient for the exercise corpus (English poetry). Do not use locale-dependent folding.

### 6.2 Match test (before invert)

Let `p` and `t` be the possibly-lowercased pattern and line text.

- **Default (no `-x`):** `p in t` (literal substring).
- **With `-x`:** `p == t` (whole line, after newline strip).

Empty pattern:

- Default: `"" in t` is `True` for every line, including empty lines. Every line matches.
- With `-x`: only a line whose stripped text is `""` matches (an empty line).

### 6.3 Invert (`-v`)

Applied **after** the match test:

```python
selected = (not matched) if invert else matched
```

Combinations:

- `-v` without `-x`: lines that do **not** contain the substring.
- `-v -x`: lines that are **not** exactly equal to the pattern.
- `-v -i`: inversion after case-insensitive match.
- `-v -i -x`: inversion after case-insensitive whole-line equality.

`-v` does not change output format, only which lines are selected.

## 7. Output formatting

Each selected line becomes one output record ending in `\n`. Concatenate records with no extra separators and no trailing extra blank line beyond those newlines.

### 7.1 `-l` (files with matches) — highest output precedence

If `-l` is set:

- When a file has **at least one selected line**, emit **exactly** `"{filename}\n"`.
- Do **not** emit line text, line numbers, or `filename:` prefixes.
- Emit each matching file **once**, at the moment the first selected line is found, then **stop scanning that file** and go to the next path.
- `-n` is ignored when `-l` is present (`-n -l` still prints only the file name). This is an explicit expected behavior of the exercise.
- `-l` still respects `-i`, `-v`, and `-x` for deciding whether a line is selected.
- File order is the order of `files`. A file with no selected lines contributes nothing.

### 7.2 Normal line output (no `-l`)

Let `text` be the line without `\n`. Always emit `text + "\n"` as the body (even if the original last line lacked a newline; the tests always include newlines, and a consistent `text + "\n"` matches `assertMultiLineEqual` expectations).

Build an optional prefix, then join with `:`:

```
[filename:][lineno:]text\n
```

Rules:

| Condition | Prefix |
|-----------|--------|
| One file, no `-n` | *(none)* — just `text\n` |
| One file, `-n` | `"{lineno}:{text}\n"` |
| Multiple files (`len(files) > 1`), no `-n` | `"{filename}:{text}\n"` |
| Multiple files, `-n` | `"{filename}:{lineno}:{text}\n"` |

Details:

- **Multiple-file mode** depends on `len(files) > 1`, not on how many files actually contained matches. Searching three files and matching only one still prefixes `iliad.txt:`.
- Searching a **single** file never prefixes the file name (unless `-l`).
- Line numbers are **1-based** and count **every** line in the file, including lines that were not selected. A match on physical line 9 prints `9`, not a match index.
- The colon after the file name (when present) comes **before** the line number (when present): `file:N:text`, never `file:text:N` or `N:file:text`.
- Do not pad line numbers.
- Preserve the original line’s characters exactly (punctuation, spacing, existing case).

### 7.3 Return value assembly

```python
return "".join(records)
```

If `records` is empty, this is `""`.

## 8. Control flow per file

```text
for filename in files:
    with open(filename) as fh:
        for lineno, raw in enumerate(fh, start=1):
            text = raw.rstrip("\n")
            matched = match(text, pattern)
            if invert:
                matched = not matched
            if not matched:
                continue
            if files_only:
                records.append(filename + "\n")
                break
            records.append(format_line(...))
```

- `break` on `-l` after the first hit is both correct (one name per file) and efficient.
- Do not `break` in normal mode; collect every selected line.
- Do not rewind or read the file twice.

## 9. Edge cases

| Case | Handling |
|------|----------|
| No flags (`""` or whitespace-only) | Substring search, no prefixes beyond multi-file names |
| No matches | `""` |
| Pattern not present, various flags (`-n -l -x -i`) | Still `""` if nothing is selected |
| Several matches in one file | All matching lines, file order |
| `-x` with a substring that is not the whole line | No match (e.g. `"may"` vs a longer line) |
| `-x` with the exact full line | Match that line |
| `-i` | `"FORBIDDEN"` matches `"Forbidden"` |
| `-i -x` | Whole-line equality ignoring case |
| `-n -i -x` together | Whole-line, case-insensitive, numbered |
| `-l` + `-n` | File name only |
| `-l` + `-v` | File name if the file has at least one **non**-matching line |
| `-x -v` | Every line except exact matches of the pattern |
| Multiple files, one match | Prefix that file’s name; other files silent |
| Multiple files, `-l` | Names of files that have ≥1 selected line, each once, in `files` order |
| Multiple files, `-n` | `filename:lineno:text\n` |
| Empty `files` list | Return `""` (no iteration). Not required by README but safe |
| Empty pattern | Every line matches as substring; with `-x`, only empty lines |
| Pattern with punctuation/spaces | Literal; do not interpret as regex |
| Leading/trailing spaces on a line | Significant; do not trim |
| File with zero lines | No output for that file (`-l` does not print it; `-l -v` also does not, because there is no selected line) |
| Last line without `\n` | `rstrip("\n")` still yields the text; emit `text + "\n"` |
| Unknown file name | Let `open` raise (the mock raises `RuntimeError`); do not catch |
| Flag string with extra spaces | `split()` already collapses whitespace |

## 10. Combinations to get right (exercise-style scenarios)

These are the behaviors implied by the README and the public fixture files (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`). Use them as mental tests while implementing.

**Single file**

- `"Agamemnon"` in `iliad.txt` → `Of Atreus, Agamemnon, King of men.\n`
- `"Forbidden"` with `-n` in `paradise-lost.txt` → `2:Of that Forbidden Tree, whose mortal tast\n`
- `"FORBIDDEN"` with `-i` in `paradise-lost.txt` → same line, original case, no number
- `"Forbidden"` with `-l` in `paradise-lost.txt` → `paradise-lost.txt\n`
- Exact line `"With loss of Eden, till one greater Man"` with `-x` → that line plus `\n`
- `"OF ATREUS, AGAMEMNON, KING OF MEN."` with `-n -i -x` in `iliad.txt` → `9:Of Atreus, Agamemnon, King of men.\n`
- `"may"` in `midsummer-night.txt` → three lines (3, 5, 6 of that file)
- `"may"` with `-n` → `3:...`, `5:...`, `6:...`
- `"may"` with `-x` → `""`
- `"ACHILLES"` with `-i` in `iliad.txt` → two lines (first and the “noble Chief Achilles” line)
- `"Of"` with `-v` in `paradise-lost.txt` → lines that do not contain the substring `Of` (case-sensitive: lines 3, 5, 6, 8 of that file)
- `"Gandalf"` with `-n -l -x -i` → `""`
- `"ten"` with `-n -l` in `iliad.txt` → `iliad.txt\n` only
- `"Illustrious into Ades premature,"` with `-x -v` in `iliad.txt` → every line except that exact line

**Multiple files** (`["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"]`)

- Always prefix `filename:` on content lines.
- `"Agamemnon"` → `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
- `"may"` → three `midsummer-night.txt:` lines
- `"who"` with `-l` → `iliad.txt\nparadise-lost.txt\n` (both contain `who`; midsummer-night does not)
- `"may"` with `-n` → `midsummer-night.txt:3:...` etc.
- `"ACHILLES"` with `-i` → two `iliad.txt:` lines
- Invert and case-insensitive combinations must prefix every emitted line with its file name

## 11. Data structures

Keep it minimal:

- `flags` → a handful of `bool`s (or a `set` of flag strings).
- `records`: a `list[str]` of complete output lines (each already including `\n`), then `"".join`.
- Optionally precompute `pattern_cmp = pattern.lower() if ignore_case else pattern` once outside the file loop.
- `show_file = len(files) > 1` computed once.

No index, automaton, or buffering beyond one file handle is needed. Files in the fixture are tiny.

Do not store all file contents in a dict keyed by name; read via `open` so the mock works.

## 12. What not to do

- Do not implement POSIX regex, `re.search`, or globbing.
- Do not write matches to stdout; **return** the string.
- Do not add a CLI / `argparse` layer; the API is the function.
- Do not strip `\r` separately in a way that changes visible text; text mode already normalizes newlines.
- Do not use `str.strip()` on lines.
- Do not prefix the filename when `len(files) == 1` except for `-l`.
- Do not emit line numbers under `-l`.
- Do not catch `open` failures.
- Do not edit `public_test.py` or add tests that the implementer must keep; the implementer only fills `grep.py`.

## 13. Suggested implementation sketch

This is the intended algorithm, not a mandate on helper names.

```python
def grep(pattern, flags, files):
    flag_list = flags.split()
    ignore_case = "-i" in flag_list
    invert = "-v" in flag_list
    entire_line = "-x" in flag_list
    show_number = "-n" in flag_list
    files_only = "-l" in flag_list
    show_file = len(files) > 1

    needle = pattern.lower() if ignore_case else pattern
    out = []

    for filename in files:
        with open(filename) as fh:
            for lineno, raw in enumerate(fh, start=1):
                text = raw.rstrip("\n")
                haystack = text.lower() if ignore_case else text
                matched = (haystack == needle) if entire_line else (needle in haystack)
                if invert:
                    matched = not matched
                if not matched:
                    continue
                if files_only:
                    out.append(filename + "\n")
                    break
                prefix_parts = []
                if show_file:
                    prefix_parts.append(filename)
                if show_number:
                    prefix_parts.append(str(lineno))
                if prefix_parts:
                    out.append(":".join(prefix_parts) + ":" + text + "\n")
                else:
                    out.append(text + "\n")

    return "".join(out)
```

This sketch is complete for the exercise. The implementer may split helpers for clarity but must preserve these semantics.

## 14. Verification notes for the implementer

- Run `python -m unittest public_test.py` (or the project’s equivalent). The public file currently contains one case: `"Agamemnon"` / `""` / `["iliad.txt"]`.
- Held-out tests will cover the rest of the matrix above: all five flags, combinations, single vs multiple files, empty result, `-l` vs `-n` precedence, invert + entire-line, case folding.
- Matching must stay literal so patterns that would be special in regex still work as plain text.

## 15. File to change

- **Implement:** `grep.py` (`grep` function; optional private helpers in the same file).
- **Do not change:** `public_test.py`, `README.md`, this plan.
