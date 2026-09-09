# grep.py implementation guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: fixed string (not a regex). Match with Python `in` / `==`, never `re`.
- `flags`: space-separated flag tokens, or `""`. Public tests call `grep("Agamemnon", "", ["iliad.txt"])` and multi-flag forms like `"-n -i -x"`. Parse with `flags.split()` so extra/missing whitespace is ignored. `"".split()` → `[]`.
- `files`: one or more filenames, in search order. Open each with the builtin `open` so `unittest.mock.patch("grep.open", ...)` in `public_test.py` intercepts it. Do not use `pathlib`, `io.open`, or a local alias that would miss the patch.
- Return one string: every emitted record ends with `\n`. No matches → `""`.

Files in tests are the three poems in `FILE_TEXT` (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`). Each file is newline-terminated text with no blank lines.

## Flags (orthogonal except `-l` vs `-n`)

| Flag | Meaning |
|------|---------|
| `-i` | Case-insensitive compare (`str.lower()` on both pattern and line). |
| `-x` | Whole-line equality, not substring. |
| `-v` | Invert: keep lines that fail the match. |
| `-n` | Prefix 1-based line number and `:`. |
| `-l` | Emit each matching **file name** once, then stop that file. |

Unknown tokens: ignore (tests only send the five above).

## Algorithm

1. Parse flags into a set: `flagset = set(flags.split())`.
2. `needle = pattern.lower() if "-i" in flagset else pattern`.
3. `multi = len(files) > 1` — filename prefix on content lines depends on **how many files were requested**, not how many matched.
4. `out = []`.
5. For each `filename` in `files` (given order):
   1. `with open(filename) as fh:` then `for lineno, raw in enumerate(fh, start=1):`.
   2. `line = raw.rstrip("\n")`. Do **not** strip spaces or `\r` beyond the trailing `\n`. Matching and output use this stripped body; the file’s `\n` is not part of the text.
   3. `hay = line.lower() if "-i" else line`.
   4. `matched = (hay == needle) if "-x" else (needle in hay)`.
   5. If `-v`: `matched = not matched`.
   6. If not `matched`: continue.
   7. If `-l`: `out.append(filename)` and **break** this file (first hit is enough). Skip `-n` and content.
   8. Else build one record: join with `":"` the non-empty prefix list:
      - `filename` iff `multi`
      - `str(lineno)` iff `-n`
      - `line` (always last)
   9. `out.append(record)`.
6. Return `"".join(item + "\n" for item in out)`.

Open files sequentially; do not read everything into memory first beyond one file at a time.

## Output shapes

Single file, content match: `{line}\n`  
Single file, `-n`: `{lineno}:{line}\n`  
Multiple files, content match: `{file}:{line}\n`  
Multiple files, `-n`: `{file}:{lineno}:{line}\n`  
`-l` (any file count): `{file}\n` per file that has ≥1 selected line. No `:` , no line text, no numbers.

`-l` **wins over** `-n`. Test: `"-n -l"` + pattern `"ten"` on `iliad.txt` → `"iliad.txt\n"`.

## Match semantics (fixed string)

- Substring (default): `"may"` hits three lines in `midsummer-night.txt`; `"Agamemnon"` hits one line in `iliad.txt`.
- `-x`: `"may"` against `midsummer-night.txt` → `""`. Full line `"With loss of Eden, till one greater Man"` with `-x` hits.
- `-i`: `"FORBIDDEN"` hits `"Of that Forbidden Tree, whose mortal tast"`. Combined `"-n -i -x"` with `"OF ATREUS, Agamemnon, KING OF MEN."` → `"9:Of Atreus, Agamemnon, King of men.\n"` (single file).
- `-v`: keep non-matches. `"Of"` + `-v` on `paradise-lost.txt` drops the four lines that contain the substring `Of` (including `"Of Oreb..."`).
- `-x -v`: every line whose full text is not exactly the pattern. Canonical case: invert exact `"Illustrious into Ades premature,"` on `iliad.txt` returns the other eight lines.
- No matches (e.g. `"Gandalf"` / `"Frodo"` even with `"-n -l -x -i"`) → `""`.

Literal special characters in `pattern` stay literal (`in` / `==`). Empty `pattern`: every line is a substring match; `-x` matches only empty lines (none in the fixture files).

## Multi-file behavior

Same match rules; prepend `filename:` on content lines. `-l` lists files in argument order, once each, only those with a hit:

- `"who"` + `-l` on all three files → `"iliad.txt\nparadise-lost.txt\n"` (midsummer has no `who`).
- `"who"` + `"-n -l"` → same filenames; line numbers omitted.

`-i` + `"TO"` across three files is a large expected blob (many substring hits including `to`, `into`, `To`); implement matching correctly rather than hard-coding.

## I/O and line numbering

- Use `open(filename)` with no extra kwargs (mocked `StringIO` does not need encoding).
- `enumerate(..., 1)`: first line is `1`.
- `rstrip("\n")` only: a line that is `"foo\n"` becomes `"foo"`; a final line without newline still counts.
- Do not use `splitlines()` on the whole file if that would drop a trailing empty line; fixtures have no empty lines, but `for raw in fh` is the right model.
- Close via `with`.

## Structure (keep `grep.py` small)

One function is enough. Optional tiny helpers if it stays local:

- `_parse_flags(flags) -> set[str]`
- `_matches(line, needle, exact) -> bool` after case folding

No classes, no regex, no CLI `sys.argv`. Do not print; only return.

Suggested body sketch (implementer fills this in `grep.py` only):

```python
def grep(pattern, flags, files):
    flagset = set(flags.split())
    ignore_case = "-i" in flagset
    invert = "-v" in flagset
    exact = "-x" in flagset
    names_only = "-l" in flagset
    number_lines = "-n" in flagset
    needle = pattern.lower() if ignore_case else pattern
    multi = len(files) > 1
    out = []
    for filename in files:
        with open(filename) as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.rstrip("\n")
                hay = line.lower() if ignore_case else line
                matched = (hay == needle) if exact else (needle in hay)
                if invert:
                    matched = not matched
                if not matched:
                    continue
                if names_only:
                    out.append(filename)
                    break
                parts = []
                if multi:
                    parts.append(filename)
                if number_lines:
                    parts.append(str(lineno))
                parts.append(line)
                out.append(":".join(parts))
    return "".join(item + "\n" for item in out)
```

## Edge-case checklist (held-out tests will cover these)

- Flags string `""` vs `"-n"` vs `"-n -i -x"` vs `"-x -v"` vs `"-n -l"`.
- One file vs three files in the list `["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"]`.
- Several matches, preserve file order then line order.
- `-l` stops at first selected line per file (important with `-v`, where the first non-match selects the file).
- `-l` + `-v`: file is listed if **any** line fails the (possibly `-x`/`-i`) match — typically every non-empty file unless every line matches.
- Prefix filename only when `len(files) > 1`, even if later files have zero hits.
- Return `""` not `"\n"` when nothing matches.
- Do not add a trailing extra newline beyond one per record.

## Out of scope

- Regex, recursive directories, stdin, binary files, color, context (`-A`/`-B`/`-C`).
- Editing tests or any file other than the eventual `grep.py` implementation (this plan file is the only planner output).
