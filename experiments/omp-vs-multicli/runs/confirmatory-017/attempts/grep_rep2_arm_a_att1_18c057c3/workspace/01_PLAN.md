# grep.py Implementation Guide

## Goal

Implement `grep(pattern, flags, files) -> str` in `grep.py`.

Search one or more files for lines that contain a **fixed string** (not a regex). Return the matching lines as a single string, in file order then line order, formatted according to flags and whether multiple files were searched.

Do not print. Do not use the `re` module. The public tests mock `grep.open`, so file I/O must go through the builtin `open` referenced from the `grep` module.

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

| Arg | Meaning |
|---|---|
| `pattern` | Literal search string. May be empty. Never treated as a regex. |
| `flags` | Space-separated flag tokens, or `""`. Example: `""`, `"-n"`, `"-n -i"`, `"-x -i -v"`. |
| `files` | One or more filenames, in search order. |

Return value: concatenation of output lines, each terminated by `\n`. No match → `""`.

## Flags

Parse once:

```python
flag_set = set(flags.split())  # "" → empty set
```

Membership tests: `"-n" in flag_set`, etc. Do not use `" -n" in flags` (fails for a lone `"-n"`). Combined glued tokens like `"-ni"` are out of scope; tokens are space-separated.

| Flag | Effect |
|---|---|
| `-n` | Prefix each content line with `N:` where `N` is the 1-based line number in that file. |
| `-l` | Emit only the filename of each file that has at least one selected line. One name per such file, then stop reading that file. |
| `-i` | Case-insensitive match (`str.lower()` on both sides is enough; inputs are ASCII). |
| `-v` | Invert: select lines that **fail** the match predicate. |
| `-x` | Match the **entire** line (equality), not a substring. |

Match flags (`-i`, `-v`, `-x`) compose. Output flags: `-l` wins over `-n` (and over filename/content formatting). `-n` still uses original file line numbers when mixed with `-v`.

## Matching

Strip only a trailing `\n` before comparing. Keep trailing spaces/tabs; they matter for `-x`.

```
text = raw_line.rstrip("\n")
hay, needle = text, pattern
if -i:
    hay, needle = hay.lower(), needle.lower()
matched = (hay == needle) if -x else (needle in hay)
selected = (not matched) if -v else matched
```

Empty `pattern`:

- without `-x`: every line is a substring match (`"" in s` is true).
- with `-x`: only an empty line matches.

Literal search: characters like `. * [ ]` are ordinary text.

## Output format

Build each emitted line as `prefix + body + "\n"`.

**`-l`:** body is unused. Emit `filename + "\n"` once per file that has ≥1 selected line. No line numbers, no content, no extra colon. Same for one file or many.

**Otherwise:**

```
prefix parts, in order:
  1. filename   — only if len(files) > 1
  2. line number as decimal — only if -n
join parts with ":" and append ":" if parts is non-empty
body = text (newline already stripped)
```

Examples (from README + public test):

| Situation | Output line |
|---|---|
| 1 file, no flags | `Of Atreus, Agamemnon, King of men.\n` |
| 1 file, `-n` | `9:Of Atreus, Agamemnon, King of men.\n` |
| ≥2 files, no flags | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| ≥2 files, `-n` | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |
| `-l` (any file count) | `iliad.txt\n` |

Filename prefix depends on `len(files)`, not on how many files actually produced hits.

Always append `\n` to every emitted record, including the last. Do not wrap with an extra trailing newline beyond that.

## Algorithm

```
parse flags into booleans: numbered, files_only, insensitive, invert, exact
multi = len(files) > 1
out = []

for filename in files:                          # given order
    with open(filename) as fh:                  # must be grep.open / builtin open
        for lineno, raw in enumerate(fh, start=1):
            text = raw.rstrip("\n")
            if selected(text, pattern, flags):
                if files_only:
                    out.append(filename + "\n")
                    break                       # rest of this file unused
                prefix = []
                if multi:
                    prefix.append(filename)
                if numbered:
                    prefix.append(str(lineno))
                if prefix:
                    out.append(":".join(prefix) + ":" + text + "\n")
                else:
                    out.append(text + "\n")

return "".join(out)
```

