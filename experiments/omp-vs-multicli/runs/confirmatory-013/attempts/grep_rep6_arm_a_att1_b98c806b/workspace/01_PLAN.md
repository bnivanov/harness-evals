# grep.py implementation guide

Implement `grep(pattern, flags, files) -> str` in `grep.py` only. Do not change tests.

This is a simplified Unix grep: **fixed-string** search (not regex). Read files in the given order, select lines, format, concatenate.

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

| Arg | Shape | Notes |
|-----|--------|--------|
| `pattern` | `str` | Literal substring / exact line text. May be empty. |
| `flags` | `str` | Zero or more short flags, space-separated (e.g. `""`, `"-n"`, `"-n -l -i"`). |
| `files` | `list[str]` | One or more filenames, search order = list order. |

Return a single string: selected output lines joined together. Every emitted record ends with `\n`. No matches → `""`.

Public example:

```python
grep("Agamemnon", "", ["iliad.txt"])
# -> "Of Atreus, Agamemnon, King of men.\n"
```

Tests patch `grep.open` (and wrap `io.StringIO`). **Must use builtin `open(filename)`** (text mode, default encoding). Do not use `pathlib`, `io.open`, or pre-read files another way — the mock will miss them.

## Flag parsing

```python
flagset = set(flags.split())
```

Recognized tokens (exact strings, including the dash):

| Flag | Meaning |
|------|---------|
| `-n` | Prefix 1-based line number + `:` on each **content** line. |
| `-l` | Names-only: emit each matching **file name** once, then stop that file. |
| `-i` | Case-insensitive compare. |
| `-v` | Invert: select lines that **fail** the match. |
| `-x` | Entire-line match (after stripping the terminating newline). |

Unknown tokens: ignore. Combined blobs like `-nl` are **not** required; the suite uses space-separated flags. Empty/`""` → no flags.

Independence: `-i`, `-v`, `-x` affect **selection**. `-n` and `-l` affect **presentation**. `-l` wins over `-n` (and over filename prefixes on content lines): when `-l` is set, never print line text or line numbers.

## Matching (per physical line)

File iteration: `for lineno, raw in enumerate(f, start=1)`.

Normalize **only for comparison**:

```python
text = raw.rstrip("\n")   # keep other trailing whitespace; do not rstrip()
```

Do **not** treat `\r\n` specially beyond `rstrip("\n")` (mock files use `\n`).

Let `needle = pattern`, `hay = text`. If `-i`: `needle = pattern.lower()`, `hay = text.lower()` (Unicode default `.lower()` is enough).

Match predicate **before** invert:

- `-x`: `hay == needle`
- else: `needle in hay` (empty pattern matches every line; with `-x`, only empty lines)

Then if `-v`: `selected = not matched`, else `selected = matched`.

`-v` applies to the already-computed match, including `-x` and `-i`. A line is selected iff it is in the inverted (or not) set.

## Output rules

Let `multi = len(files) > 1`. Filename prefix applies to **content lines only**, and only when `multi` is true. A single-file search never prefixes the filename unless `-l`.

### `-l` (names only)

If the file has **at least one selected line**:

- append `f"{filename}\n"`
- **break** (do not scan the rest; do not print other matches)

Order: file order in `files`. Duplicate filenames in `files` are independent searches (may print twice).

`-n` is ignored under `-l`.

### Content lines (no `-l`)

For each selected line, emit:

```
[filename:][lineno:][raw]
```

- `filename:` iff `multi`
- `lineno:` iff `-n` (decimal, no padding, 1-based)
- `raw` is the line **as read**, including its trailing `\n` if present

If `raw` has no trailing newline (possible last line), still emit a trailing `\n` so every record is a full line. (Canonical fixtures always include `\n` on every line, including the last.)

Examples:

| files | flags | one selected line `text\n` at line 9 of `a.txt` |
|-------|--------|--------------------------------------------------|
| 1 | (none) | `text\n` |
| 1 | `-n` | `9:text\n` |
| 2+ | (none) | `a.txt:text\n` |
| 2+ | `-n` | `a.txt:9:text\n` |
| any | `-l` | `a.txt\n` (once, if any selected line) |

