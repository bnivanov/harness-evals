# grep.py Implementation Guide

This document is the complete implementation plan for `grep.py`. Implement only `grep.py`. Do not change tests. The public suite currently contains a single example, but the README defines the full contract; hidden tests will exercise every flag, flag combination, single-file vs multi-file output, and no-match cases.

---

## 1. Goal

Implement a simplified, **fixed-string** (not regex) `grep` as a pure function:

```python
def grep(pattern, flags, files):
    ...
```

It must:

1. Read the given files **in the order listed**.
2. Select lines according to `pattern` and `flags`.
3. Return one output string of selected results, in the order they were found.
4. When more than one file was passed, prefix each matching **line** with `filename:`.
5. Honor the five flags described in the README.

The function returns text. It does not print. It is not a CLI.

---

## 2. Public contract (from README + `public_test.py`)

### 2.1 Signature and types

| Argument  | Type           | Meaning |
|-----------|----------------|---------|
| `pattern` | `str`          | Fixed search string. May be empty. Not a regular expression. |
| `flags`   | `str`          | Zero or more flags, space-separated (e.g. `""`, `"-n"`, `"-n -i -x"`). |
| `files`   | `list[str]`    | File names, in search order. One or more in normal use. |

**Return type:** `str`.

- Concatenate every emitted record. Each record ends with `\n`.
- If nothing is selected, return `""` (not `"\n"`, not `None`, not a list).

The public test uses `assertMultiLineEqual`, so the return value must be a single string with exact newlines.

### 2.2 File I/O constraint (critical)

`public_test.py` patches **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

The mock serves `io.StringIO` contents for three names: `iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`.

Therefore:

- Read files with the builtin `open(...)` **inside** `grep.py` (e.g. `with open(filename) as fh:`).
- Do **not** use `pathlib.Path.read_text`, `io.open`, `Path.open`, or a pre-opened handle. Those bypass the mock and fail.
- `open(filename)` or `open(filename, "r")` is enough. Do not require encoding kwargs.
- Use a `with` block so the handle is closed.
- Iterate lines (`for line in fh`) or `fh.readlines()`. Both work with `StringIO`.

Unknown names raise in the mock; do not invent extra files. Do not catch and swallow I/O errors unless a file is missing in a way the tests never exercise. The given tests only open the three names above.

### 2.3 Flags

Parse `flags` with `flags.split()`. Treat the result as a set of tokens. Order of tokens does not matter. Unknown tokens can be ignored. Duplicates are harmless.

| Flag | Effect |
|------|--------|
| `-n` | Prefix **line number** (1-based) and `:` on each emitted **line**. Number goes after the filename when a filename is also printed. |
| `-l` | Emit **only file names** that contain at least one selected line. One `filename\n` per such file, in input-file order, at most once per file. |
| `-i` | Case-insensitive **comparison only**. Output still uses the original line / original file name. |
| `-v` | Invert selection: keep lines that **fail** the match. |
| `-x` | Match the **entire** stripped line, not a substring. |

Empty `flags` (`""`) means none of the above.

### 2.4 Filename prefix rule

Prefix matching **lines** with `filename:` **if and only if** `len(files) > 1`.

This depends on how many names were **passed**, not on how many files produced hits. Three files with a hit in only one still print `thatfile:the line\n`.

`-l` never uses the `filename:line` form. It always prints bare `filename\n`, for one file or many.

### 2.5 `-l` overrides `-n`

If both `-l` and `-n` are present, emit file names only. Do not emit line numbers or line text.

---

## 3. Architecture

Keep the module small. Recommended decomposition:

```
grep(pattern, flags, files)
    │
    ├─ parse_flags(flags) -> Options
    ├─ for filename in files:
    │     with open(filename) as fh:
    │         grep_one_file(...)
    │             │
    │             ├─ normalize each physical line (strip one trailing \n)
    │             ├─ line_selected(line, pattern, options) -> bool
    │             └─ format_and_collect
    └─ "".join(collected)
```

