# Implementation Guide: `grep.py`

## Goal

Implement `grep(pattern, flags, files) -> str` as a simplified, **fixed-string** (not regex) search. Read the given files in order, select lines according to the flags, and return a single string of formatted result lines, each terminated by `\n`.

Do **not** use the `re` module. The search string is a literal substring (or a full-line literal when `-x` is set).

The public test patches `grep.open` and `io.StringIO`. The implementation **must** open files with the builtin `open(...)` so `mock.patch("grep.open")` intercepts it.

---

## Function contract

```python
def grep(pattern, flags, files):
    """
    pattern: str  — literal search string (may be empty)
    flags:   str  — space-separated flag tokens, e.g. "", "-n", "-n -i -x"
    files:   list[str] — one or more filenames, processed in this order
    returns: str  — concatenated output lines, each ending with "\n";
                    "" if there are no results
    """
```

Never return `None`. The stub’s `pass` is incorrect.

### Inputs observed from tests / README

- `flags` is a **string**, not a list. Tokens are space-separated: `"-n -l -x -i"`.
- `files` is a list of names such as `"iliad.txt"`.
- File contents in tests are newline-terminated text (Unix `\n`). Files are provided via a mock `open` that returns `io.StringIO`.

Parse flags defensively:

```text
flag_tokens = flags.split()          # "" -> []
has_n = "-n" in flag_tokens          # line numbers
has_l = "-l" in flag_tokens          # filenames only
has_i = "-i" in flag_tokens          # case-insensitive
has_v = "-v" in flag_tokens          # invert match
has_x = "-x" in flag_tokens          # whole-line match
```

Unknown tokens can be ignored. Combined clusters like `-nix` are **not** required; tests use one flag per token.

---

## High-level algorithm

```
parse flags into booleans
multi_file = (len(files) > 1)
results = []

for each filename in files (given order):
    lines = read_lines(filename)          # 1-based numbering over this list
    for index, line in enumerate(lines, start=1):
        matched = line_matches(line, pattern, has_i, has_x)
        if has_v:
            matched = not matched
        if not matched:
            continue
        if has_l:
            results.append(filename + "\n")
            break                         # one name per file; skip remaining lines
        results.append(format_line(filename, index, line, multi_file, has_n))

return "".join(results)
```

This is a single sequential pass. Files are small; no indexing is needed.

---

## Reading files

Use builtin `open` (patch target is `grep.open`):

```python
with open(filename) as fh:
    text = fh.read()
```

Do **not** use `pathlib`, `io.open`, or `Path.read_text()` — those bypass the mock.

### Splitting into lines

Use `str.splitlines()` (no keepends).

Why not `split("\n")`?

- Test files end with a trailing `\n`. `split("\n")` would produce a final empty string, which would be treated as an extra empty line.
- Inverted-match tests (`-v`) would then emit a spurious empty result line.
- `splitlines()` drops the terminator and does not keep a trailing empty line after a final newline.

Line numbers are **1-based** over the resulting list (physical lines, including lines that will later be filtered out).

Preserve line text exactly: leading/trailing spaces, punctuation, and internal whitespace stay as-is. Do not strip.

If a file is empty (`text == ""`), `splitlines()` yields `[]` — no matches, and `-v` also yields nothing (there are no lines to invert).

---

## Matching (`line_matches`)

Matching is **literal**.

### Normalization for `-i`

If `has_i`, compare `line.lower()` and `pattern.lower()`.

`casefold()` is also acceptable; test data is ASCII, so `lower()` is enough. Apply the same function to both sides. Do not mutate the original `line` used for output.

### Match predicate (before invert)

| Flags | Predicate (on possibly-lowercased `line` / `pattern`) |
|---|---|
| default | `pattern in line` (substring; empty pattern matches every line) |
| `-x` | `line == pattern` (entire line, including spaces/punctuation) |
| `-x` + empty pattern | only a truly empty line matches |

Do **not** treat the pattern as a regex. A pattern of `"."` matches a period character, not “any character”.

### Invert (`-v`)

Applied **after** the predicate:

```text
keep = (not predicate) if has_v else predicate
```

`-v` inverts *which lines are selected*, not the meaning of `-x` or `-i`. Combine as:

