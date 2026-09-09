# Implementation Guide: `grep.py`

This document is the complete implementation plan for `grep.py`. Implement only `grep.py`. Do not edit tests or this plan while coding.

Source of truth for this plan:

- `README.md` — product behavior
- `public_test.py` — call signature, file I/O contract, output shape
- `grep.py` — stub: `def grep(pattern, flags, files):`

Hidden tests (not in this workspace) are expected to cover the rest of the Exercism *grep* exercise: every flag, flag combinations, one vs many files, zero matches, and inverted / whole-line matching. Design for that full surface, not only the single public test.

---

## 1. Problem summary

Implement a simplified Unix `grep` that searches for a **fixed string** (not a regular expression) in one or more files and returns matching lines as a single string.

Function:

```python
def grep(pattern, flags, files) -> str:
```

Arguments:

| Arg | Type | Meaning |
|-----|------|---------|
| `pattern` | `str` | Literal search string. May be empty. |
| `flags` | `str` | Space-separated flag tokens, e.g. `""`, `"-n"`, `"-i -x"`, `"-n -l -i"`. |
| `files` | `list[str]` | File names, in search order. One or more. |

Return: a single `str` of formatted result lines, each ending in `\n`. Return `""` when there are no results.

---

## 2. Non-negotiable I/O contract

`public_test.py` patches **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

and serves file contents from an in-memory map via `io.StringIO`.

Therefore:

1. Read files with the builtin **`open(filename)`** (or `open(filename, "r")`) **inside** `grep.py`, so the name `open` resolves as a global of the `grep` module.
2. Do **not** use `pathlib`, `io.open`, `Path.read_text()`, `os.read`, or a locally imported `open`. Those bypass the mock and fail.
3. Use a context manager: `with open(filename) as fh:`.
4. Iterate lines with `for line_no, line in enumerate(fh, start=1):`. File iteration keeps the line's trailing newline when present.
5. Process files **in the order given** in `files`. Do not sort.
6. Do not catch `FileNotFoundError` / `KeyError` from `open`. Missing names are a test error, not a grep feature.
7. Do not write to disk. Do not look at `__pycache__`, held-out tests, or the network.

---

## 3. Architecture

Keep the module to one public function plus small private helpers. Suggested layout:

```
grep(pattern, flags, files)
  └─ parse_flags(flags) -> FlagSet
  └─ for each filename in files:
        with open(filename) as fh:
          for each (line_no, raw_line):
            if line_matches(raw_line, pattern, flagset):
              emit formatted result
              if filenames_only: stop this file
  └─ return "".join(results)
```

Helpers (names are suggestions; behavior is required):

| Helper | Role |
|--------|------|
| `parse_flags(flags: str)` | Tokenize the flags string into booleans. |
| `normalize_for_match(text: str, ignore_case: bool)` | Strip the line delimiter; optionally case-fold. |
| `line_matches(raw_line, pattern, flagset) -> bool` | Apply `-i`, `-x`, then `-v`. |
| `format_match(...)` | Build one output record (`-l` / `-n` / multi-file prefix). |

Do not introduce classes unless you want a tiny `FlagSet` (`dataclass` or `NamedTuple`) to pass five booleans cleanly. A `dict` or five locals is equally fine.

No regex engine. Matching is literal substring / equality.

---

## 4. Data structures

### 4.1 Flag set

After parsing, five independent booleans:

```text
line_numbers     # -n
filenames_only   # -l
ignore_case      # -i
invert           # -v
entire_line      # -x
```

Parsing algorithm:

1. `tokens = flags.split()`  
   `split()` with no args treats any whitespace as separator and ignores extra spaces. `""` yields `[]`.
2. Membership: `"-n" in tokens`, etc.
3. Unknown tokens: ignore (hidden tests should only send the five flags).
4. Duplicate flags: harmless; treat as present.

Optional extra (not required by README, but cheap): if a token looks like clustered shorts (e.g. `"-inx"`), treat each letter after the dash as a flag. **Do not** require this unless you want belt-and-suspenders. Canonical Python-track tests pass space-separated flags like `"-n -i"`.

Do **not** parse with naive `" -n" in flags` without padding; it is easy to get wrong. `split()` membership is the robust approach.