Three concerns, three helpers (inlined is fine if the file stays clear):

1. **Options** — booleans derived from the flag string.
2. **Match** — given one line body (no trailing newline), decide keep / drop.
3. **Format** — turn a kept line (or a kept file) into an output record.

Do not use `re`. This is literal substring / equality search.

---

## 4. Data structures

### 4.1 `Options`

A small immutable record is enough:

```python
# conceptually
Options(
    line_numbers: bool,   # -n
    filenames_only: bool, # -l
    ignore_case: bool,    # -i
    invert: bool,         # -v
    entire_line: bool,    # -x
)
```

A `tuple`, `namedtuple`, `dataclass(frozen=True)`, or five local booleans in `grep` are all acceptable. Prefer a single object so matching and formatting do not re-parse flags.

Construction:

```text
tokens = set(flags.split())
line_numbers   = "-n" in tokens
filenames_only = "-l" in tokens
ignore_case    = "-i" in tokens
invert         = "-v" in tokens
entire_line    = "-x" in tokens
```

`str.split()` with no arguments splits on any whitespace and drops extra spaces, so `"  -n   -i "` still works.

### 4.2 Per-file scan state

While scanning one file:

| Name | Type | Role |
|------|------|------|
| `line_no` | `int` | 1-based physical line index. Increment for every line, matched or not. |
| `body` | `str` | Line with at most one trailing `\n` removed. Preserve interior spaces and a trailing `\r` only if present (test data is `\n`-only). |
| `selected` | `bool` | Result of match XOR invert. |
| `file_has_hit` | `bool` | For `-l`: true once any selected line is seen. |

Collector: a `list[str]` of **complete records**, each already ending in `\n`. Final return is `"".join(records)`.

Do not mutate `pattern`. If `-i` is set, compute comparison copies (`pattern_cmp`, `line_cmp`) and leave originals for output.

### 4.3 Output records (grammar)

```
output       :=  ε  |  record+
record       :=  file_record | line_record

file_record  :=  filename  "\n"                          # only when -l

line_record  :=  prefix  body  "\n"
prefix       :=  ""                                      # 1 file, no -n
              |  number ":"                              # 1 file, -n
              |  filename ":"                            # N files, no -n
              |  filename ":" number ":"                 # N files, -n
```

`number` is `str(line_no)` with no padding.

Implement prefix as joining non-empty parts with `:`:

```text
parts = []
if not filenames_only and len(files) > 1:
    parts.append(filename)
if not filenames_only and line_numbers:
    parts.append(str(line_no))
parts.append(body)
record = ":".join(parts) + "\n"
```

When `-l`, skip that path and emit `filename + "\n"` once.

---

## 5. Algorithms

### 5.1 Line normalization

For each raw line from the file:

```text
body = line[:-1] if line.endswith("\n") else line
```

Equivalent: `line.removesuffix("\n")` (3.9+) or `line.rstrip("\n")`.

**Do not** use `str.strip()` or `rstrip()` without arguments. That would drop trailing spaces and break `-x`.

**Do not** use `str.splitlines()` without care: it also splits on `\r` / Unicode separators. The exercise files are `\n`-delimited. File iteration is the right source of “a line”.

If the last line has no newline, it is still a line. Match against its full body. When emitting, still add `\n` after the record (Unix grep prints a newline after a selected last line). Test fixtures all end with `\n`.

### 5.2 Match predicate (before invert)

Let `P` be the pattern and `B` the line body.

1. If `ignore_case`:
   - `P' = P.casefold()` (or `.lower()`; fixtures are ASCII, either is fine).
   - `B' = B.casefold()` (same method as `P`).
   - Else `P', B' = P, B`.
2. If `entire_line` (`-x`): `hit = (B' == P')`.
3. Else: `hit = (P' in B')` — literal substring, including the empty-pattern case (`"" in B'` is `True` for every line).