- `-x -v`: keep every line whose **entire** text is **not** equal to the pattern.
- `-i -v`: invert the case-insensitive substring test.
- `-i -x -v`: keep lines that are not a case-insensitive full-line equal.

---

## Output formatting

Each kept result is one string ending in `\n`. Concatenate in discovery order.

Let `line` be the original (not lowercased) line **without** a trailing newline.

### `-l` (filenames only) — highest output precedence

If `-l` is set:

- Output `"{filename}\n"` once for a file that has **at least one** selected line (after `-i`/`-x`/`-v`).
- Do **not** print line text.
- Do **not** print line numbers, even if `-n` is also set.
- Still prefix nothing else; never `filename:`.
- Applies to **single-file and multi-file** searches alike.

This is the documented/tested rule: **file-name flag takes precedence over line-number flag**.

Stop scanning a file after the first selected line when `-l` is on.

### Line output (no `-l`)

Build an optional prefix, then the raw line, then `\n`.

| Situation | Format |
|---|---|
| 1 file, no `-n` | `{line}\n` |
| 1 file, `-n` | `{n}:{line}\n` |
| 2+ files, no `-n` | `{filename}:{line}\n` |
| 2+ files, `-n` | `{filename}:{n}:{line}\n` |

Rules:

- Filename prefix is based on `len(files) > 1`, **not** on how many files actually produced hits.
- Even if only one of three files matches, surviving lines still get the `filename:` prefix.
- Colon separators have no extra spaces: `iliad.txt:9:Of Atreus...`
- `{n}` is the 1-based integer as decimal text (`"2"`, `"9"`), no padding.
- Filename appears **before** the line number when both are present.

Return `""` when `results` is empty (no extra trailing newline).

---

## Flag combinations (required)

All flags are orthogonal except the output-precedence of `-l` over `-n` / content.

| Combination | Behavior |
|---|---|
| none | substring, case-sensitive, print matching lines |
| `-n` | same, prefix line numbers |
| `-l` | print matching file names only |
| `-i` | case-insensitive substring |
| `-v` | print non-matching lines |
| `-x` | full-line equality instead of substring |
| `-n -l` | `-l` wins: names only, no numbers |
| `-n -i -x` | case-insensitive full-line match, numbered |
| `-x -v` | all lines except exact (case-sensitive) full-line hits |
| `-n -l -x -i` | names of files that contain a case-insensitive full-line match |
| `-n -l -x -i` with no hits | `""` |

Process files left to right; within a file, lines top to bottom.

---

## Suggested structure

Keep everything in `grep.py`. A small, clear decomposition is enough:

```python
def grep(pattern, flags, files):
    opts = _parse_flags(flags)
    multi = len(files) > 1
    out = []
    for name in files:
        _search_file(name, pattern, opts, multi, out)
    return "".join(out)


def _parse_flags(flags):
    tokens = flags.split() if isinstance(flags, str) else list(flags)
    return {
        "n": "-n" in tokens,
        "l": "-l" in tokens,
        "i": "-i" in tokens,
        "v": "-v" in tokens,
        "x": "-x" in tokens,
    }


def _search_file(filename, pattern, opts, multi, out):
    with open(filename) as fh:
        lines = fh.read().splitlines()
    needle = pattern.lower() if opts["i"] else pattern
    for n, line in enumerate(lines, start=1):
        hay = line.lower() if opts["i"] else line
        hit = (hay == needle) if opts["x"] else (needle in hay)
        if opts["v"]:
            hit = not hit
        if not hit:
            continue
        if opts["l"]:
            out.append(filename + "\n")
            return
        out.append(_format_line(filename, n, line, multi, opts["n"]))


def _format_line(filename, n, line, multi, numbered):
    prefix = ""
    if multi:
        prefix += filename + ":"
    if numbered:
        prefix += str(n) + ":"
    return prefix + line + "\n"
```

Helpers may be inlined; names are not part of the public API. Only `grep` is imported by tests.

The `isinstance(flags, str)` guard is optional. Tests pass a string.

---

## Edge cases to handle

