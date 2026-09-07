# grep.py Implementation Guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: literal fixed string (never a regex).
- `flags`: space-separated flag tokens, e.g. `""`, `"-n"`, `"-n -i -x"`. Order does not matter. Do not support clustered GNU-style `-nix`.
- `files`: one or more filenames, processed left to right.
- Return: a single string of output lines in discovery order. No matches → `""`.

Tests patch `grep.open`. **Must** call the builtin `open(...)` inside this module (e.g. `with open(filename) as fh:`). Do not use `pathlib`, `io.open`, or another alias.

## High-level algorithm

1. Parse flags once.
2. `multi = len(files) > 1` — filename prefix is based only on this, not on how many files actually match.
3. For each filename, in given order:
   - Read the file with `open(filename)` (text mode). Iterate lines; keep each line **exactly** as returned by the file object (including its trailing `\n` if present).
   - Line numbers are **1-based** and count every physical line, matches and non-matches.
   - For each line, decide match vs non-match (see Matching).
   - If `-l` and this file has ≥1 selected line: emit `f"{filename}\n"` once, then stop reading that file.
   - Else: for each selected line, emit the formatted line (see Output format).
4. `return "".join(chunks)`.

No extra trailing newline beyond what each emitted piece already has.

## Flag parsing

```text
tokens = set(flags.split())   # "".split() == []
n_flag = "-n" in tokens       # prepend line number
l_flag = "-l" in tokens       # filenames only
i_flag = "-i" in tokens       # case-insensitive
v_flag = "-v" in tokens       # invert selection
x_flag = "-x" in tokens       # whole-line match
```

Unknown tokens: ignore (none appear in tests). Combinations are all valid.

## Matching (per line)

Compare against the line **without** its terminator. Do **not** use `.strip()` — leading/trailing spaces are significant.

```text
body = line.rstrip("\n")
needle, hay = pattern, body
if i_flag:
    needle, hay = needle.lower(), hay.lower()

if x_flag:
    hit = (hay == needle)
else:
    hit = (needle in hay)      # substring; empty pattern matches every line

selected = (not hit) if v_flag else hit
```

Rules:

- Literal only: `in` / `==`. Never `re`.
- `-i` applies to both pattern and line body before compare.
- `-x` is full-body equality after the optional case-fold; substring is not enough.
- `-v` inverts the boolean **after** `-i`/`-x`. Selected lines are the ones printed (or that qualify a file for `-l`).
- `-l` + `-v`: list files that contain at least one **non-matching** line (i.e. at least one inverted-selected line).

## Output format

Precedence: **`-l` wins over `-n` and over the multi-file prefix.**

| Mode | One file | Several files (`len(files) > 1`) |
|---|---|---|
| default | `{line}` | `{filename}:{line}` |
| `-n` | `{lineno}:{line}` | `{filename}:{lineno}:{line}` |
| `-l` | `{filename}\n` | `{filename}\n` (once per matching file) |
| `-n -l` | same as `-l` | same as `-l` |

`{line}` is the raw file line, including its `\n` when the file had one.

Colon placement: filename (if any), then line number (if `-n` and not `-l`), then the raw line, joined by single `:` between the metadata parts and before the line.

```text
# helpers for non -l output
prefix_parts = []
if multi:
    prefix_parts.append(filename)
if n_flag:
    prefix_parts.append(str(lineno))
if prefix_parts:
    emit = ":".join(prefix_parts) + ":" + line
else:
    emit = line
```

`-l` output is always `filename + "\n"`, never `filename:`. Duplicate matches in one file still produce **one** name.

## File I/O details

- `with open(filename) as fh:` then `for lineno, line in enumerate(fh, start=1):`.
- Files in the public fixture all end with `\n`, so every line includes a trailing newline. If a last line had no newline, emit it unchanged (do not invent `\n` on content lines).
- Do not skip empty lines: an empty body `""` is a real line; `-x` with pattern `""` would select it.
- Missing files: let `open` raise; tests only open known names.

## Worked examples (from README + public fixture)

Fixture files (9 / 7 / 8 lines), same text as `public_test.py`.

**Single file, no flags**

`grep("Agamemnon", "", ["iliad.txt"])`  
→ `Of Atreus, Agamemnon, King of men.\n`

**`-n`**

`grep("Forbidden", "-n", ["paradise-lost.txt"])`  
→ `2:Of that Forbidden Tree, whose mortal tast\n`