Never compile a regex. Characters like `. * + [ ]` in `pattern` are ordinary literals.

### 5.3 Invert (`-v`)

```text
selected = (not hit) if invert else hit
```

Invert applies to the boolean result of (substring or whole-line) comparison, **after** case folding. Combinations:

| Flags | Keep line when |
|-------|----------------|
| (none) | `P` is a substring of `B` |
| `-x` | `B == P` |
| `-i` | `P` is a substring of `B`, ignoring case |
| `-i -x` | `B` equals `P`, ignoring case |
| `-v` | `P` is **not** a substring of `B` |
| `-v -x` | `B != P` |
| `-v -i` | `P` is not a substring, ignoring case |
| `-v -i -x` | `B` is not equal to `P`, ignoring case |

### 5.4 File-name mode (`-l`)

For each file, independently:

- Scan lines with the same `selected` predicate (including `-v`, `-x`, `-i`).
- If **any** line is selected, append `filename\n` **once**.
- Then move to the next file. Do not emit line bodies or numbers.

Optimization (optional, behavior-identical): after the first selected line, stop reading that file.

A file with zero selected lines contributes nothing, even under `-l`.

`-l` together with `-n` still only prints names (`-l` wins).

### 5.5 Line-number mode (`-n`)

`line_no` is the physical index in **that file**, starting at 1 for the first line, including lines that are not selected. A later match on line 9 prints `9`, not “1st match”.

Numbers are not used when `-l` is set.

### 5.6 Multi-file walk

```text
records = []
multi = len(files) > 1
options = parse_flags(flags)
pattern_cmp = pattern.casefold() if options.ignore_case else pattern

for filename in files:
    with open(filename) as fh:
        if options.filenames_only:
            for raw in fh:
                body = strip_one_newline(raw)
                if line_selected(body, ...):
                    records.append(filename + "\n")
                    break
        else:
            for line_no, raw in enumerate(fh, start=1):
                body = strip_one_newline(raw)
                if line_selected(body, ...):
                    records.append(format_line(filename, line_no, body, multi, options))

return "".join(records)
```

Process files strictly in list order. Process lines strictly in file order. Do not sort.

### 5.7 Complexity

Let `N` be total bytes / lines across files, `M` the pattern length.

- Time: `O(N * M)` with naive `in` (CPython’s `in` is efficient; do not hand-roll search).
- Space: `O(output)` plus one line of lookahead. Reading the whole file into a list is acceptable at this scale.

No need for Aho–Corasick, Boyer–Moore, or indexing.

---

## 6. End-to-end control flow

```
grep(pattern, flags, files)
  if files is empty: return ""          # defensive; README says one or more

  options ← parse flags
  multi   ← len(files) > 1
  out     ← []

  for each filename in files:
      open filename
      if options.filenames_only:
          if exists a selected line:
              out ← filename + "\n"
          continue
      for line_no, raw_line in enumerate(file, 1):
          body ← strip trailing \n
          if selected(body):
              out ← formatted record

  return join(out)
```

---

## 7. Worked examples (must-match behavior)

Fixture lines (1-based), matching `public_test.py`:

**iliad.txt**

1. `Achilles sing, O Goddess! Peleus' son;`
2. `His wrath pernicious, who ten thousand woes`
3. `Caused to Achaia's host, sent many a soul`
4. `Illustrious into Ades premature,`
5. `And Heroes gave (so stood the will of Jove)`
6. `To dogs and to all ravening fowls a prey,`
7. `When fierce dispute had separated once`
8. `The noble Chief Achilles from the son`
9. `Of Atreus, Agamemnon, King of men.`

**midsummer-night.txt**

1. `I do entreat your grace to pardon me.`
2. `I know not by what power I am made bold,`
3. `Nor how it may concern my modesty,`
4. `In such a presence here to plead my thoughts;`
5. `But I beseech your grace that I may know`
6. `The worst that may befall me in this case,`
7. `If I refuse to wed Demetrius.`

