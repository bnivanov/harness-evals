# Implementation Guide: `grep.py`

## Goal

Implement `grep(pattern, flags, files)` so it searches one or more text files for a **fixed string** (not a regular expression) and returns a single string of matching lines.

This is a simplified Unix `grep`. Behavior is defined by `README.md` and by the public test in `public_test.py`. Hidden tests are expected to cover the rest of the usual Exercism `grep` suite (flag combinations, multiple files, no-match cases) using the same three fixture files and the same `grep.open` mock.

**Do not** treat the pattern as a regex. Characters such as `.` `*` `[` must match literally.

---

## Function contract

```python
def grep(pattern, flags, files):
    """Return a string of matching lines (each ending in '\\n')."""
```

| Argument | Type | Meaning |
|---|---|---|
| `pattern` | `str` | Fixed search string. May be empty. |
| `flags` | `str` | Space-separated flag tokens, e.g. `""`, `"-n"`, `"-n -i"`, `"-x -i -n"`. |
| `files` | `list[str]` | File names to search, **in the given order**. One or more in normal use. |

**Return value:** `str`, never `None`. Concatenate every output record. Each record ends with `\n`. No matches → `""`.

**Do not print.** The caller asserts on the returned string.

**Do not mutate** `files` or the contents of opened files.

---

## Supported flags

Parse `flags` by splitting on whitespace into a set of tokens. Unknown tokens should be ignored (none are expected). Order of flags does not matter. Duplicates are harmless.

| Flag | Meaning |
|---|---|
| `-n` | Prefix each **content** line with its 1-based line number and `:`. Number goes **after** the filename prefix when a filename is shown. |
| `-l` | List **file names only** (one name per line, with `\n`). A file is listed if it has **at least one** matching line after `-i`/`-x`/`-v` are applied. Stop reading that file after the first match. `-n` has no effect when `-l` is set. |
| `-i` | Case-insensitive match (`str.casefold()` or `.lower()` on both pattern and line). Fixture text is ASCII; either is fine. |
| `-v` | Invert: keep lines that **fail** the match. Combined with `-l`, list files that have at least one non-matching line. |
| `-x` | Whole-line match: the line (without its terminator) must equal the pattern. Without `-x`, the pattern is a **substring**. |

Empty `flags` (`""`) means all of the above are off.

Suggested parse:

```python
tokens = set(flags.split())  # "".split() == []
want_line_numbers = "-n" in tokens
list_names_only   = "-l" in tokens
ignore_case       = "-i" in tokens
invert            = "-v" in tokens
whole_line        = "-x" in tokens
```

Do **not** require flags to be packed (`-ni`) unless you also accept space-separated form. Tests pass space-separated strings.

---

## File I/O (mock-critical)

`public_test.py` patches **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

Therefore `grep.py` **must** call the builtin name `open(...)` from inside the `grep` module (e.g. `with open(filename) as fh:`).

**Do not** use:

- `io.open`, `builtins.open`, `pathlib.Path.read_text`, `Path.open`
- `from io import open`
- pre-reading files at import time

Text mode is correct (default). Do not pass a binary mode. The mock ignores extra `open` args but still returns `io.StringIO` of the fixture text.

Read files **sequentially in `files` order**. For each file, process lines top to bottom.

### Line iteration

Prefer iterating the file object so each yielded string keeps its terminator:

```python
with open(filename) as fh:
    for line_no, raw in enumerate(fh, start=1):
        ...
```

- Line numbers are **1-based** and count **every** physical line, including non-matches. `-v` still reports the original numbers.
- Matching uses the line **without** the trailing newline. A trailing `\n` (and, defensively, `\r`) is **not** part of the line text for `-x` equality or substring search.
- Output of a content line should be the original line text **including** its newline. If a file’s last line has no terminator, append `\n` when emitting so records do not glue together. Fixture files all end with `\n`.

Equivalent approach: `fh.read().splitlines(keepends=True)` and then strip the terminator only for matching.