Helpers (keep them small; no extra files):

- `_parse_flags(flags: str) -> set[str]` or a tiny namespace/tuple of booleans.
- `_matches(text, pattern, insensitive, exact) -> bool` — the pre-invert predicate.

Stay in one module. No classes required.

## I/O and tests

Public tests patch `grep.open` with `create=True` and feed in-memory `io.StringIO` keyed by filename. Therefore:

- Call `open(filename)` (text mode, default encoding). Do not use `pathlib.Path.read_text`, `io.open` via another name, or pre-read caches.
- Iterate the file object; do not require a real filesystem.
- Unknown names in the mock raise `RuntimeError`; do not invent fallbacks.

Given fixture files (for reasoning, not to hard-code):

- `iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt` — each a trailing-newline-terminated poem. Last physical line still includes `\n`, so `for line in f` yields `\n`-terminated strings.

Public case already specified:

```python
grep("Agamemnon", "", ["iliad.txt"])
# == "Of Atreus, Agamemnon, King of men.\n"
```

## Edge cases

1. **No hits** — return `""`, not `"\n"`.
2. **Several hits in one file** — emit all, in file order (unless `-l`, then one filename).
3. **Several files** — scan in list order; concatenate. A miss in file *i* does not skip later files.
4. **`-l` + multiple matches in one file** — one filename, then next file.
5. **`-l` + `-v`** — file is listed if it has at least one line that does **not** match the pattern.
6. **`-l` + `-n`** — `-l` only; drop numbers.
7. **`-v` + `-n`** — numbers are original 1-based indices of the non-matching lines.
8. **`-v` + `-x`** — select lines that are not exactly the pattern.
9. **`-i` + `-x`** — whole-line equality after lowercasing both sides.
10. **`-i` substring** — `"OF"` matches `"Of Mans First Disobedience, and the Fruit"`.
11. **Single-file vs multi-file prefix** — `len(files) == 1` never prefixes filename, even if that file has hits and others (none) were not passed. Passing two files always prefixes, even if only one file hits.
12. **Line numbering** — count every physical line, including those rejected by the predicate.
13. **Trailing whitespace** — part of the line; `-x` does not strip it.
14. **Missing final newline in a file** — `rstrip("\n")` is a no-op; still emit with `\n`.
15. **Empty files list** — return `""` (README says one or more; still be total).
16. **Do not mutate** `files` or `flags`.

## Non-goals

- Regex, recursive directory walk, stdin (`-`), binary files, color, context (`-A/-B/-C`), count-only (`-c`) except as implied by `-l`.
- Writing files, logging, CLI `argparse` / `sys.argv`. Library function only.
- Extra dependencies.

## Verification (for the implementer)

After coding `grep.py` only:

```text
python -m unittest public_test.py
```

Must pass `test_one_file_one_match_no_flags`. Hidden tests will cover flag combinations, multi-file prefixes, inversion, and `-l` short-circuit output. Do not add or edit tests.

## Suggested shape of `grep.py`

```python
def grep(pattern, flags, files):
    flag_set = set(flags.split())
    numbered = "-n" in flag_set
    files_only = "-l" in flag_set
    insensitive = "-i" in flag_set
    invert = "-v" in flag_set
    exact = "-x" in flag_set
    multi = len(files) > 1
    out = []
    for filename in files:
        with open(filename) as fh:
            for lineno, raw in enumerate(fh, 1):
                text = raw.rstrip("\n")
                hay, needle = text, pattern
                if insensitive:
                    hay, needle = hay.lower(), needle.lower()
                matched = hay == needle if exact else needle in hay
                if invert:
                    matched = not matched
                if not matched:
                    continue
                if files_only:
                    out.append(f"{filename}\n")
                    break
                prefix = []
                if multi:
                    prefix.append(filename)
                if numbered:
                    prefix.append(str(lineno))
                if prefix:
                    out.append(f"{':'.join(prefix)}:{text}\n")
                else:
                    out.append(f"{text}\n")
    return "".join(out)
```

This is the complete intended implementation. Keep behavior identical; helpers are optional.