**paradise-lost.txt**

1. `Of Mans First Disobedience, and the Fruit`
2. `Of that Forbidden Tree, whose mortal tast`
3. `Brought Death into the World, and all our woe,`
4. `With loss of Eden, till one greater Man`
5. `Restore us, and regain the blissful Seat,`
6. `Sing Heav'nly Muse, that on the secret top`
7. `Of Oreb, or of Sinai, didst inspire`
8. `That Shepherd, who first taught the chosen Seed`

### 7.1 Public test (single file, no flags)

```text
grep("Agamemnon", "", ["iliad.txt"])
→ "Of Atreus, Agamemnon, King of men.\n"
```

Substring match, original line, trailing newline, **no** `iliad.txt:` prefix because only one file was passed.

### 7.2 `-n` (single file)

```text
grep("Forbidden", "-n", ["paradise-lost.txt"])
→ "2:Of that Forbidden Tree, whose mortal tast\n"
```

### 7.3 `-i` (single file)

```text
grep("FORBIDDEN", "-i", ["paradise-lost.txt"])
→ "Of that Forbidden Tree, whose mortal tast\n"
```

Output is the original casing, not the pattern’s casing.

### 7.4 `-l` (single file)

```text
grep("Forbidden", "-l", ["paradise-lost.txt"])
→ "paradise-lost.txt\n"
```

### 7.5 `-x` (single file)

```text
grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])
→ "With loss of Eden, till one greater Man\n"
```

`grep("may", "-x", ["midsummer-night.txt"])` → `""` because `may` is only a substring.

### 7.6 Combined `-n -i -x` (single file)

```text
grep("OF ATREUS, Agamemnon, KING OF MEN.", "-n -i -x", ["iliad.txt"])
→ "9:Of Atreus, Agamemnon, King of men.\n"
```

Whole-line, case-insensitive, numbered.

### 7.7 Several substring hits (single file)

```text
grep("may", "", ["midsummer-night.txt"])
→ three lines: 3, 5, 6 of that file, each ending with \n, no numbers.

grep("may", "-n", ["midsummer-night.txt"])
→ "3:...\n5:...\n6:...\n"
```

### 7.8 `-i` several hits

```text
grep("ACHILLES", "-i", ["iliad.txt"])
→ line 1 and line 8 (original text).
```

### 7.9 `-v` (single file)

```text
grep("Of", "-v", ["paradise-lost.txt"])
```

Case-sensitive substring `"Of"`:

- Dropped: lines 1, 2, 7 (they start with `Of`).
- Kept: 3, 4, 5, 6, 8.

Line 4 (`With loss of Eden...`) contains lowercase `of`, **not** `Of`, so it is kept.

### 7.10 No matches, many flags

```text
grep("Gandalf", "-n -l -x -i", ["iliad.txt"]) → ""
```

### 7.11 `-n -l` precedence

```text
grep("ten", "-n -l", ["iliad.txt"]) → "iliad.txt\n"
```

(`ten` occurs in line 2, `thousand`.)

### 7.12 `-x -v` (single file)

```text
grep("Illustrious into Ades premature,", "-x -v", ["iliad.txt"])
```

Every iliad line except line 4, in order, no numbers.

### 7.13 Multiple files, no flags

```text
grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])
→ "iliad.txt:Of Atreus, Agamemnon, King of men.\n"
```

Filename prefix even though only one file hit.

### 7.14 Multiple files, several hits

```text
grep("may", "", [iliad, midsummer, paradise])
→ three midsummer lines, each prefixed `midsummer-night.txt:`.
```

### 7.15 Multiple files + `-n`

