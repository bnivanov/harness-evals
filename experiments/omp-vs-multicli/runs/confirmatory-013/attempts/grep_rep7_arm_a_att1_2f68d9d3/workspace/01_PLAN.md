# grep.py — Implementation Guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: fixed string (literal substring), never a regex.
- `flags`: a single string of zero or more space-separated tokens from `{-n, -l, -i, -v, -x}`. Empty string means no flags. Parse with `str.split()` (whitespace-separated exact tokens). Do not interpret bundled forms like `-nix`.
- `files`: one or more filenames, searched in the given order.
- Return: one concatenated string of output lines, each terminated by `\n`. Return `""` when nothing matches. Do not print.

Tests patch `grep.open`. Call the builtin `open(filename)` (text mode, default encoding). Do not use `pathlib`, `io.open`, or `from io import open`.

## File I/O

For each name in `files`, in order:

```python
with open(filename) as fh:
    for lineno, line in enumerate(fh, start=1):
        ...
```

- Line numbers are 1-based and count every physical line, matches or not.
- `line` from the file iterator usually includes a trailing `\n`. Compare without the terminator; emit with a terminator.
- Normalize for matching: `content = line.rstrip("\n")`.
- Normalize for output: if `line` already ends in `\n`, use it as-is; otherwise append `\n`. This covers a last line with no newline.

Assume filenames exist (the test mock raises if not). Do not catch `KeyError`/`FileNotFoundError`.

## Flag parsing

```text
tokens = set(flags.split())
n = "-n" in tokens   # prepend line number
l = "-l" in tokens   # file names only
i = "-i" in tokens   # case-insensitive
v = "-v" in tokens   # invert match
x = "-x" in tokens   # whole-line match
```

Unknown tokens: ignore or treat as absent; the public suite only sends the five flags above.

Flags compose. Evaluation order for a candidate line:

1. Optionally case-fold both sides (`-i`).
2. Test match (`-x` vs substring).
3. Invert boolean (`-v`).
4. Format using `-n` / `-l` / multi-file prefix.

## Match predicate

Let `text = line.rstrip("\n")` and `pat = pattern`.

If `-i`: compare `text.lower()` to `pat.lower()` (Unicode default `.lower()` is enough). Do not use `casefold()` unless needed; tests are ASCII.

If `-x`: `matched = (text == pat)` after optional lowercasing.

Else: `matched = (pat in text)` after optional lowercasing.

If `-v`: `matched = not matched`.

Empty `pattern`:

- Without `-x`: `"" in text` is true for every line → all lines match (then `-v` yields none).
- With `-x`: only a line whose content is exactly `""` (a blank line, i.e. `"\n"` in the file) matches.

Never compile `pattern` as a regex. Characters like `'`, `.`, `*`, `[` are literal.

## Output formatting

Let `multi = len(files) > 1`.

### `-l` (file-name mode)

`-l` overrides line content and `-n`.

- If a file has **at least one** matching line (after `-i`/`-x`/`-v`), emit `filename + "\n"` once.
- Skip remaining lines of that file once a hit is found (optional optimization).
- Do not prefix extra `filename:` — the name **is** the output.
- Same format for one file or many.
- Files with zero matching lines contribute nothing.
- Order: same as `files`.

`-l` + `-v`: a file is listed iff it contains at least one line that **fails** the pattern test. A file whose every line matches the pattern is omitted. An empty file is omitted (no lines → no inverted hits).

### Line mode (no `-l`)

For each matching line, emit exactly one output record:

```
[ filename ":" ] [ lineno ":" ] original_line_with_newline
```

Rules:

- Filename prefix **if and only if** `len(files) > 1`. Single-file search never prefixes the name (even if that one name is in a one-element list).
- Line-number prefix **if and only if** `-n`. Numbers are decimal, no padding, 1-based.
- When both prefixes apply: `filename:lineno:content\n` — number **after** the filename, both followed by `:`.
- When only `-n`: `lineno:content\n`.
- When only multi-file: `filename:content\n`.
- When neither: `content\n` (the original line).
- `content` is the original line text plus newline, not the case-folded copy.

