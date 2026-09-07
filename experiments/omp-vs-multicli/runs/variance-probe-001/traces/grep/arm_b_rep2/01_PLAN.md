# Implementation Guide: `grep.py`

## 1. Problem

Implement a simplified Unix `grep` that searches **fixed strings** (not regular expressions) in one or more files and returns matching lines as a single string.

Public entry point (already stubbed):

```python
def grep(pattern, flags, files):
    ...
```

| Argument  | Type        | Meaning |
|-----------|-------------|---------|
| `pattern` | `str`       | Literal search string. |
| `flags`   | `str`       | Space-separated flag tokens, or `""` for none. Examples: `""`, `"-n"`, `"-n -i -x"`. |
| `files`   | `list[str]` | File names to search, in order. One or more. |

**Return value:** one `str`. Every emitted record ends with `\n`. No matches → `""` (not `"\n"`).

This matches the Exercism `grep` contract used by `public_test.py` (generated from problem-specifications). Held-out tests cover the rest of that suite: all five flags, combinations, single-file vs multi-file formatting, several matches, inverted matches, and empty result sets.

---

## 2. Non-negotiable test harness constraints

`public_test.py` patches **`grep.open`** (`create=True`) and feeds an in-memory `io.StringIO` per known file name.

1. **Read files only with the builtin `open(...)`** inside `grep.py`. That name lookup is what the mock intercepts.
2. **Do not** use `pathlib`, `io.open`, `__builtins__['open']`, or pre-read file contents some other way.
3. Extra `open` arguments (`mode`, `encoding`) are acceptable; the mock is `*args, **kwargs`.
4. Unknown file names raise `RuntimeError` from the mock. Do not add missing-file handling.
5. The three fixture files (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`) all use `\n` and end with a trailing newline.

Call `open` once per name in `files`, in list order. If the same name appeared twice, it would be searched twice.

---

## 3. Architecture

Keep the module as a thin pipeline. Four responsibilities, four functions (plus the public `grep`):

```
grep(pattern, flags, files)
  │
  ├─ parse_flags(flags) → Options
  ├─ matches(line, pattern, options) → bool
  ├─ format_hit(filename, lineno, line, options, multi_file) → str
  └─ search_file(filename, pattern, options, multi_file) → list[str]
```

`grep` concatenates per-file result lists and `"".join`s them.

No classes are required. A small `Options` structure (see §4) is enough. Do **not** use the `re` module for matching: the search string is a literal. Apostrophes, commas, and other punctuation in the fixtures must match as ordinary characters. `pattern in line` / `line == pattern` is the whole matcher.

---

## 4. Data structures

### 4.1 `Options`

Parse flags once. A `set` of tokens is fine; a tiny dataclass/namedtuple is clearer:

```text
Options
  line_numbers: bool      # -n
  filenames_only: bool    # -l
  ignore_case: bool       # -i
  invert: bool            # -v
  exact_line: bool        # -x
```

Parsing:

```python
tokens = set(flags.split())   # "" → empty set; extra spaces ignored
```

Unknown tokens: ignore. Tests only send the five documented flags.

Do **not** treat a clustered blob like `"-nix"` as three flags unless you also accept space-separated forms. The Python track always passes **space-separated** tokens (`"-n -i -x"`). Implement `flags.split()` membership checks (`"-n" in tokens`). That is sufficient.

### 4.2 Per-line working values

For each physical line:

| Field     | Rule |
|-----------|------|
| `lineno`  | 1-based index of the line in the file (every line, matching or not). |
| `line`    | Line text **without** the trailing newline. Do **not** strip other whitespace. |
| `hit`     | `matches(line, pattern, options) != options.invert` |

Output always uses the original `line` (original case, original spacing), never a lowercased copy.

### 4.3 Result accumulation

Use a `list[str]` of already-formatted records (each including its terminating `\n`). Return `"".join(results)`.

---

## 5. Algorithms

### 5.1 Reading lines

```python
with open(filename) as fh:
    for lineno, raw in enumerate(fh, start=1):
        line = raw.rstrip("\n")
        ...
```

Why this and not `split("\n")`:

| Input        | `split("\n")`     | file iteration + `rstrip("\n")` / `splitlines()` |
|--------------|-------------------|--------------------------------------------------|
| `"a\nb\n"`   | `['a','b','']`    | `['a','b']`                                      |
| `"a\nb"`     | `['a','b']`       | `['a','b']`                                      |
| `""`         | `['']`            | `[]`                                             |
| `"\n"`       | `['','']`         | `['']`                                           |

The fixtures end with `\n`. `split("\n")` would invent a phantom empty last line and shift `-n` numbers / `-x` results. **Do not split on `"\n"`.**

`str.splitlines()` is also correct for these fixtures. If you use it, number lines with `enumerate(..., start=1)` on that list.

Only strip the line terminator. `str.rstrip()` with no arguments would drop trailing spaces and break exact-line matching. Prefer `rstrip("\n")` (fixtures are `\n`-only).

### 5.2 Matching (fixed string)

Let `needle` / `haystack` be `pattern` / `line`, or both `.lower()` when `-i` is set. ASCII `.lower()` is enough for the fixtures.

```text
if exact_line:   # -x
    raw_match = haystack == needle
else:
    raw_match = needle in haystack   # unanchored substring, not whole-word
```

Then apply invert:

```text
selected = raw_match != invert    # -v flips inclusion
```

Consequences the tests rely on:

- Substring, not token: `"to" in "into"` and `"to" in "top"` are true. `-i` + pattern `"TO"` therefore hits those lines.
- `-x` compares the **entire** stripped line to the pattern. A substring that is not the whole line is not a hit.
- `-x -i` compares case-folded equality, still the whole line.
- `-v` without `-x` keeps lines that do **not** contain the substring.
- `-x -v` keeps every line that is **not** exactly equal to the pattern (after optional case-fold).
- An empty pattern (`""`) is a substring of every string, so every line hits unless `-x` is set (then only empty lines hit). Unlikely in tests; handle it by using `in`/`==` naturally.
- Never lowercase the text that is later printed.

### 5.3 `-l` (filenames only)

If a file has **at least one selected line** (after `-i`/`-x`/`-v`):

- Emit exactly `f"{filename}\n"`.
- Emit it **once**, when the first selected line is found.
- Stop scanning that file (optional optimization; scanning the rest is fine if you still emit once).
- Do **not** emit line text or line numbers.

`-l` **wins over `-n`**: `-n -l` still prints only names. Tests state this as “file flag takes precedence over line number flag.”

`-l` prints the name even when **only one** file was given (unlike the normal multi-file prefix rule).

`-l -v`: the name is printed if the file has at least one line that **fails** the (possibly exact, possibly case-insensitive) match. A file whose every line matches is omitted. An empty file has no selected lines → omit.

### 5.4 Output format (when not `-l`)

`multi_file = len(files) > 1`. This depends on how many names were **passed**, not how many actually produced hits. Searching three files and matching in only one still prefixes `filename:`.

Assemble a prefix, then the original line, then `\n`:

| Situation              | Record |
|------------------------|--------|
| 1 file, no `-n`        | `{line}\n` |
| 1 file, `-n`           | `{lineno}:{line}\n` |
| N>1 files, no `-n`     | `{filename}:{line}\n` |
| N>1 files, `-n`        | `{filename}:{lineno}:{line}\n` |
| `-l` (1 or N files)    | `{filename}\n` |

Colon placement: filename (if present), then line number (if `-n` and not `-l`), then the raw line. No extra spaces.

Line numbers count **all** file lines from 1, not the index among matches.

### 5.5 Top-level `grep`

```text
options = parse_flags(flags)
multi_file = len(files) > 1
out = []
for filename in files:
    out.extend(search_file(filename, pattern, options, multi_file))
return "".join(out)
```

Order: files in `files` order; within a file, increasing `lineno`.

If `files` is empty, return `""`. The spec says one or more files; this is defensive only.

---

## 6. Flag interaction matrix

| Flags        | Matcher                         | What is emitted |
|--------------|---------------------------------|-----------------|
| (none)       | substring, case-sensitive       | matching lines, prefix if N>1 |
| `-i`         | substring, case-insensitive     | same, original text |
| `-x`         | whole line == pattern           | matching lines |
| `-x -i`      | whole line, case-insensitive    | matching lines |
| `-v`         | not substring                   | non-matching lines |
| `-x -v`      | not whole-line equality         | all other lines |
| `-n`         | (any matcher)                   | add `lineno:` after optional `filename:` |
| `-l`         | (any matcher)                   | each hitting file name once |
| `-n -l`      | (any matcher)                   | same as `-l` only |
| `-n -i -x`   | whole line, case-insensitive    | numbered (and named if N>1) original line |
| `-n -l -x -i`| whole line, case-insensitive    | names of files that have an exact (CI) hit; or `""` if none |

All five flags may appear together. Parse independently; `-l` only changes **formatting / early stop**, not the matcher, except that invert still affects *whether* the file is selected.

---

## 7. Worked examples (from the fixture texts)

Use these as mental oracles while implementing. Line numbers are 1-based.

**Single file, substring, no flags**

`grep("Agamemnon", "", ["iliad.txt"])`  
→ `"Of Atreus, Agamemnon, King of men.\n"`

**Single file, `-n`**

`grep("Forbidden", "-n", ["paradise-lost.txt"])`  
→ `"2:Of that Forbidden Tree, whose mortal tast\n"`

**Single file, `-i`**

`grep("FORBIDDEN", "-i", ["paradise-lost.txt"])`  
→ `"Of that Forbidden Tree, whose mortal tast\n"`  
(printed text stays mixed-case)

**Single file, `-l`**

`grep("Forbidden", "-l", ["paradise-lost.txt"])`  
→ `"paradise-lost.txt\n"`

**Single file, `-x`**

`grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])`  
→ that full line plus `\n`. Pattern `"Eden"` with `-x` would miss.

**Single file, combined `-n -i -x`**

Pattern `OF ATREUS, Agamemnon, KING OF MEN.` on `iliad.txt`  
→ `"9:Of Atreus, Agamemnon, King of men.\n"`

**Single file, several substring hits (`"may"` on `midsummer-night.txt`)**

Lines 3, 5, 6 (no filename prefix). With `-n`: `3:...`, `5:...`, `6:...`. With `-x`: no hits (`""`).

**Single file, `-v` with `"Of"` on `paradise-lost.txt`**

Keep lines that do not contain capital-O `Of` (case-sensitive). Lines 1, 2, 7 start with `Of` and are dropped. Remaining five lines, in file order, each with `\n`.

**`-l` precedence**

`grep("ten", "-n -l", ["iliad.txt"])` → `"iliad.txt\n"` (no `2:`).

**Multiple files, one hit**

`grep("Agamemnon", "", [iliad, midsummer, paradise])`  
→ `"iliad.txt:Of Atreus, Agamemnon, King of men.\n"`  
Filename prefix is present because `len(files) == 3`.

**Multiple files, `-n`, pattern `"that"`**

```
midsummer-night.txt:5:But I beseech your grace that I may know
midsummer-night.txt:6:The worst that may befall me in this case,
paradise-lost.txt:2:Of that Forbidden Tree, whose mortal tast
paradise-lost.txt:6:Sing Heav'nly Muse, that on the secret top
```

(each followed by `\n`, concatenated)

**Multiple files, `-i`, pattern `"TO"`**

Hits include `into`, `To`, `to`, and `top` (substring). Output is original lines, each prefixed with `filename:`.

**Multiple files, `-n -l`, pattern `"who"`**

→ `"iliad.txt\nparadise-lost.txt\n"`  
(`midsummer-night.txt` has no `who`)

**No matches, even with many flags**

`grep("Gandalf", "-n -l -x -i", ["iliad.txt"])` → `""`

---

## 8. Edge cases and pitfalls

1. **Phantom blank line** from `split("\n")` on a trailing newline — wrong line count and extra records under `-v`.
2. **`rstrip()` of spaces** — breaks `-x` and would alter printed lines.
3. **Lowercasing printed output** — tests compare exact fixture text.
4. **Regex matching** — `Peleus'`, commas, `Heav'nly` must be literal; do not compile `pattern` as a regex.
5. **Whole-word matching** — not required and wrong (`"to"` must match inside `"into"`).
6. **Filename prefix based on hit count** — prefix iff `len(files) > 1`, even if only one file hits.
7. **`-l` omitted on single-file searches** — `-l` always prints names.
8. **`-n` leaking through `-l`**.
9. **Line numbers among matches only** — must be physical file line numbers.
10. **Missing final `\n`** on the last record — `assertMultiLineEqual` expects it.
11. **`"\n"` when there are zero hits** — must be `""`.
12. **Opening files without `open`** — mock never fires; tests fail.
13. **Case fold only on comparison copies**, not on `line` used for output.
14. **Invert applied before “does this file have a hit?”** for `-l`.
15. **Empty lines** in the middle of a file are real lines: they have a number; `-x` with `""` would match them; they print as `"\n"` (empty content + terminator).
16. **Preserve file order and in-file order.** Do not sort.
17. **Do not add a space after colons.**

Out of scope (do not implement unless you need them for local debugging):

- Regular expressions, `-w`, `-c`, `-A/-B/-C`, stdin (`-`), recursive search, binary files, encodings other than the mock’s Unicode strings, exit codes.

---

## 9. Suggested implementation sketch

Keep `grep.py` small (on the order of 40–70 lines). Illustrative structure only — this is the spec for the implementer, not a paste-in solution.

```python
def grep(pattern, flags, files):
    options = _parse_flags(flags)
    multi_file = len(files) > 1
    chunks = []
    for filename in files:
        chunks.extend(_search_file(filename, pattern, options, multi_file))
    return "".join(chunks)