### 4.2 Per-line working values

For each physical file line:

| Name | Definition |
|------|------------|
| `raw_line` | Exactly what file iteration yields. May or may not end with `\n`. |
| `body` | `raw_line.removesuffix("\n")` (Python 3.9+) or `raw_line[:-1] if raw_line.endswith("\n") else raw_line`. **Do not** use `rstrip()` / `strip()` — that would drop trailing spaces, which are part of the line for `-x`. Only strip a single trailing `\n`. Do not strip `\r` unless you also want to treat `\r\n`; the provided fixtures are `\n`-only. |
| `line_no` | 1-based index of this physical line in the current file. Count every line, matched or not. |
| `filename` | The name as given in `files` (e.g. `"iliad.txt"`). |

### 4.3 Output accumulator

A `list[str]` of already-formatted records (each including a trailing `\n`). Join once at the end. Do not build with repeated `+=` on a giant string in a tight loop (fine for these files, but list-then-join is the intended shape).

For `-l`, each record is exactly `filename + "\n"`, and a given file appears **at most once**.

---

## 5. Matching algorithm (fixed string)

Let `P` be the pattern, `B` the line body (no trailing `\n`).

### 5.1 Case folding (`-i`)

If `ignore_case`:

- Compare using `P.lower()` and `B.lower()`.
- ASCII-only fixtures (`Agamemnon`, `Forbidden`, etc.). `casefold()` is also acceptable; pick one and use it on **both** sides.

Folding is **only** for comparison. Output always uses the original `raw_line` / `body` (original case and spacing).

### 5.2 Whole line vs substring (`-x`)

After optional folding:

- **Without `-x`:** match iff `P` is a contiguous substring of `B` (`P in B`).
- **With `-x`:** match iff `P == B` (exact, including internal and trailing spaces).

Empty pattern:

- Without `-x`: `"" in B` is true for every line, including empty lines. Every line matches.
- With `-x`: only lines whose body is `""` match (blank lines).

This is fixed-string search. Characters that are regex metacharacters in `P` are literal. Do **not** call `re.search` on the raw pattern.

### 5.3 Inversion (`-v`)

Compute `matched` from the rules above, then:

```text
if invert:
    matched = not matched
```

`-v` inverts the **boolean**, not the meaning of other flags. Combinations:

| Flags | A line is selected when |
|-------|-------------------------|
| (none) | body contains pattern |
| `-x` | body equals pattern |
| `-i` | folded body contains folded pattern |
| `-i -x` | folded body equals folded pattern |
| `-v` | body does **not** contain pattern |
| `-v -x` | body is **not** equal to pattern |
| `-v -i` | folded body does not contain folded pattern |
| `-v -i -x` | folded body is not equal to folded pattern |

Empty files: no lines, so nothing is selected (even with `-v`). `-v` does not invent a match for “the file as a whole.”

### 5.4 `-l` and matching

`-l` does not change *which* lines match. It changes *what is printed* and *when to stop scanning a file*:

- If at least one selected line exists in the file, emit the filename once.
- After the first selected line, `break` to the next file (correctness-preserving optimization).

With `-l -v`, list files that have **at least one non-matching line**.

---

## 6. Output formatting

Build one output record per selected line (or per selected file for `-l`).

Let `multi = len(files) > 1`.

Always terminate a record with `\n`. If `raw_line` already ends with `\n`, use that newline; if the last line of a file has no newline, **append** `\n` in the output. Hidden tests and POSIX-style grep expect every result record to be a complete line.

### 6.1 Precedence

1. If `filenames_only` (`-l`): output `{filename}\n` and nothing else. **Ignore** `-n` and the usual line-text / multi-file colon rules. Still search every file; print a name only when that file has a match.
2. Else assemble a prefix, then the original line body + `\n`.

### 6.2 Prefix (when not `-l`)

Pieces, in order, joined with `:`:

| Condition | Append to prefix |
|-----------|------------------|
| `len(files) > 1` | `filename` |
| `-n` | `str(line_no)` (decimal, no padding, 1-based) |

Then:

- If prefix is non-empty: `prefix + ":" + body + "\n"`
- If prefix is empty (single file, no `-n`): `body + "\n"`

Worked examples (body shown without writing the actual Iliad text):