**`-i`**

`grep("FORBIDDEN", "-i", ["paradise-lost.txt"])`  
→ `Of that Forbidden Tree, whose mortal tast\n`

**`-l`**

`grep("Forbidden", "-l", ["paradise-lost.txt"])`  
→ `paradise-lost.txt\n`

**`-x`**

`grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])`  
→ that full line plus `\n`.  
`grep("may", "-x", ["midsummer-night.txt"])` → `""` (substring-only hits).

**`-n -i -x`**

`grep("OF ATREUS, AGAMEMNON, KING OF MEN.", "-n -i -x", ["iliad.txt"])`  
→ `9:Of Atreus, Agamemnon, King of men.\n`

**Several matches, `-n`**

`grep("may", "-n", ["midsummer-night.txt"])`  
→ lines 3, 5, 6 with `3:`, `5:`, `6:` prefixes.

**`-v`**

`grep("Of", "-v", ["paradise-lost.txt"])`  
drops every line whose body **contains** `Of` (case-sensitive). Remaining: lines 3, 4, 5, 6, 8.

**`-x -v`**

`grep("Illustrious into Ades premature,", "-x -v", ["iliad.txt"])`  
every iliad line except the exact line 4.

**`-n -l` precedence**

`grep("ten", "-n -l", ["iliad.txt"])` → `iliad.txt\n` (no line number).

**No matches** (any flag mix, including `-n -l -x -i`) → `""`.

**Multiple files, no flags** — prefix every content line:

`grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])`  
→ `iliad.txt:Of Atreus, Agamemnon, King of men.\n`

**Multiple files, `-n`** — `filename:lineno:line`:

`grep("that", "-n", [iliad, midsummer, paradise])`  
→  
`midsummer-night.txt:5:But I beseech your grace that I may know\n`  
`midsummer-night.txt:6:The worst that may befall me in this case,\n`  
`paradise-lost.txt:2:Of that Forbidden Tree, whose mortal tast\n`  
`paradise-lost.txt:6:Sing Heav'nly Muse, that on the secret top\n`  

(`That Shepherd...` is **not** a hit without `-i`.)

**Multiple files, `-l`**

`grep("who", "-l", [all three])` → `iliad.txt\nparadise-lost.txt\n`  
(midsummer has no `who`; each matching file once; file order preserved).

**Multiple files, `-n -i -x`**

`grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", [all three])`  
→ `paradise-lost.txt:4:With loss of Eden, till one greater Man\n`

## Suggested structure (keep it boring)

One public function plus two tiny helpers is enough. No classes.

```text
def grep(pattern, flags, files):
    opts = _parse_flags(flags)
    multi = len(files) > 1
    out = []
    for name in files:
        out.extend(_scan_file(name, pattern, opts, multi))
    return "".join(out)

def _parse_flags(flags) -> simple namespace/tuple of five bools

def _selected(body, pattern, opts) -> bool

def _scan_file(name, pattern, opts, multi) -> list[str]
    # open, enumerate, either [filename\n] or formatted lines
```

Do not pre-read all files into a dict; stream one file at a time.

## Edge cases to handle (even if public_test.py is thin)

| Case | Behavior |
|---|---|
| `flags == ""` | all options false |
| Extra spaces in flags | `str.split()` already collapses them |
| Empty pattern, no `-x` | every line is a substring hit |
| Empty pattern, `-x` | only lines whose body is empty |
| `-i` + `-x` + `-n` + multi-file | fold, full-line, then `file:lineno:line` |
| `-l` after first hit | emit name once; may `break` inner loop |
| `-v` with no inverted hits | file contributes nothing (`-l` does not print it) |
| Single-file search never prefixes `filename:` on content lines |
| `len(files) > 1` always prefixes, even if only one file has hits |
| Pattern contains regex metacharacters | literal; `in`/`==` |
| Preserve internal spaces and punctuation on the line |

## Out of scope

- Regex, `-r` recursion, stdin, exit codes, color, binary files.
- Clustered flags (`-nix`), long options.
- Writing files, mutating fixtures, importing third-party packages.

## Verification the implementer should run

After coding `grep.py` only:

```text
python -m unittest public_test.py
```

Public test covers one-file / one-match / no flags. The design above is the full flag/format matrix the rest of the suite exercises; implement all of it in the first cut (do not special-case the single public example).
