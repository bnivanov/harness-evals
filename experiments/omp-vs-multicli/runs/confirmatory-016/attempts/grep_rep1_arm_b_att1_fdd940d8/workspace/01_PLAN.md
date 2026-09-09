# Implementation Guide: `grep.py`

## 1. Goal

Implement a simplified, **fixed-string** `grep` (not a regular-expression engine).

The public function searches one or more files for lines that contain a search string, applies optional flags, and **returns** a single output string of matching lines (or file names), in the order they were found.

Do not print to stdout. Do not mutate caller-owned inputs. Do not use the `re` module or treat the pattern as a regex: characters such as `.`, `*`, `[`, `]` are literal.

---

## 2. Public contract

```python
def grep(pattern, flags, files):
    """Return the grep output string for `pattern` under `flags` in `files`."""
```

| Argument  | Type        | Meaning |
|-----------|-------------|---------|
| `pattern` | `str`       | Fixed search string. May be empty. |
| `flags`   | `str`       | Zero or more flags, space-separated (see §4). Empty string `""` means no flags. |
| `files`   | `list[str]` | One or more file names, in search order. Non-empty in this exercise. |

**Return type:** `str`

- Concatenation of every output record, each already terminated by `\n`.
- If there are no matches: return `""` (no trailing newline).

The public tests mock `grep.open` (see §3). The function must open files with the builtin `open` looked up on this module (`open(...)` inside `grep.py`), not `io.open` and not a locally rebound name that the mock cannot patch.

---

## 3. File I/O

### 3.1 How tests supply file contents

`public_test.py` patches `grep.open` so `open(fname)` returns `io.StringIO` of a canned text. The three fixtures are:

- `iliad.txt`
- `midsummer-night.txt`
- `paradise-lost.txt`

Each fixture ends with a trailing `\n`. Lines are Unix-separated.

### 3.2 How to read

```python
with open(filename) as fh:
    for line_number, raw in enumerate(fh, start=1):
        line = _strip_terminator(raw)
        ...
```

Rules:

- Iterate files in the given `files` order.
- Line numbers are **1-based** and count **every** physical line, matching or not.
- Do not skip blank lines; they are real lines (an empty line can match an empty pattern, or fail `-x` against a non-empty pattern).
- You may assume files exist and are UTF-8 text. Do not implement missing-file error handling beyond letting `open` raise.

### 3.3 Newline stripping

Text-mode iteration keeps the line terminator on every line except possibly a final line that has none.

Strip **only** a single trailing `\n`, then a single trailing `\r` if present (so `\n` and `\r\n` both become the logical line). Do **not** use `str.strip()` / `str.rstrip()` without arguments: that would remove meaningful trailing spaces.

Suggested helper:

```python
def _strip_terminator(raw: str) -> str:
    if raw.endswith("\n"):
        raw = raw[:-1]
    if raw.endswith("\r"):
        raw = raw[:-1]
    return raw
```

`str.splitlines()` is acceptable **only** if you still number lines correctly and preserve a trailing empty line when the file ends with `\n`. Prefer the per-line iterator above; it matches “for line in file” and the mock `StringIO` exactly.

---

## 4. Flag parsing

### 4.1 Supported flags

| Flag | Name                 | Effect |
|------|----------------------|--------|
| `-n` | line numbers         | Prefix each matching **content** line with `N:` (1-based). |
| `-l` | file names only      | Output each matching file’s name once; no line text, no line numbers. |
| `-i` | case-insensitive     | Compare pattern and line case-insensitively. |
| `-v` | invert match         | Select lines that **fail** the match. |
| `-x` | entire line          | Match the whole logical line, not a substring. |

### 4.2 Input shape

Canonical calls look like:

- `""` — no flags
- `"-n"`
- `"-l"`
- `"-n -l"`
- `"-n -i -x"`
- `"-x -v"`
- `"-n -l -x -i"`

Parse with `flags.split()` (whitespace-separated tokens). Membership tests:

```python
tokens = flags.split()
line_numbers = "-n" in tokens
filenames_only = "-l" in tokens
case_insensitive = "-i" in tokens
invert = "-v" in tokens
entire_line = "-x" in tokens
```

Unknown tokens can be ignored. Extra internal whitespace is already handled by `str.split()`.