**Do not** use `str.split("\n")` without handling the empty trailing piece after a final newline. That would invent a bogus empty last line and throw off `-x` / `-v` / `-n`.

---

## Matching algorithm

Work on `text = raw.rstrip("\n")` (optionally also rstrip `"\r"`).

1. Prepare needles/haystacks for case:
   - If `-i`: compare `text.casefold()` with `pattern.casefold()` (or `.lower()`).
   - Else: compare `text` with `pattern` as-is.
2. Raw hit:
   - If `-x`: `haystack == needle`
   - Else: `needle in haystack`  (empty `pattern` is a substring of every line, including `""`)
3. Selected:
   - If `-v`: keep when **not** raw hit
   - Else: keep when raw hit

No regex, no `fnmatch`, no collapsing whitespace. Spaces and punctuation in the pattern are literal.

Whole-line match is **not** “pattern is the only word”; it is exact equality of the full line body.

---

## Output formatting

Let `multi = len(files) > 1`. Filename prefixes depend on how many paths were **passed**, not on how many produced hits.

### `-l` (names only)

For each file that has ≥ 1 selected line, emit exactly:

```
{filename}\n
```

No line text, no line numbers, no extra colon. Single-file searches still print the name (`iliad.txt\n`), because `-l` means “print names”.

Once a file is known to qualify, do not emit it again.

### Content lines (no `-l`)

Each selected line becomes:

```
{file_prefix}{number_prefix}{line_body_with_newline}
```

| Condition | `file_prefix` | `number_prefix` |
|---|---|---|
| 1 file, no `-n` | `""` | `""` |
| 1 file, `-n` | `""` | `"{n}:"` |
| 2+ files, no `-n` | `"{filename}:"` | `""` |
| 2+ files, `-n` | `"{filename}:"` | `"{n}:"` |

Examples (from the fixture `iliad.txt`, line 9):

- `grep("Agamemnon", "", ["iliad.txt"])` → `Of Atreus, Agamemnon, King of men.\n`
- `grep("Agamemnon", "-n", ["iliad.txt"])` → `9:Of Atreus, Agamemnon, King of men.\n`
- `grep("Agamemnon", "", ["iliad.txt", "paradise-lost.txt"])` → `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
- `grep("Agamemnon", "-n", ["iliad.txt", "paradise-lost.txt"])` → `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n`

Join records in encounter order: files as given, then line order within each file.

---

## Recommended architecture

Keep `grep.py` small and side-effect-free besides `open`.

```
grep(pattern, flags, files)
  ├─ parse flags → frozenset / booleans
  ├─ for filename in files:
  │     search_file(...) → selected (line_no, raw_line)*
  │     if list_names_only:
  │         if any selected: append "name\n"
  │     else:
  │         for each selected: append format(...)
  └─ return "".join(chunks)
```

Suggested helpers (names optional):

| Helper | Role |
|---|---|
| `_parse_flags(flags) -> set[str]` | Tokenize |
| `_matches(text, pattern, ignore_case, whole_line) -> bool` | Raw hit |
| `_selected(text, pattern, opts) -> bool` | Raw hit XOR invert |
| `_format_line(filename, line_no, raw, opts, multi) -> str` | Prefixes + line |

A single function with nested loops is also acceptable if it stays readable.

**Early exit:** when `-l` and a file already has a selected line, `break` that file’s loop.

---

## Data structures

| Data | Representation |
|---|---|
| Flag set | `set[str]` of tokens like `"-n"` |
| Accumulator | `list[str]` of complete output records, then `"".join` |
| Per-line | `(line_no: int, raw: str)` only if you collect before formatting; streaming into the accumulator is better |
| Match haystack | `str` with terminator stripped |

No classes required. No extra modules besides the standard library (none are needed).

---

## Control-flow sketch

```text
function grep(pattern, flags, files) -> str:
    opts = parse(flags)
    multi = len(files) > 1
    out = []

    for name in files:
        with open(name) as fh:
            for line_no, raw in enumerate(fh, start=1):
                text = raw.rstrip("\n")
                if not selected(text, pattern, opts):
                    continue
                if opts.list_names_only:
                    out.append(name + "\n")
                    break
                line_out = raw if raw.endswith("\n") else raw + "\n"
                prefix = ""
                if multi:
                    prefix += name + ":"
                if opts.line_numbers:
                    prefix += str(line_no) + ":"
                out.append(prefix + line_out)

    return "".join(out)