def _parse_flags(flags):
    tokens = set(flags.split())
    return {
        "line_numbers": "-n" in tokens,
        "filenames_only": "-l" in tokens,
        "ignore_case": "-i" in tokens,
        "invert": "-v" in tokens,
        "exact_line": "-x" in tokens,
    }


def _search_file(filename, pattern, options, multi_file):
    hits = []
    with open(filename) as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip("\n")
            if _selected(line, pattern, options):
                if options["filenames_only"]:
                    return [f"{filename}\n"]
                hits.append(_format(filename, lineno, line, options, multi_file))
    return hits


def _selected(line, pattern, options):
    needle, haystack = pattern, line
    if options["ignore_case"]:
        needle, haystack = needle.lower(), haystack.lower()
    found = haystack == needle if options["exact_line"] else needle in haystack
    return found != options["invert"]


def _format(filename, lineno, line, options, multi_file):
    prefix = f"{filename}:" if multi_file else ""
    if options["line_numbers"]:
        prefix += f"{lineno}:"
    return f"{prefix}{line}\n"
```

Notes for the implementer:

- A dataclass instead of a `dict` is fine.
- Early `return [f"{filename}\n"]` on `-l` is optional; a `break` after append is equivalent.
- `_format` is never called for `-l`.

---

## 10. Verification (without touching tests)

After implementation, a later agent should:

1. Run `python -m unittest public_test.py` (the one published test: single-file `"Agamemnon"`).
2. Mentally or with a local scratch runner (not a test file in this repo) walk the worked examples in §7, especially:
   - multi-file prefix
   - `-n` placement relative to filename
   - `-l` vs `-n`
   - `-x -i` combined
   - `-v` and `-x -v`
   - `"TO"` / `-i` substring (`into`, `top`)
   - empty result `""`
3. Confirm `open` is used so the mock still wraps reads.

Do not add files under a tests/ directory, do not edit `public_test.py`, and do not fetch canonical-data.json from the network. This plan already encodes that suite’s behavior.