### 4.3 Optional robustness (not required by public tests)

If a token is a cluster of short options such as `-nli`, you may treat each character after the leading `-` as a flag (`n`, `l`, `i`, `v`, `x`). Do **not** treat a lone `-` as a flag. Combined-form parsing is extra; space-separated canonical flags are the contract.

### 4.4 Flag interactions

- **`-l` takes precedence over `-n`.** If `-l` is set, never emit line numbers or line text. The output is only `filename\n` for each file that has at least one selected line.
- **`-i` applies before `-x` and `-v`:** case folding changes what “equal” / “contains” means; invert then flips that boolean.
- **`-v` and `-x` compose:** “lines that are not exactly the pattern” (after optional case folding).
- **`-l` and `-v` compose:** a file is listed if it contains **at least one non-matching** line (i.e. at least one line selected by the inverted predicate).
- Flags are independent otherwise. All five can appear together.

Store flags in a small structure (dataclass, `NamedTuple`, or a set of booleans) so matching and formatting do not re-parse strings.

---

## 5. Matching semantics

Matching is on the **logical line** (terminator already stripped).

### 5.1 Normalization

If `-i`:

- `needle = pattern.lower()`
- `haystack = line.lower()`

Otherwise use `pattern` and `line` unchanged.

ASCII case folding via `str.lower()` is sufficient for this exercise. Do not use locale-dependent case conversion.

### 5.2 Predicate (before invert)

- If `-x`: `matched = (haystack == needle)`
- Else: `matched = (needle in haystack)`  — substring, including empty needle

### 5.3 Invert

If `-v`: `matched = not matched`.

A line is **selected** iff `matched` is true after invert.

### 5.4 Important matching facts

| Situation | Result |
|-----------|--------|
| Empty `pattern`, no `-x` | Every line is a substring match (`"" in s` is true). |
| Empty `pattern`, `-x` | Only empty logical lines match. |
| Pattern with regex metacharacters | Literal substring / equality. |
| Same line contains the pattern several times | One selected line, not one per occurrence. |
| `-i` | `FORBIDDEN` matches `Forbidden`; `ACHILLES` matches `Achilles`. |
| No `-i` | `Of` does **not** match `of`. |
| `-x` and extra surrounding text | Not a match. |
| `-x` and equal line | Match (subject to `-i` / `-v`). |

Do **not** search the filename. Do **not** include the `\n` terminator in the comparison.

---

## 6. Output formatting

Build a list of output records (each ending in `\n`) and `return "".join(records)`.

### 6.1 `-l` (file-name mode)

For each file, if **any** line is selected:

- Append `f"{filename}\n"`.
- Do **not** append further lines from that file.
- Do **not** add a colon after the name.
- Do **not** emit line numbers even if `-n` is also set.

Files with zero selected lines contribute nothing.

Order: the order of `files`. Each matching file appears **at most once**.

This applies to **both** one-file and multi-file invocations. A single-file `-l` match still prints the file name, not the matching text.

### 6.2 Content mode (no `-l`)

For every selected line, emit one record:

```
{file_prefix}{number_prefix}{line}\n
```

- `file_prefix`:
  - If `len(files) > 1`: `f"{filename}:"`
  - If `len(files) == 1`: `""`
  - The decision uses the length of the **input** `files` list, not “how many files actually contained a match”. One match among three files still gets a `filename:` prefix.
- `number_prefix`:
  - If `-n`: `f"{line_number}:"` (decimal, no padding)
  - Else: `""`
- `line`: the logical line with terminator already stripped; then add exactly one `\n` for the output record.

**Prefix order is always filename, then line number, then text:**

| Files | `-n` | Example |
|-------|------|---------|
| 1 | no | `Of Atreus, Agamemnon, King of men.\n` |
| 1 | yes | `9:Of Atreus, Agamemnon, King of men.\n` |
| >1 | no | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| >1 | yes | `paradise-lost.txt:4:With loss of Eden, till one greater Man\n` |

No space after colons.

### 6.3 Empty result

Zero selected lines across all files → `""`.

---

## 7. Main algorithm