| Situation | Record shape |
|-----------|----------------|
| 1 file, no flags | `Of Atreus, Agamemnon, King of men.\n` |
| 1 file, `-n`, line 9 | `9:Of Atreus, Agamemnon, King of men.\n` |
| 2+ files, no flags | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| 2+ files, `-n`, line 9 | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |
| any files, `-l` | `iliad.txt\n` |
| `-l -n` together | still `iliad.txt\n` (no line number) |
| 1 file, `-l` | `iliad.txt\n` (filename even for a single file) |

Colon placement: filename (if any), then line number (if any), then the **original** line. There is a colon **between** prefix parts and **between** the prefix and the line text. There is **no** extra space around colons.

### 6.3 Order

- Files: given order.
- Lines within a file: file order.
- `-l`: matching files in given order, each once.

Several matches in one file (without `-l`): several records, in the order those lines appear.

### 6.4 No-match result

Return `""` (not `"\n"`, not `None`).

---

## 7. Reference walk-through (public fixture)

`public_test.py` defines `iliad.txt` (9 lines). Pattern `"Agamemnon"`, flags `""`, files `["iliad.txt"]`.

- Single file → no filename prefix.
- No `-n` → no line numbers.
- Line 9 body contains `Agamemnon`.
- Expected: `"Of Atreus, Agamemnon, King of men.\n"`

Same search with extra files (e.g. `["iliad.txt", "midsummer-night.txt"]`) would prefix `iliad.txt:`.

Same search with `-n` on one file would be `"9:Of Atreus, Agamemnon, King of men.\n"`.

Useful other lines in the fixtures (for a local mental checklist, not extra files):

- `paradise-lost.txt` line 1: `Of Mans First Disobedience, and the Fruit` — substring `of` matches with `-i`, not without.
- `Forbidden` appears in `paradise-lost.txt`.
- `the` appears in multiple files and multiple lines — exercises multi-file prefixes and several matches.

---

## 8. Edge cases (must handle)

| Case | Required behavior |
|------|-------------------|
| Empty flags string | All flag booleans false. |
| Extra spaces in flags | `split()` absorbs them. |
| Flag order | Irrelevant; all combinations commute except output precedence of `-l` over `-n`. |
| `-l` and `-n` together | `-l` wins. |
| `-l` and `-v` together | Files with ≥1 inverted-match line. |
| `-l` and `-x` / `-i` | Same match rules; output still filenames. |
| Pattern longer than the line | No substring match; `-x` fails unless equal. |
| Pattern equals the full line | Matches with and without `-x`. |
| Pattern is a proper prefix/suffix of the line | Matches without `-x`; fails with `-x`. |
| Empty pattern `""` | Every line matches (substring); with `-x`, only empty bodies. |
| Empty file | No lines emitted; with `-l`, file is not listed. |
| Last line without `\n` | Match on body; still emit a trailing `\n` in the result. |
| Trailing spaces on a line | Part of the body. `-x` requires they be in the pattern too. |
| Multiple files, match in only some | Prefix those lines; skip silent files (unless `-l` only prints matching files). |
| Multiple files, no matches at all | `""`. |
| Same file name listed twice | Search twice; emit twice if it matches (do not uniquify `files` unless `-l` within a single open — still process each list entry independently). Hidden tests likely pass unique names; still do not dedupe the input list. |
| Case-only difference | Matches only with `-i`. Output original case. |
| Literal `.`, `*`, `[`, `\` in pattern | Ordinary characters. |
| Do not trim leading/trailing spaces from pattern | `" Foo "` is not `"Foo"`. |
| Line numbers | Always physical 1-based index, including for `-v` (numbers refer to the file, not “nth match”). |
| Unicode | Not in fixtures; `lower()` is enough. |

---

## 9. Suggested implementation (pseudocode)

```python
def parse_flags(flags):
    tokens = flags.split()
    return {
        "n": "-n" in tokens,
        "l": "-l" in tokens,
        "i": "-i" in tokens,
        "v": "-v" in tokens,
        "x": "-x" in tokens,
    }


def body_of(raw_line):
    if raw_line.endswith("\n"):
        return raw_line[:-1]
    return raw_line


