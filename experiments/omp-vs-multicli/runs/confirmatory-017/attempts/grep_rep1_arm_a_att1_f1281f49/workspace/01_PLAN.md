# grep.py — Implementation Guide

## Contract

```python
def grep(pattern, flags, files) -> str:
```

- `pattern`: fixed string (not a regex). Literal substring / whole-line match only.
- `flags`: a single string of zero or more space-separated options (`""`, `"-n"`, `"-n -i"`, …).
- `files`: non-empty list of path strings, searched in list order.
- Return: one string of selected output lines, each terminated by `\n`. No matches → `""` (never `None`).

The public suite patches `grep.open`. Call the builtin `open()` from this module (text mode, default encoding). Do not use `pathlib`, `io.open` bound elsewhere, or a pre-imported `open` alias that would miss the patch.

Files in `public_test.py` are Shakespeare/Milton excerpts ending with a trailing newline. Treat that as the normal case; still handle a missing final newline.

## Flags

Parse with `flags.split()` → a set. Presence of the token is enough (`"-n" in flagset`). Unknown tokens: ignore (none appear in tests).

| Flag | Effect |
|------|--------|
| `-i` | Case-insensitive match (`str.lower()` on both pattern and line text). |
| `-x` | Whole-line match: equality after optional case-fold, not substring. |
| `-v` | Invert: keep lines that **fail** the (possibly `-i`/`-x`) match. |
| `-n` | Prefix **1-based** physical line number and `:` on each content line. |
| `-l` | Print each matching **file name once**, not line contents. |

Combinations are orthogonal except `-l` suppresses content/`-n` formatting.

Match predicate (before `-v`):

```
haystack = line.lower() if -i else line
needle   = pattern.lower() if -i else pattern
ok = (haystack == needle) if -x else (needle in haystack)
if -v: ok = not ok
```

Apply `-v` **after** `-i`/`-x`. Empty `pattern`: substring-matches every line; with `-x`, only empty lines.

## Line I/O

For each `filename` in `files`, in order:

```python
with open(filename) as fh:
    for lineno, raw in enumerate(fh, start=1):
        line = raw.rstrip("\n")   # not str.rstrip() — keep trailing spaces
        ...
```

- Matching and output use `line` **without** the terminator.
- Line numbers count every physical line, including those dropped by `-v`.
- Do not interpret regex metacharacters in `pattern`.

## Output format

`multi = len(files) > 1`. Filename prefixes apply only when `multi` is true, **except** `-l` (always names).

**Content mode** (`-l` absent). For each selected line, join with `:` then append `\n`:

| | single file | multiple files |
|--|--|--|
| no `-n` | `{line}\n` | `{filename}:{line}\n` |
| `-n` | `{lineno}:{line}\n` | `{filename}:{lineno}:{line}\n` |

Order: filename, then line number, then text. Never a space after `:`.

**Name mode** (`-l` present): on the first selected line in a file, emit `{filename}\n` and skip the rest of that file. Files with zero selected lines emit nothing. `-n` is ignored. `-v` still defines “selected”.

Concatenate in discovery order. No extra trailing newline beyond the last `\n` of the last record.

## Algorithm

```
parse flags
results = []
multi = len(files) > 1

for filename in files:
    with open(filename) as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not selected(line, pattern, flags):
                continue
            if -l:
                results.append(filename + "\n")
                break
            parts = []
            if multi:
                parts.append(filename)
            if -n:
                parts.append(str(lineno))
            parts.append(line)
            results.append(":".join(parts) + "\n")

return "".join(results)
```

Helpers worth extracting (keep in `grep.py`, no extra modules):

- `_parse_flags(flags: str) -> set[str]`
- `_matches(line, pattern, insensitive: bool, exact: bool) -> bool`

Keep `grep()` as the only public name.

## Edge cases

1. **No matches** — `""`.
2. **Several matches, one file** — all matching lines, file order, no filename prefix.
3. **Several files** — prefix every content line with `filename:`; files with no hits contribute nothing.
4. **`-i`** — `Agamemnon` matches `agamemnon`; `-x -i` is case-folded equality.
5. **`-x`** — `"Fruit"` does not match `"… Fruit"`; whole line must equal pattern (minus newline).
6. **`-v`** — emit non-matching lines; with `-x`, emit lines that are not exactly the pattern.
7. **`-n`** — 1-based; inverted lines keep original numbers.
8. **`-l`** — one name per file that has ≥1 selected line; single-file still prints the name.
9. **`-l -v`** — name if the file has ≥1 non-matching line; a file whose every line matches is omitted.
10. **`-l -n`** — names only; no numbers.
11. **`-n -i -x`** (and other stacks) — all active; format from `-n`/`multi`, predicate from `-i`/`-x`.
12. **Literal pattern** — `.`, `*`, `[` are ordinary characters (`"in"` / `==`, not `re`).
13. **Last line without `\n`** — still a line; output record still ends with `\n`.
14. **Flags string** — `""`, `"-n"`, `"-n -l -i"`; `split()` handles extra spaces.
15. **File order** — never sort; honor `files` and in-file order.

## Verification (implementer)

Do not edit `public_test.py`. After implementing `grep.py`:

```
python -m unittest public_test.py
```

Public coverage is one case (`Agamemnon` in `iliad.txt`, no flags). The rest of the design is required for the full flag/file matrix above.

## Out of scope

- Regex, recursive directories, stdin, binary files, color, context (`-A`/`-B`/`-C`).
- New files, tests, or comments that restate the README.
- Accessing canonical-data, held-out tests, or anything outside this workspace.
