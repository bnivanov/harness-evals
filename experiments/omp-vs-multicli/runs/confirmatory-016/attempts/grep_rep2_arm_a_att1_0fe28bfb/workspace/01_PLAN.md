# grep.py Implementation Guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

Return one concatenated string of matching output (not a list). Empty result is `""`, never `None`.

`public_test.py` mocks `grep.open` (`@mock.patch("grep.open", ...)`). The implementation **must** call the builtin `open()` on the `grep` module (plain `open(filename)` or `open(filename, "r")`). Do not use `pathlib`, `io.open`, or other readers — the mock will not intercept them.

Files exist as the mock's `StringIO` contents. Do not handle missing files.

Search is **fixed-string**, not regex. Treat `pattern` as a literal substring / whole-line string. Do not compile it with `re`.

## Inputs

| Arg | Shape | Notes |
|---|---|---|
| `pattern` | `str` | Literal search text. May be empty (then every line contains it). |
| `flags` | `str` | Space-separated tokens, e.g. `""`, `"-n"`, `"-n -i -x"`. |
| `files` | `list[str]` | One or more paths, in search order. |

Parse flags once:

```python
flag_set = set(flags.split())
```

Recognized tokens: `-n`, `-l`, `-i`, `-v`, `-x`. Unknown tokens: ignore. Concatenated bundles like `-ni` are **not** required (canonical tests use space-separated flags).

## File I/O and line identity

For each name in `files`, in list order:

```python
with open(filename) as fh:
    for line in fh:  # keeps the trailing newline if present
        ...
```

- Line numbers are **1-based** and count every physical line, matched or not.
- Matching uses the line **without** a single trailing `\n` (do not `str.strip()` / `rstrip()` — that would drop other trailing spaces).
  - `body = line[:-1] if line.endswith("\n") else line`
- Output of a matching line is the **original** `line` (newline preserved if the file had one).

## Match predicate

Let `needle = pattern.lower() if "-i" in flag_set else pattern`  
Let `hay = body.lower() if "-i" in flag_set else body`

1. Base match:
   - `-x` present: `hay == needle`
   - else: `needle in hay`
2. `-v` present: invert the boolean from step 1.

Order: compute match, then invert. `-i` applies to both sides before compare/`in`. `-x` is whole `body`, not a regex `^...$`.

Empty `pattern`: `-x` matches only empty bodies; without `-x`, every line matches (`"" in hay` is true).

## Output assembly

Walk files in order. Collect pieces in a list and `"".join` at the end (or equivalent).

### `-l` (file names only) — takes precedence

If a file has **at least one** matching line (after `-v`/`-x`/`-i`):

- Emit `f"{filename}\n"` **once**.
- Do not emit line text or line numbers.
- Later flags (`-n`) are ignored for formatting.
- Remaining lines of that file may be skipped.

Files with zero matches emit nothing. File order is the order of `files`.

### Line output (no `-l`)

For every matching line, emit:

```
[filename_prefix][number_prefix][original_line]
```

- `filename_prefix`: `f"{filename}:"` **iff** `len(files) > 1`.  
  This depends on how many files were **passed**, not how many produced hits. A 3-file search with one hit still prefixes that hit.
- `number_prefix`: `f"{line_number}:"` iff `-n` is set. Number is 1-based. When both prefixes apply, **filename first**, then number: `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n`
- Then the original line text, including its newline.

Single file, no `-n`: just the original line(s).

## Flag interaction matrix

| Flags | Effect |
|---|---|
| none | Substring, case-sensitive; raw lines; filename prefix iff multiple files |
| `-n` | Same match; prepend `N:` (after filename if any) |
| `-l` | Filenames of files with ≥1 match; no line text, no numbers |
| `-i` | Case-insensitive `in` / `==` |
| `-v` | Keep lines that **fail** the (possibly `-x`/`-i`) match |
| `-x` | Whole-line equality on the newline-stripped body |
| `-n -l` | `-l` wins → filenames only |
| `-n -i -x` | Case-insensitive whole-line; numbered (and file-prefixed if multi) |
| `-x -v` | Keep lines whose full body ≠ pattern (after `-i` if set) |
| `-n -l -x -i` | Still `-l` formatting; match is case-insensitive whole-line |