```
parse flags from the flags string
show_filename := (len(files) > 1)
records := []

for filename in files:
    opened = open(filename)          # must be module-global open
    with opened as fh:
        for line_number, raw in enumerate(fh, start=1):
            line := strip terminator from raw
            if not line_selected(line, pattern, flags):
                continue
            if filenames_only:
                records.append(filename + "\n")
                break                # first hit is enough for -l
            record := ""
            if show_filename:
                record += filename + ":"
            if line_numbers:
                record += str(line_number) + ":"
            record += line + "\n"
            records.append(record)

return "".join(records)
```

Complexity: O(total bytes of all files). One pass per file. The `-l` early `break` is optional for correctness but recommended.

Keep matching, flag parsing, and formatting in separate helpers so combinations stay easy to reason about.

---

## 8. Suggested module layout

Keep everything in `grep.py`. No extra packages.

```text
grep.py
├── grep(pattern, flags, files) -> str     # public API
├── _parse_flags(flags) -> FlagSet         # booleans for n/l/i/v/x
├── _strip_terminator(raw) -> str
├── _line_selected(line, pattern, flags) -> bool
└── (optional) _format_record(...) -> str
```

`FlagSet` may be a `@dataclass(frozen=True)` or a simple namespace of booleans. Avoid a dict of strings.

Do not add CLI `argparse` / `sys.argv` handling unless something else requires it; the exercise is the function.

---

## 9. Worked examples (from the public fixture texts)

Use these as executable mental tests. File contents are those in `public_test.py`.

### Single file

| Call | Output |
|------|--------|
| `grep("Agamemnon", "", ["iliad.txt"])` | `Of Atreus, Agamemnon, King of men.\n` |
| `grep("Forbidden", "-n", ["paradise-lost.txt"])` | `2:Of that Forbidden Tree, whose mortal tast\n` |
| `grep("FORBIDDEN", "-i", ["paradise-lost.txt"])` | `Of that Forbidden Tree, whose mortal tast\n` |
| `grep("Forbidden", "-l", ["paradise-lost.txt"])` | `paradise-lost.txt\n` |
| `grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])` | that full line + `\n` |
| `grep("OF ATREUS, AGAMEMNON, KING OF MEN.", "-n -i -x", ["iliad.txt"])` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("may", "", ["midsummer-night.txt"])` | three lines (3, 5, 6 of that file), in order, each with `\n` |
| `grep("may", "-n", ["midsummer-night.txt"])` | `3:...`, `5:...`, `6:...` |
| `grep("may", "-x", ["midsummer-night.txt"])` | `""` |
| `grep("ACHILLES", "-i", ["iliad.txt"])` | line 1 and line 8 |
| `grep("Of", "-v", ["paradise-lost.txt"])` | lines that do **not** contain the substring `Of` (case-sensitive): 3, 5, 6, 8 |
| `grep("Gandalf", "-n -l -x -i", ["iliad.txt"])` | `""` |
| `grep("ten", "-n -l", ["iliad.txt"])` | `iliad.txt\n` (`-l` wins over `-n`) |
| `grep("Illustrious into Ades premature,", "-x -v", ["iliad.txt"])` | every iliad line **except** that exact line |

### Multiple files

`files = ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"]`

| Call | Output notes |
|------|----------------|
| `grep("Agamemnon", "", files)` | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `grep("may", "", files)` | three `midsummer-night.txt:...` lines |
| `grep("that", "-n", files)` | `midsummer-night.txt:5:...`, `:6:...`, `paradise-lost.txt:2:...`, `:6:...` |
| `grep("who", "-l", files)` | `iliad.txt\nparadise-lost.txt\n` |
| `grep("may", "-n -l", files)` | `midsummer-night.txt\n` |
| `grep("TO", "-i", files)` | every line containing `to`/`To`/`TO`/… with `filename:` prefix |
| `grep("a", "-v", files)` | lines with no lowercase `a`, each prefixed by filename |
| `grep("But I beseech your grace that I may know", "-x", files)` | `midsummer-night.txt:` + that line |
| `grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", files)` | `paradise-lost.txt:4:With loss of Eden, till one greater Man\n` |
| `grep("Frodo", "-n -l -x -i", files)` | `""` |

---

## 10. Edge cases to handle