```

---

## Fixture files (for reasoning about tests)

`public_test.py` defines three in-memory files. Hidden tests reuse them.

**`iliad.txt`** (9 lines):

```
1 Achilles sing, O Goddess! Peleus' son;
2 His wrath pernicious, who ten thousand woes
3 Caused to Achaia's host, sent many a soul
4 Illustrious into Ades premature,
5 And Heroes gave (so stood the will of Jove)
6 To dogs and to all ravening fowls a prey,
7 When fierce dispute had separated once
8 The noble Chief Achilles from the son
9 Of Atreus, Agamemnon, King of men.
```

**`midsummer-night.txt`** (7 lines):

```
1 I do entreat your grace to pardon me.
2 I know not by what power I am made bold,
3 Nor how it may concern my modesty,
4 In such a presence here to plead my thoughts;
5 But I beseech your grace that I may know
6 The worst that may befall me in this case,
7 If I refuse to wed Demetrius.
```

**`paradise-lost.txt`** (8 lines):

```
1 Of Mans First Disobedience, and the Fruit
2 Of that Forbidden Tree, whose mortal tast
3 Brought Death into the World, and all our woe,
4 With loss of Eden, till one greater Man
5 Restore us, and regain the blissful Seat,
6 Sing Heav'nly Muse, that on the secret top
7 Of Oreb, or of Sinai, didst inspire
8 That Shepherd, who first taught the chosen Seed
```

Public test: `grep("Agamemnon", "", ["iliad.txt"])` → `Of Atreus, Agamemnon, King of men.\n`

---

## Expected behaviors hidden tests will likely cover

Use these as acceptance criteria while implementing. Do not add test files; this is a checklist.

### Single file

| Scenario | Pattern / flags | Notes |
|---|---|---|
| One substring hit | `Agamemnon`, no flags | Line 9 of iliad, no prefix |
| `-n` | `Forbidden`, `-n`, paradise-lost | `2:Of that Forbidden Tree, whose mortal tast\n` |
| `-i` | `FORBIDDEN`, `-i` | Same line, no number |
| `-l` | `Forbidden`, `-l` | `paradise-lost.txt\n` |
| `-x` hit | full line `With loss of Eden, till one greater Man` | That one line |
| `-x` miss | substring `may` with `-x` on midsummer-night | `""` (three substring hits, zero whole-line hits) |
| Combined `-n -i -x` | `OF ATREUS, AGAMEMNON, KING OF MEN.` on iliad | `9:Of Atreus, Agamemnon, King of men.\n` |
| Several hits | `may` on midsummer-night | Lines 3, 5, 6, in order, each with `\n` |
| Several hits + `-n` | same | `3:...`, `5:...`, `6:...` |
| Several hits + `-i` | `ACHILLES` on iliad | Lines 1 and 8 |
| `-v` | `Of` on paradise-lost | Every line that does **not** contain `Of` |
| No hits | `Gargantua` with any flags | `""` |
| `-l` beats `-n` | `-n -l` | Only `iliad.txt\n` (or whichever file), never `n:name` |

### Multiple files (always filename prefix on content lines)

Search `["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"]` in that order.

| Scenario | Notes |
|---|---|
| One hit | `Agamemnon` → `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| Several hits | `may` → three `midsummer-night.txt:...` lines |
| `-n` | `midsummer-night.txt:3:...` etc. |
| `-l` + `who` | `iliad.txt\nparadise-lost.txt\n` (both contain `who`; midsummer-night does not) |
| `-i` + `TO` | Every line containing `to`/`To`/`TO`, prefixed by filename, file order preserved |
| `-v` | Lines **not** containing the needle, still prefixed |
| `-x` | Full-line match in one file: `midsummer-night.txt:But I beseech your grace that I may know\n` |
| `-n -i -x` | `paradise-lost.txt:4:With loss of Eden, till one greater Man\n` |
| No hits | `Frodo` → `""` |
| `-l` + `-n` | Names only, still no numbers |

