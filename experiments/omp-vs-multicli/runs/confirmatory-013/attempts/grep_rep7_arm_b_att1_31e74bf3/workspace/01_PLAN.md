# Implementation Guide: `grep.py`

## Goal

Implement `grep(pattern, flags, files)` so it searches one or more files for a **fixed string** (not a regular expression) and returns matching lines as a single string.

The public test covers only one path. Hidden tests follow the README and the standard Exercism `grep` suite (same three files, same flag combinations). Implement the full spec below, not just the one public assertion.

Do **not** change tests. Do **not** use regex for matching.

---

## Public contract

```python
def grep(pattern, flags, files):
    ...
```

| Argument | Type | Meaning |
|---|---|---|
| `pattern` | `str` | Literal search string. May contain spaces and punctuation. Never treat as a regex. |
| `flags` | `str` | Zero or more flags, **space-separated**. Examples: `""`, `"-n"`, `"-n -i -x"`, `"-x -v"`, `"-n -l -x -i"`. |
| `files` | `list[str]` | One or more file names, in the order they must be searched. |

**Return type:** `str`

- Concatenate every output record, each ending with `\n`.
- No matches → `""` (empty string, not `"\n"`).
- Do not print. Do not write to stdout.

---

## File I/O (required for tests)

Tests patch **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

Therefore the implementation **must** call the builtin `open` as a name looked up in the `grep` module:

```python
with open(filename) as f:
    ...
```

Rules:

- Do **not** use `pathlib.Path.read_text`, `io.open`, or `from io import open`.
- Do **not** import `open` from elsewhere.
- A plain `open(filename)` / `open(filename, "r")` is enough. Encoding is not specified; default text mode is correct.
- Files in tests are always present. Missing files need not be handled unless you want a clean `FileNotFoundError`.
- Tests also wrap `io.StringIO`; you do not need to construct `StringIO` yourself.

### Reading lines

Iterate the file object so line numbers stay 1-based and match the original file:

```python
for line_number, raw in enumerate(f, start=1):
    line = raw.removesuffix("\n")   # or: line = raw[:-1] if raw.endswith("\n") else raw
```

Why not `splitlines()` on the whole file? Either is fine **if** you:

1. Drop the extra empty string produced by a trailing newline (`"a\nb\n".split("\n")` → `["a", "b", ""]`).
2. Do **not** strip other whitespace.
3. Number lines starting at 1 in file order.

`for line in f` is the least error-prone: a file whose last line has no newline is still one line; a trailing `\n` does not create an extra empty line.

**Never** `.strip()` the line. Leading/trailing spaces are part of the match text and of the output.

---

## Flag parsing

`flags` is a single string. Split on whitespace and test membership:

```python
tokens = flags.split()          # "" → []
show_line_numbers = "-n" in tokens
only_filenames    = "-l" in tokens
ignore_case       = "-i" in tokens
invert            = "-v" in tokens
entire_line       = "-x" in tokens
```

Unknown tokens can be ignored. Tests only pass the five documented flags.

Do **not** require clustered forms like `-nix`. Tests always pass separate tokens (`"-n -i -x"`). Supporting clustering is optional and unused.

Suggested internal structure (boolean flags only):

```python
@dataclass(frozen=True)
class Options:
    line_numbers: bool
    only_filenames: bool
    ignore_case: bool
    invert: bool
    entire_line: bool
```

A dict or five locals is equally fine. Keep parsing in one place.

---

## Matching algorithm (fixed string)

Match against the line **without** its terminating newline.

### Normalization (`-i`)

If `-i` is set, compare case-insensitively using `.lower()` on both pattern and line (ASCII text in tests; `casefold()` is also acceptable). Apply this **only for comparison**, never mutate the line that will be printed.

Cache `needle = pattern.lower() if ignore_case else pattern` once per call.

### Predicate (`-x` vs substring)

Let `haystack` be the (possibly lowercased) line and `needle` the (possibly lowercased) pattern.

| `-x` | Match if |
|---|---|
| off | `needle in haystack` (substring) |
| on  | `needle == haystack` (entire line, including spaces) |

Do **not** use `re`, `fnmatch`, or glob. A pattern such as `Ades` must not be treated as a character class.

### Inversion (`-v`)

```python
matched = (needle == haystack) if entire_line else (needle in haystack)
if invert:
    matched = not matched
```

`-v` inverts the boolean **after** `-i` and `-x` have been applied. It does not change output format.

### Empty pattern

Not in the public tests. POSIX-like behavior if it appears: `"" in line` is true for every line; with `-x`, only an empty line matches. No special case required if you use `in` / `==`.

---

## Output format

Build a list of strings and `"".join` at the end (each item already includes `\n`).

Let `multi_file = len(files) > 1`. Filename prefixes depend on how many files were **passed in**, not on how many produced hits.

### Mode A: `-l` (filenames only)

If a file has **at least one** matching line (after `-v` / `-x` / `-i`):