1. **No matches** — return `""`, not `"\n"`.
2. **Empty pattern** — substring of every line; with `-x`, only empty lines; with `-v`, invert as usual.
3. **Empty logical line** — valid; `-x` with non-empty pattern does not select it (unless `-v`).
4. **File that is empty** — zero lines, so never selected (even with `-v`, because there is no line to invert). `-l` emits nothing for it.
5. **File whose only content is `\n`** — one empty logical line.
6. **Last line without a trailing newline** — still searched; still emitted with a `\n` in the **output** if selected.
7. **`-l` short-circuit** — first selected line is enough; do not emit the name twice.
8. **`-l` + `-n`** — names only.
9. **Single vs many files** — filename prefix depends on `len(files)`, not on match count.
10. **One file passed as a one-element list** — no `filename:` prefix in content mode; `-l` still prints the name.
11. **Duplicate file names in `files`** — process each occurrence independently (second open, second possible `-l` line). Do not unique the list unless you have a reason; the tests do not duplicate names.
12. **Pattern longer than the line** — not a substring match; `-x` requires equality, so also not a match.
13. **Overlapping or repeated occurrences on one line** — still one output record.
14. **Leading/trailing spaces in the line** — significant for `-x` and for substring search. Do not trim the line body.
15. **Spaces in the pattern** — significant; match literally.
16. **Flags string with extra spaces or empty** — `str.split()`; empty → all flags false.
17. **Invert of “no match”** — every line is selected (`-v` with a pattern that never occurs).
18. **Case folding only for comparison** — output the original line text, original filename, original digits.
19. **Do not write files; do not close anything except the `with` block.**
20. **Mocked `open`** — never call `open` before flags are parsed in a way that skips files; always open every file unless you `-l` break out of **that** file. Always open files even if the pattern is empty.

---

## 11. What not to do

- Do not use `re`, `fnmatch`, or globbing on the pattern.
- Do not print with `print()`.
- Do not implement a Unix CLI parser for `grep pattern [files...]`; flags arrive as one string.
- Do not prefix filenames when only one path is in `files` (content mode).
- Do not put a space after `:` in prefixes.
- Do not sort output; preserve file order and in-file line order.
- Do not drop the final `\n` on a selected line’s output record.
- Do not read files outside `files` and do not touch tests.

---

## 12. Implementation sketch (reference logic, not required wording)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class _Flags:
    line_numbers: bool
    filenames_only: bool
    ignore_case: bool
    invert: bool
    entire_line: bool


def _parse_flags(flags: str) -> _Flags:
    tokens = flags.split()
    return _Flags(
        line_numbers="-n" in tokens,
        filenames_only="-l" in tokens,
        ignore_case="-i" in tokens,
        invert="-v" in tokens,
        entire_line="-x" in tokens,
    )


def _strip_terminator(raw: str) -> str:
    if raw.endswith("\n"):
        raw = raw[:-1]
    if raw.endswith("\r"):
        raw = raw[:-1]
    return raw


def _selected(line: str, pattern: str, f: _Flags) -> bool:
    haystack = line.lower() if f.ignore_case else line
    needle = pattern.lower() if f.ignore_case else pattern
    ok = haystack == needle if f.entire_line else needle in haystack
    return not ok if f.invert else ok


def grep(pattern, flags, files):
    f = _parse_flags(flags)
    show_filename = len(files) > 1
    out = []
    for filename in files:
        with open(filename) as fh:
            for n, raw in enumerate(fh, start=1):
                line = _strip_terminator(raw)
                if not _selected(line, pattern, f):
                    continue
                if f.filenames_only:
                    out.append(filename + "\n")
                    break
                prefix = ""
                if show_filename:
                    prefix += filename + ":"
                if f.line_numbers:
                    prefix += f"{n}:"
                out.append(prefix + line + "\n")
    return "".join(out)
```

This sketch is complete enough to implement. Prefer this control flow over clever one-liners.

---

## 13. Verification notes for the implementer

- Run `public_test.py` after implementing. The checked-in public suite currently covers one case (`Agamemnon` in `iliad.txt` with no flags); the architecture above is sized for the full flag matrix and multi-file behavior described in `README.md`.
- Do not edit `grep.py` until the implementation phase. Do not edit tests.
- Keep helpers private (`_` prefix) so only `grep` is imported by tests.