---

## Edge-case handling

| Case | Required behavior |
|---|---|
| No matches | Return `""` |
| Empty `files` | Return `""` (nothing to open) |
| Empty `pattern` | Substring of every line → all lines (or none if `-v`; only empty lines if `-x`) |
| Empty line in file | Matches empty pattern; matches `-x` only if pattern is `""`; `-v` excludes it when the pattern is empty |
| Pattern with regex metacharacters | Literal; `in` / `==` only |
| Pattern with spaces / punctuation | Literal, including trailing spaces if present |
| Flags with extra spaces | `str.split()` collapses them |
| Flag order | Irrelevant |
| `-l` + `-v` | File listed iff some line **fails** the (possibly `-i`/`-x`) match. An empty file has no selected lines → not listed. A file whose **every** line matches is not listed under `-v`. |
| `-l` + `-x` / `-i` | Apply those to decide “has a match”, then print the name |
| `-n` + `-v` | Numbers are original file line numbers of the **kept** lines |
| One file vs many | Filename prefix iff `len(files) > 1` **and** not `-l` |
| Same file named twice | Process twice (search and emit again) |
| Last line without `\n` | Match on body; emit with a trailing `\n` |
| Leading/trailing whitespace on a line | Significant for `-x` and for substring |
| Case folding | Only with `-i`; without `-i`, `Agamemnon` does not match `AGAMEMNON` |
| Non-existent file | Production Unix grep would error; tests only open fixture names. Do not invent a custom error format; let `open` raise if it happens |
| Binary / encoding | Out of scope; fixtures are ASCII text |

---

## Pitfalls to avoid

1. **Using `re` without escaping** — will fail on `.` and similar. Do not use `re` at all.
2. **Comparing with the trailing `\n` still attached under `-x`** — whole-line matches would all fail.
3. **Forgetting `\n` on returned lines** — `assertMultiLineEqual` requires them.
4. **Putting the number before the filename** — must be `file:n:line`, not `n:file:line`.
5. **Prefixing the filename for a single-file content search** — only when `len(files) > 1` or when `-l`.
6. **Applying `-n` under `-l`** — names only.
7. **Calling something other than `open`** — mock will not intercept; tests fail with `RuntimeError` or unmocked FS access.
8. **`split("\n")` creating a phantom empty last line** — breaks counts and `-v`/`-x`.
9. **Returning a list** — must be one string.
10. **Lowercasing the output** — `-i` affects matching only; emit original line text.
11. **Stopping after the first match** except for `-l`.
12. **Sorting files or lines** — preserve input order.

---

## Public test (must pass)

```python
grep("Agamemnon", "", ["iliad.txt"])
# == "Of Atreus, Agamemnon, King of men.\n"
```

`open("iliad.txt")` is mocked to the fixture string. Implementation must go through `open`.

---

## Implementation constraints

- Edit **`grep.py` only** when implementing. Do not change tests.
- Stay inside the workspace.
- No third-party packages.
- No network.
- Keep the public function name `grep`.
- A complete solution is typically ~40–80 lines.

---

## Suggested implementation order

1. Parse flags; read each file via `open`; substring match; return joined matching lines (no prefixes). Confirm the public test.
2. Add terminator-stripping for matching; emit original text with `\n`.
3. Add `-i`, `-x`, `-v` on the match boolean.
4. Add `-n` and multi-file filename prefixes.
5. Add `-l` with early `break`, taking precedence over `-n` and over line text.
6. Mentally walk the checklist above (especially `-x` vs substring, `-l` with multiple files, inverted empty files, `file:n:line` order).