## Algorithms (linear, one pass)

```
parse flag_set
multi = len(files) > 1
want_l, want_n, want_i, want_v, want_x = tokens in flag_set
needle = pattern.lower() if want_i else pattern
out = []

for filename in files:
    with open(filename) as fh:
        for n, line in enumerate(fh, start=1):
            body = line[:-1] if line.endswith("\n") else line
            hay = body.lower() if want_i else body
            matched = (hay == needle) if want_x else (needle in hay)
            if want_v:
                matched = not matched
            if not matched:
                continue
            if want_l:
                out.append(filename + "\n")
                break
            prefix = ""
            if multi:
                prefix += filename + ":"
            if want_n:
                prefix += f"{n}:"
            out.append(prefix + line)

return "".join(out)
```

No extra allocation beyond the output list and per-line strings. Do not slurp a file into a second full copy unless using `readlines()` once (acceptable; streaming `for line in fh` is preferred).

## Edge cases

- **No matches / unknown pattern**: `""`.
- **Multiple matches in one file**: all matching lines, file order, line order.
- **Same line matches once**: substring match is boolean, not per-occurrence.
- **Last line without `\n`**: match on full body; emit without adding a newline.
- **Pattern equals line including spaces**: `-x` compares the body, which still has leading/trailing spaces other than the line terminator.
- **`-i` and non-ASCII**: `str.lower()` is enough for the literary ASCII fixtures.
- **One file in `files`**: never `filename:` prefix (except `-l`, which is the filename itself).
- **`-l` and `-v`**: a file is listed if it has any non-matching line.
- **`-x` substring-only hits**: e.g. `"may"` with `-x` on midsummer-night yields no lines.
- **Do not strip the files list**; search every entry even if names repeat.

## Fixture-backed expected examples

`iliad.txt` / `midsummer-night.txt` / `paradise-lost.txt` as in `public_test.py` (`FILE_TEXT`).

- `grep("Agamemnon", "", ["iliad.txt"])`  
  → `Of Atreus, Agamemnon, King of men.\n`
- `grep("Forbidden", "-n", ["paradise-lost.txt"])`  
  → `2:Of that Forbidden Tree, whose mortal tast\n`
- `grep("FORBIDDEN", "-i", ["paradise-lost.txt"])`  
  → `Of that Forbidden Tree, whose mortal tast\n`
- `grep("Forbidden", "-l", ["paradise-lost.txt"])`  
  → `paradise-lost.txt\n`
- `grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])`  
  → `With loss of Eden, till one greater Man\n`
- `grep("OF ATREUS, Agamemnon, KIng of MEN.", "-n -i -x", ["iliad.txt"])`  
  → `9:Of Atreus, Agamemnon, King of men.\n`
- `grep("may", "", ["midsummer-night.txt"])`  
  → three lines (3, 5, 6 of that file), concatenated, no prefixes.
- `grep("may", "-n", ["midsummer-night.txt"])`  
  → `3:...modesty,\n5:...know\n6:...case,\n`
- `grep("may", "-x", ["midsummer-night.txt"])`  
  → `""`
- `grep("ACHILLES", "-i", ["iliad.txt"])`  
  → lines 1 and 8.
- `grep("Of", "-v", ["paradise-lost.txt"])`  
  → lines whose body does not contain `Of` (lines 3, 4, 5, 6, 8).
- `grep("Gandalf", "-n -l -x -i", ["iliad.txt"])`  
  → `""`
- `grep("ten", "-n -l", ["iliad.txt"])`  
  → `iliad.txt\n`  (`-l` wins over `-n`)
- `grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])`  
  → `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
- `grep("who", "-l", [those three])`  
  → `iliad.txt\nparadise-lost.txt\n`
- `grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", [those three])`  
  → `paradise-lost.txt:4:With loss of Eden, till one greater Man\n`

## Module shape

Single function `grep` in `grep.py`. No CLI, no extra exports, no tests in this file. Keep helpers local if used (`_matches`, `_parse_flags`) — optional; a single function is enough.

## Out of scope

- Regex, binary files, directories, recursive search, stdin (`-`), exit codes, color.
- Mutating `files` or global state.
- Reading anything except `open(filename)` for names in `files`.