- Emit exactly `{filename}\n`
- Emit it **once**, when the first match in that file is found
- Stop scanning that file (optional but recommended)
- Do **not** emit line text
- Do **not** emit line numbers, even if `-n` is also set
- Do **not** add an extra `{filename}:` prefix

This is true for **one or many** files. Example: `grep("Agamemnon", "-l", ["iliad.txt"])` → `"iliad.txt\n"`.

`-l` takes precedence over `-n`. Combined `"-n -l"` still prints only names.

With `-l -v`, list files that contain at least one **non-matching** line. A file whose every line matches is omitted. An empty file has no such line, so it is omitted.

### Mode B: matching lines (default)

For each matching line, emit:

```
[{filename}:][{line_number}:]{line}\n
```

Assembly:

```text
prefix parts, joined by ":", then ":" then the raw line, then "\n"
```

| Condition | Prefix |
|---|---|
| 1 file, no `-n` | *(none)* → `{line}\n` |
| 1 file, `-n` | `{n}:{line}\n` |
| N files, no `-n` | `{file}:{line}\n` |
| N files, `-n` | `{file}:{n}:{line}\n` |

Line numbers are **1-based** and count every physical line in the file, including lines that did not match. Under `-v -n`, numbers are the original file line numbers of the non-matching lines.

The printed line is the original text (original case, original spacing), never the lowercased comparison copy.

---

## Control flow

```
parse flags
multi_file = len(files) > 1
needle = pattern.lower() if ignore_case else pattern
out = []

for filename in files:                 # preserve argument order
    with open(filename) as f:
        for line_number, raw in enumerate(f, start=1):
            line = strip only a trailing \n
            haystack = line.lower() if ignore_case else line
            is_match = (haystack == needle) if entire_line else (needle in haystack)
            if invert:
                is_match = not is_match
            if not is_match:
                continue

            if only_filenames:
                out.append(filename + "\n")
                break                  # first hit is enough
            else:
                parts = []
                if multi_file:
                    parts.append(filename)
                if line_numbers:
                    parts.append(str(line_number))
                if parts:
                    out.append(":".join(parts) + ":" + line + "\n")
                else:
                    out.append(line + "\n")

return "".join(out)
```

Process files left to right; within a file, lines top to bottom. That is the required output order.

---

## Reference corpus (used by tests)

These three files are opened by name via the mock. Your code must request exactly the names in `files`.

**iliad.txt** (9 lines)

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

**midsummer-night.txt** (7 lines)

```
1 I do entreat your grace to pardon me.
2 I know not by what power I am made bold,
3 Nor how it may concern my modesty,
4 In such a presence here to plead my thoughts;
5 But I beseech your grace that I may know
6 The worst that may befall me in this case,
7 If I refuse to wed Demetrius.
```

**paradise-lost.txt** (8 lines)

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

Use this corpus to reason about expected strings. Do not hard-code these contents in `grep.py`.

---

## Expected behaviors (cover these even if public_test does not)

### Single file