```text
grep("that", "-n", [all three])
→
midsummer-night.txt:5:But I beseech your grace that I may know
midsummer-night.txt:6:The worst that may befall me in this case,
paradise-lost.txt:2:Of that Forbidden Tree, whose mortal tast
paradise-lost.txt:6:Sing Heav'nly Muse, that on the secret top
```

(Each of those as `filename:N:body\n`.)

Note: `that` is case-sensitive; `That Shepherd...` does **not** match.

### 7.16 Multiple files + `-l`

```text
grep("who", "-l", [all three])
→ "iliad.txt\nparadise-lost.txt\n"
```

iliad line 2 and paradise line 8. midsummer has no `who`. Each hitting file once, in argument order.

### 7.17 Multiple files + `-v`

```text
grep("a", "-v", [all three])
```

Keep lines with **no** lowercase `a`:

- iliad 1 (`Achilles...` has `A` but no `a`)
- iliad 8 (`The noble Chief Achilles from the son`)
- midsummer 7 (`If I refuse to wed Demetrius.`)

Each prefixed with its filename.

### 7.18 Multiple files + `-x`

```text
grep("But I beseech your grace that I may know", "-x", [all three])
→ "midsummer-night.txt:But I beseech your grace that I may know\n"
```

### 7.19 Multiple files + `-n -i -x`

```text
grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", [all three])
→ "paradise-lost.txt:4:With loss of Eden, till one greater Man\n"
```

### 7.20 Multiple files, no hits

```text
grep("Frodo", "-n -l -x -i", [all three]) → ""
```

### 7.21 Multiple files + `-n -l`

```text
grep("who", "-n -l", [all three])
→ "iliad.txt\nparadise-lost.txt\n"
```

Same as `-l` alone.

### 7.22 Multiple files + `-x -v`

Every line of every file except iliad line 4, each as `filename:body\n`, files in argument order, lines in file order.

---

## 8. Edge-case handling

Implement these even if they are not in `public_test.py`. Hidden tests will use the README rules on other inputs.

| Case | Required behavior |
|------|-------------------|
| No matches | `""` |
| Empty `flags` / whitespace-only flags | No flags set (`split()` → empty) |
| Flag order | `-i -n -x` same as `-x -n -i` |
| Combined tokens | Tests pass **separate** tokens (`"-n -i"`). Do not require clustered `-nix`. Parsing via `split()` and membership of `"-n"` etc. is the specified interface. |
| Extra spaces in `flags` | `split()` already handles |
| Unknown flag token | Ignore |
| Duplicate flag | Same as once |
| `len(files) == 1` | Never `filename:` on line records |
| `len(files) > 1` but only one file hits | Still `filename:` on line records |
| `-l` and one or many files | Always bare `filename\n` |
| `-l` and `-n` | Names only |
| `-l` and `-v` | Name printed if the file has at least one **non**-matching line |
| `-l` on a file with no selected lines | Omit that file |
| Same file name twice in `files` | Search twice; `-l` may print the name twice (once per occurrence). Unlikely in tests; sequential scan is correct. |
| Pattern empty `""` | Substring: every line hits. `-x`: only empty bodies hit. Then `-v` inverts as usual. |
| Pattern with regex metacharacters | Literal; `"a.c"` does not match `"abc"` |
| Pattern appears twice on one line | One output record for that line |
| Match at start / middle / end | All count as substring hits |
| `-x` vs substring | Proper substring is **not** a whole-line hit |
| `-i` | Fold only for comparison; emit original `body` |
| Unicode case (if any) | `casefold()` is safer than `lower()`; ASCII fixtures work with either — pick one and use it on **both** sides |
| Trailing spaces on a line | Part of `body`; they matter for `-x` |
| Last line without `\n` | Still a line; output record still ends with `\n` |
| Empty file (zero lines) | No records; `-l` does not print the name |
| File that is only `\n` | One empty body `""` |
| Do not lowercase file names | Print `filename` exactly as given |
| Do not strip the pattern | `" may "` is not `"may"` |
| Return type | Always `str`, never a list of lines |
| Printing | No `print`, no `sys.stdout` |
| Regex | Do not import `re` |
| `open` | Must be the name `open` in module `grep` |