1. **No matches** — return `""`, including with many flags set.
2. **Single vs multiple files** — filename prefix depends on the length of the `files` argument.
3. **Several matches in one file** — emit every selected line, in file order.
4. **`-x` with a substring that is not the whole line** — no match (e.g. pattern `"may"` vs a longer sentence).
5. **`-i`** — `"FORBIDDEN"` matches `"Forbidden"`; output uses the file’s original casing.
6. **`-l` + several hits in one file** — one filename line, then move to the next file.
7. **`-l` + `-n`** — still filenames only.
8. **`-v`** — lines that do **not** contain the pattern; still honor `-i` / `-x`.
9. **`-x -v`** — omit only the exact matching line(s); print the rest with the usual prefixes.
10. **Trailing newline in source files** — do not emit a blank extra line.
11. **Empty pattern** — `"" in line` is true for every line; with `-x`, only empty lines; with `-v` and no `-x`, no lines (every line “matches”).
12. **Empty file** — no lines, so no output even with `-v`.
13. **Literal special characters** — `*`, `.`, `[` are ordinary characters.
14. **File order** — `files = ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"]` must keep that order in the output.
15. **Same file listed twice** — search it twice independently (not required by tests, but follows the spec).
16. **Do not strip** line content; commas, quotes, and spacing are significant for `-x`.

---

## Worked examples (from the public file corpus)

Corpus files: `iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt` (see `public_test.py` / README-style Iliad / Midsummer / Paradise Lost snippets). Last lines of each file include a terminating `\n`.

| Call | Result |
|---|---|
| `grep("Agamemnon", "", ["iliad.txt"])` | `Of Atreus, Agamemnon, King of men.\n` |
| `grep("Forbidden", "-n", ["paradise-lost.txt"])` | `2:Of that Forbidden Tree, whose mortal tast\n` |
| `grep("FORBIDDEN", "-i", ["paradise-lost.txt"])` | `Of that Forbidden Tree, whose mortal tast\n` |
| `grep("Forbidden", "-l", ["paradise-lost.txt"])` | `paradise-lost.txt\n` |
| `grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])` | that full line + `\n` |
| `grep("OF ATREUS, AGAMEMNON, KING OF MEN.", "-n -i -x", ["iliad.txt"])` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("may", "", ["midsummer-night.txt"])` | three `may` lines, in order, each with `\n` |
| `grep("may", "-n", ["midsummer-night.txt"])` | `3:...\n5:...\n6:...\n` |
| `grep("may", "-x", ["midsummer-night.txt"])` | `""` |
| `grep("ACHILLES", "-i", ["iliad.txt"])` | two Achilles lines |
| `grep("Of", "-v", ["paradise-lost.txt"])` | the five lines that do not contain `"Of"` |
| `grep("Gandalf", "-n -l -x -i", ["iliad.txt"])` | `""` |
| `grep("ten", "-n -l", ["iliad.txt"])` | `iliad.txt\n` |
| `grep("Agamemnon", "", [all three])` | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `grep("who", "-l", [all three])` | `iliad.txt\nparadise-lost.txt\n` |
| `grep("who", "-n -l", [all three])` | same as `-l` only |
| `grep("Frodo", "-n -l -x -i", [all three])` | `""` |

For `-n` on multiple files, the shape is `midsummer-night.txt:5:But I beseech...`.

For `-i` on `"TO"` across three files, every line containing `to` / `To` / `TO` as a substring is emitted with `filename:` prefixes, files in argument order.

---

## Constraints and non-goals

- **Must** use builtin `open(filename)` (context manager preferred).
- **Must not** compile or search with regex.
- **Must not** print to stdout; **return** the string.
- **Must not** depend on the real filesystem; tests inject `StringIO`.
- No CLI / `sys.argv`. The function *is* the interface.
- No extra files, logging, or debug prints.
- Do not edit tests.

---

## Implementation checklist

1. Parse space-separated flags into five booleans.
2. Open each file with `open`, `read()`, `splitlines()`.
3. Match with `in` or `==`, optional `.lower()`, then optional invert.
4. Format with filename / line-number prefixes as specified; `-l` short-circuits per file.
5. `return "".join(parts)`.

After implementation, `python -m unittest public_test.py` must pass. Hidden tests cover the flag matrix and multi-file formatting above; matching this plan is sufficient.