def matches(raw_line, pattern, f):
    body = body_of(raw_line)
    p, b = pattern, body
    if f["i"]:
        p, b = p.lower(), b.lower()
    hit = (b == p) if f["x"] else (p in b)
    return (not hit) if f["v"] else hit


def grep(pattern, flags, files):
    f = parse_flags(flags)
    multi = len(files) > 1
    out = []
    for name in files:
        with open(name) as fh:
            for lineno, raw in enumerate(fh, start=1):
                if not matches(raw, pattern, f):
                    continue
                if f["l"]:
                    out.append(name + "\n")
                    break
                body = body_of(raw)
                prefix_parts = []
                if multi:
                    prefix_parts.append(name)
                if f["n"]:
                    prefix_parts.append(str(lineno))
                if prefix_parts:
                    out.append(":".join(prefix_parts) + ":" + body + "\n")
                else:
                    out.append(body + "\n")
    return "".join(out)
```

This is complete. Translate it into `grep.py` with whatever naming you prefer. Do not add CLI `sys.argv` wrapping; tests import `grep` directly.

---

## 10. Implementation steps (for the implementer)

1. Replace `pass` with `parse_flags` + empty-result path so `grep("Agamemnon", "", ["iliad.txt"])` can run.
2. Implement file loop using `open`, substring match, collect original lines. Confirm the public test:
   `grep("Agamemnon", "", ["iliad.txt"]) == "Of Atreus, Agamemnon, King of men.\n"`.
3. Add `-i`, `-x`, `-v` in `matches` (boolean pipeline: fold → compare → invert).
4. Add output prefixes: multi-file filename, then `-n` line numbers.
5. Add `-l` short-circuit and filename-only records; ensure `-l` suppresses `-n` and line text.
6. Normalize output newlines via `body_of` + always `"\n"`.
7. Mentally (or with a **temporary** helper only in the CWD, never committed as a test file the runner might collect) check combinations:
   - one file / many files
   - each flag alone
   - `-n -i`, `-x -v`, `-l -v`, `-l -n`, `-i -x`
   - zero matches
   - several matches in one file
8. Delete any scratch helpers. Leave `grep.py` as the only product change.

---

## 11. Testing notes (do not edit `public_test.py`)

The public file contains a single assertion. Hidden tests typically include (names from the standard exercise, for awareness):

- One file, several matches, no flags
- One file, `-n`
- One file, no matches
- One file, `-x` (match and miss)
- One file, `-i`
- One file, `-v` and `-x -v`
- One file, `-l`
- Several files, one or several matches, with and without `-n`
- Several files, `-i`, `-x`, `-v`
- Several files, `-l` (and `-l` with `-i`)
- Several files, no matches

Match **strings exactly**, including the final newline on each record. `assertMultiLineEqual` is newline-sensitive.

Do not add `unittest` modules in the workspace root named `test_*.py` if that might confuse a runner; keep experiments under a clearly throwaway name only if needed, and prefer not adding them.

---

## 12. Constraints and anti-patterns

- **No regex matching** of the user pattern (`re.search(pattern, ...)` is wrong unless the pattern is `re.escape`d *and* you still honor `-x` as fullmatch). Prefer `in` and `==`.
- **No** `fnmatch` / glob on file names.
- **No** default `strip()` on lines or pattern.
- **No** 0-based line numbers.
- **No** space after colons (`iliad.txt:9:text`, not `iliad.txt: 9: text`).
- **No** filename prefix on single-file searches except for `-l`.
- **No** reading stdin; files are always provided.
- **No** modification of `public_test.py` or of files outside this directory.

---

## 13. Acceptance checklist

- [ ] `grep(pattern, flags, files)` exists and returns `str`
- [ ] Uses `open(...)` in this module (mockable)
- [ ] Fixed-string match; `-i` / `-x` / `-v` composed as specified
- [ ] `-n` prefixes 1-based numbers
- [ ] Multi-file non-`-l` output is `file:…`
- [ ] Combined multi-file + `-n` is `file:N:…`
- [ ] `-l` prints each matching file once as `file\n`
- [ ] `-l` overrides `-n` and line text
- [ ] Empty result is `""`
- [ ] Public test passes
- [ ] `grep.py` is the only implementation file that needs to ship