## Algorithm

```
parse flagset from flags.split()
multi = len(files) > 1
out = []

for filename in files:
    with open(filename) as fh:
        for lineno, raw in enumerate(fh, 1):
            text = raw.rstrip("\n")
            matched = (text == pattern) or (pattern in text)  # with -i/-x as above
            if "-v" in flagset:
                matched = not matched
            if not matched:
                continue
            if "-l" in flagset:
                out.append(filename + "\n")
                break
            prefix = ""
            if multi:
                prefix += filename + ":"
            if "-n" in flagset:
                prefix += str(lineno) + ":"
            body = raw if raw.endswith("\n") else raw + "\n"
            out.append(prefix + body)

return "".join(out)
```

Open/close via `with`. Do not swallow `FileNotFoundError`; tests only open known names.

## Edge cases

| Case | Behavior |
|------|----------|
| No matches in any file | `""` |
| Multiple matches, one file | All selected lines, file order, no filename prefix |
| Multiple files, matches in some | Only matching files/lines; unmatched files emit nothing |
| Match only in last file | Same formatting; earlier files silent |
| `-i` | `"Agamemnon"` matches `"agamemnon"`; `-x -i` is case-insensitive full-line |
| `-v` | All non-matching lines; with `-x`, all lines that are not exactly the pattern |
| `-v -l` | File name if **at least one** non-matching line exists (selected-line semantics, not “files with zero matches”) |
| `-x` | Full `text == pattern` only; substring-only lines are non-matches |
| `-x` on a line with extra spaces | Non-match (spaces are significant) |
| Empty pattern, no `-x` | Every line matches (`"" in text`) |
| Empty pattern, `-x` | Only lines whose text is empty |
| Empty pattern, `-v` | Inverts the above |
| Pattern equals full line, no `-x` | Still a match (substring of itself) |
| `-n` line numbers | Count **every** physical line, including non-selected; numbers are not remapped |
| `-l` after first hit | Stop reading that file |
| `-n -l` | `-l` only |
| `-n -i`, `-x -n`, `-x -v`, `-i -v`, etc. | Combine selection flags then format |
| Several files + `-l` | One name per file that has a selected line, each `name\n` |
| Trailing newline on last fixture line | Present in mocks; matching uses stripped text; output keeps `\n` |
| Literal special chars in pattern | `. * [ ]` etc. are ordinary characters — **no regex** |
| Same line matches once | Do not emit duplicates from one line |

## Data structures

Keep it boring:

- `set[str]` of flag tokens
- `list[str]` accumulator of output chunks
- booleans: `ignore_case`, `invert`, `exact_line`, `names_only`, `number_lines`, `multi`

No compiled regex, no extra classes.

## File I/O invariant

```python
with open(filename) as f:
    ...
```

Must be the module-global `open` so `unittest.mock.patch("grep.open", ...)` intercepts it. Do not pass `encoding=` unless needed; mocks ignore extra kwargs but keep the call simple.

## Return / newline invariant

`"".join(chunks)` where every chunk ends with `\n`. Never strip the final newline. Never join with extra separators.

## Suggested helper split (optional)

Single function is enough. If splitting:

- `_parse_flags(flags) -> frozenset`
- `_selected(text, pattern, ignore_case, exact) -> bool`  # pre-invert
- rest inline in `grep`

Do not over-abstract.

## Verification (implementer)

Run the public test after implementing:

```text
python -m unittest public_test.py
```

Expect `test_one_file_one_match_no_flags` to pass: pattern `"Agamemnon"`, flags `""`, files `["iliad.txt"]` → exactly that one Iliad line plus newline.

Held-out tests will cover the flag matrix, multi-file prefixes, `-l` short-circuit, invert, case fold, and full-line match. The rules above are the full behavior; do not special-case the public fixture.