| Call | Result |
|---|---|
| `grep("Agamemnon", "", ["iliad.txt"])` | `Of Atreus, Agamemnon, King of men.\n` |
| `grep("Forbidden", "-n", ["paradise-lost.txt"])` | `2:Of that Forbidden Tree, whose mortal tast\n` |
| `grep("FORBIDDEN", "-i", ["paradise-lost.txt"])` | `Of that Forbidden Tree, whose mortal tast\n` |
| `grep("Forbidden", "-l", ["paradise-lost.txt"])` | `paradise-lost.txt\n` (name only, even for a single file) |
| `grep("may", "-x", ["midsummer-night.txt"])` | `""` (substring-only; no entire-line match) |
| `grep("OF ATREUS, AGAMEMNON, KING OF MEN.", "-n -i -x", ["iliad.txt"])` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("may", "", ["midsummer-night.txt"])` | three lines containing `may` |
| `grep("may", "-n", ["midsummer-night.txt"])` | `3:…\n5:…\n6:…\n` |
| `grep("ACHILLES", "-i", ["iliad.txt"])` | lines 1 and 8 |
| `grep("Of", "-v", ["paradise-lost.txt"])` | lines that do **not** contain `Of` (case-sensitive: lines 3,4,5,6,8) |
| `grep("Gandalf", "-n -l -x -i", ["iliad.txt"])` | `""` |
| `grep("ten", "-n -l", ["iliad.txt"])` | `iliad.txt\n` (`-l` wins) |
| `grep("Illustrious into Ades premature,", "-x -v", ["iliad.txt"])` | every iliad line except line 4 |

The important `-l` rule: on the first hit in a file, print `{filename}\n` once and move on. If the file has no hits, print nothing for it.

### Multiple files

Always prefix with `filename:` when `len(files) > 1`, even if only one file actually hits.

| Call | Result shape |
|---|---|
| `grep("Agamemnon", "", [iliad, midsummer, paradise])` | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `grep("may", "", same)` | three `midsummer-night.txt:…` lines |
| `grep("that", "-n", same)` | `midsummer-night.txt:5:…`, `midsummer-night.txt:6:…`, `paradise-lost.txt:2:…`, `paradise-lost.txt:6:…` |
| `grep("who", "-l", same)` | `iliad.txt\nparadise-lost.txt\n` (midsummer has no `who`) |
| `grep("may", "-n -l", same)` | `midsummer-night.txt\n` |
| `grep("TO", "-i", same)` | every line containing `to`/`To`/`TO`, each prefixed by file name |
| `grep("Frodo", "-n -l -x -i", same)` | `""` |

File order in the `files` list is output order. Within `-l`, names appear in the order those files first match.

---

## Edge cases and pitfalls

1. **Substring vs word.** `Of` matches `Of`, `Off`, and `loss of Eden`. There is no word-boundary flag.
2. **Case without `-i`.** `Of` does not match `of`. `ACHILLES` does not match `Achilles`.
3. **Entire line includes punctuation and spaces.** `-x` is exact equality of the full line, not “whole word”.
4. **`-x` + `-i`.** Lowercase both sides, then `==`.
5. **`-v` + `-x`.** Keep lines whose full text is **not** equal to the pattern.
6. **`-v` + substring.** Keep lines that do not contain the pattern anywhere.
7. **`-n` numbers non-matches under `-v`.** Numbers come from `enumerate`, not from a match counter.
8. **`-l` + `-n`.** Names only.
9. **`-l` + no hits.** Empty string; do not print anything.
10. **One file vs many.** Prefix filenames only when `len(files) > 1`. A single-file search never prints `iliad.txt:` before line content (except `-l`, which prints the name alone).
11. **Trailing newline on return.** Every emitted record ends with `\n`. The whole return value therefore ends with `\n` if it is non-empty, and is `""` otherwise. Do not add an extra final newline.
12. **Do not rstrip.** `King of men.` keeps the period. Do not strip spaces.
13. **Literal pattern.** Characters like `.` `*` `[` in the pattern are ordinary characters. (`Ades` in iliad is a substring of `Ades premature`, not a regex.)
14. **Stable scan.** Do not sort files or lines.
15. **Reuse of `open`.** Call `open` once per file. Do not read a file you were not asked to search.
16. **`flags` type.** It is a string in this track, not a list. `"-n" in flags` would also be true for `"-n -l"`, but **do not** use substring checks on the raw flags string (`"-i" in "-n"` is false, but a hypothetical `"-in"` would be ambiguous). Always `split()` then membership.
17. **Multiple flags, any order.** `"-x -v"` and `"-v -x"` are equivalent.

---

## Module shape

Keep everything in `grep.py`. A single function is enough; helpers are encouraged for clarity:

- `parse_flags(flags) -> Options`
- `matches(line, pattern, options) -> bool`
- `format_match(filename, line_number, line, options, multi_file) -> str`
- `grep(...)` orchestration + I/O

No CLI (`argparse`, `sys.argv`) is required. No extra dependencies.

Type hints are optional. If used, stay compatible with the test import: `from grep import grep`.

---

## Suggested implementation sketch

```python
def grep(pattern, flags, files):
    tokens = flags.split()
    line_numbers = "-n" in tokens
    only_filenames = "-l" in tokens
    ignore_case = "-i" in tokens
    invert = "-v" in tokens
    entire_line = "-x" in tokens

    needle = pattern.lower() if ignore_case else pattern
    multi_file = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as fh:
            for line_number, raw in enumerate(fh, start=1):
                line = raw[:-1] if raw.endswith("\n") else raw
                haystack = line.lower() if ignore_case else line
                found = haystack == needle if entire_line else needle in haystack
                if invert:
                    found = not found
                if not found:
                    continue
                if only_filenames:
                    output.append(f"{filename}\n")
                    break
                prefix = []
                if multi_file:
                    prefix.append(filename)
                if line_numbers:
                    prefix.append(str(line_number))
                if prefix:
                    output.append(":".join(prefix) + ":" + line + "\n")
                else:
                    output.append(line + "\n")

    return "".join(output)
```

This sketch is complete enough to pass the public test and the usual hidden suite. Prefer this logic over a regex-based rewrite.

---

## Self-check before finishing

- [ ] `open(...)` is used (patch target `grep.open`).
- [ ] Return value is `str`, lines joined with `\n`, empty → `""`.
- [ ] Five flags parsed from a space-separated string.
- [ ] `-i` / `-x` / `-v` compose as described.
- [ ] `-l` prints each matching file name once and ignores `-n`.
- [ ] Filename prefix only when `len(files) > 1`.
- [ ] Line numbers are 1-based original indices.
- [ ] Matching is literal substring / full-line equality, not regex.
- [ ] Original line text (not lowercased) is what gets printed.
- [ ] File and line order preserved.

---

## Out of scope

- Regex, `-E`, `-F` as a user-facing flag (search is always fixed-string).
- Recursive directory search, stdin, `-r`, `-c`, `-o`, context (`-A`/`-B`/`-C`).
- Binary files, encodings, color.
- Editing tests or adding files outside this workspace.