### 8.1 What not to implement

- Recursive directory search, `-r`, globs.
- Regular expressions, `-E`, `-F` as a flag (search is already fixed-string).
- Context lines (`-A -B -C`), count-only (`-c`), color, stdin (`-` or no files).
- Exit codes (this is a function, not a process).
- Binary-file handling.
- Raising custom errors for bad flags.

---

## 9. Suggested implementation sketch

This is the intended design, not a mandate on helper names.

```python
def grep(pattern, flags, files):
    options = _parse_flags(flags)
    needle = pattern.casefold() if options.ignore_case else pattern
    multi = len(files) > 1
    out = []

    for name in files:
        with open(name) as fh:
            _search_file(fh, name, needle, pattern, options, multi, out)

    return "".join(out)


def _parse_flags(flags):
    tokens = set(flags.split())
    return Options(
        line_numbers="-n" in tokens,
        filenames_only="-l" in tokens,
        ignore_case="-i" in tokens,
        invert="-v" in tokens,
        entire_line="-x" in tokens,
    )


def _selected(body, needle, ignore_case, entire_line, invert):
    hay = body.casefold() if ignore_case else body
    hit = (hay == needle) if entire_line else (needle in hay)
    return (not hit) if invert else hit


def _search_file(fh, name, needle, pattern, options, multi, out):
    # pattern is unused if needle already folded; shown for clarity
    for line_no, raw in enumerate(fh, start=1):
        body = raw.removesuffix("\n")
        if not _selected(body, needle, options.ignore_case,
                         options.entire_line, options.invert):
            continue
        if options.filenames_only:
            out.append(name + "\n")
            return
        parts = []
        if multi:
            parts.append(name)
        if options.line_numbers:
            parts.append(str(line_no))
        parts.append(body)
        out.append(":".join(parts) + "\n")
```

Notes for the implementer:

- If `ignore_case` is false, `needle` is the raw `pattern`; `hay` is the raw `body`.
- Fold **once** for the pattern outside the line loop.
- `removesuffix("\n")` only drops a single terminator; `rstrip("\n")` is equivalent here.
- Early `return` from `_search_file` is only for `-l` after the first hit.

A single-function body that does the same thing is acceptable. Clarity of the three phases (parse → match → format) matters more than the number of defs.

---

## 10. Implementation constraints

- Standard library only. No third-party packages.
- Python 3: `enumerate(..., start=1)`, `str.split`, `in`, `==`, `with open`.
- Type hints optional.
- Do not write to disk. Do not create helper modules. All logic in `grep.py`.
- Do not edit `public_test.py` or any other test file.
- Do not consult held-out tests, canonical solutions, or the network.

---

## 11. Self-check before finishing `grep.py`

Walk these mentally or with a short local harness (do not modify official tests):

1. Public test: `grep("Agamemnon", "", ["iliad.txt"])` equals exactly  
   `"Of Atreus, Agamemnon, King of men.\n"`.
2. `open` is invoked with the file name string (the mock keys off `fname`).
3. One file vs three files changes **only** the filename prefix on line records.
4. `-n` uses physical line numbers.
5. `-l` prints each hitting file once, with a trailing newline, no extra colon.
6. `-i` does not rewrite output text.
7. `-x` rejects substring-only hits.
8. `-v` keeps the complement, case-sensitively unless `-i`.
9. `-x -v` drops only exact (possibly folded) lines.
10. `-n -l` equals `-l`.
11. Zero hits → `""`.
12. No `re`, no `print`, return a `str`.

---

## 12. File to produce

Replace the stub in `grep.py`:

```python
def grep(pattern, flags, files):
    pass
```

with the implementation described above. Keep the public function name `grep` unchanged so `from grep import grep` continues to work.