Join records with `""` (each already has `\n`). Preserve file order, then line order.

## Algorithm (single pass)

```text
opts = parse flags
multi = len(files) > 1
out = []

for filename in files:
    with open(filename) as fh:
        file_already_listed = False
        for lineno, raw in enumerate(fh, start=1):
            if l and file_already_listed:
                break
            text = raw.rstrip("\n")
            if line_matches(text, pattern, i, x, v):
                if l:
                    out.append(filename + "\n")
                    file_already_listed = True
                else:
                    out.append(format(filename, lineno, raw, multi, n))

return "".join(out)
```

No extra buffering beyond `out`. Do not sort. Do not unique lines (two identical matching lines both emit).

## Worked examples (from public fixture text)

`iliad.txt` line 9 is `Of Atreus, Agamemnon, King of men.\n`.

| Call | Result |
|---|---|
| `grep("Agamemnon", "", ["iliad.txt"])` | `Of Atreus, Agamemnon, King of men.\n` |
| `grep("Agamemnon", "-n", ["iliad.txt"])` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("Agamemnon", "-l", ["iliad.txt"])` | `iliad.txt\n` |
| `grep("AGAMEMNON", "-i", ["iliad.txt"])` | same line as no-flags |
| `grep("Agamemnon", "-x", ["iliad.txt"])` | `""` (line is not exactly the pattern) |
| `grep("Of Atreus, Agamemnon, King of men.", "-x", ["iliad.txt"])` | that full line |
| `grep("Agamemnon", "-v", ["iliad.txt"])` | all iliad lines except line 9 |
| `grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt"])` | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `grep("Agamemnon", "-n", ["iliad.txt", "paradise-lost.txt"])` | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |

Multiple matches in one file: emit every hit in order. Example: pattern `"Of"` in `paradise-lost.txt` hits lines 1, 2, and 7 (`Of Mans…`, `Of that Forbidden…`, `Of Oreb…`).

## Edge cases

| Case | Behavior |
|---|---|
| No matches | `""` |
| Empty `files` | `""` (nothing to search); suite always passes ≥1 file |
| Empty file | no lines → no output; `-l` does not print it |
| Empty pattern | substring-match all lines; `-x` matches only empty content lines |
| Pattern longer than line | no substring match; `-x` is false unless equal |
| `-i` only folds comparison, never output | |
| `-v` + `-x` | keep lines that are not exactly the pattern |
| `-v` + `-i` | invert after case-insensitive test |
| `-l` + `-n` | names only; drop numbers |
| `-l` + multi-file | still `name\n` per hitting file, no `name:` prefix |
| Last line without `\n` | still emit a trailing `\n` on that record |
| Trailing spaces / punctuation | part of the line; `-x` requires exact equality including spaces |
| `'`, commas, etc. in pattern | literal |
| Flag string with extra spaces | `split()` already collapses |
| Repeated flags | `set` membership; harmless |
| Overlapping files in the list | search each occurrence independently (unlikely) |

## Data structures

- Flags: `set[str]` of tokens, or five booleans.
- Output: `list[str]` then `"".join`. Avoid repeated `+=` on a string in the inner loop.
- No regex, no dict of files, no class required. A tiny helper for match and a tiny helper for format keep `grep()` readable.

## Non-goals / pitfalls

- Do not use `re` / `fnmatch`.
- Do not strip trailing spaces from lines.
- Do not 0-index lines.
- Do not prefix filename when `len(files) == 1`.
- Do not emit a trailing extra `\n` beyond those on each record (no blank line at EOF).
- Do not write files or use stdin.
- Keep helpers in `grep.py`; the only required export is `grep`.

## Suggested layout

```python
def _parse_flags(flags: str) -> tuple[bool, bool, bool, bool, bool]:
    ...

def _matches(text: str, pattern: str, insensitive: bool, exact: bool, invert: bool) -> bool:
    ...

def _format_line(filename: str, lineno: int, raw_line: str, multi: bool, number: bool) -> str:
    ...

def grep(pattern, flags, files):
    ...
```

That is the full behavior surface. Implement exactly this; do not extra-validate arguments.
