# grep.py Implementation Plan

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: fixed string (not a regex). Match is substring containment unless `-x`.
- `flags`: space-separated token string, e.g. `""`, `"-n"`, `"-n -i -x"`. Unknown tokens ignored if any appear; expected set is `-n -l -i -v -x`.
- `files`: one or more filenames, searched in list order.
- Return: concatenation of result lines. Every emitted line ends with `\n`. No match → `""`.

Public test: `grep("Agamemnon", "", ["iliad.txt"])` → `"Of Atreus, Agamemnon, King of men.\n"`.

I/O: call builtin `open(filename)` (tests patch `grep.open`). Do not import extra I/O helpers. Use `with open(fname) as f:` and iterate lines.

## Flag parse

Split `flags` on whitespace. Store booleans:

| flag | meaning |
|------|---------|
| `-n` | prepend 1-based line number |
| `-l` | emit each matching **filename** once, not line text |
| `-i` | case-insensitive compare |
| `-v` | invert: keep lines that **fail** the match |
| `-x` | whole-line equality instead of substring |

Flags compose. `-l` dominates output shape (no line text, no line numbers). `-n` still applies when not `-l`.

## Match predicate

Normalize once:

```
needle = pattern.lower() if case_insensitive else pattern
```

For each raw file line:

1. Strip at most one trailing `\n` (and `\r` if present: `line.rstrip("\n").rstrip("\r")` or `line.splitlines()[0] if line else ""`). Keep interior whitespace. Do **not** strip leading/trailing spaces — they are part of the line for `-x` and output.
2. `hay = text.lower() if case_insensitive else text`
3. `matched = (hay == needle) if whole_line else (needle in hay)`
4. `keep = (not matched) if invert else matched`

Empty `pattern`: `"" in hay` is True for every line; with `-x`, only a truly empty line matches.

## File loop

```
results = []
multi = len(files) > 1

for fname in files:
    with open(fname) as fh:
        for lineno, raw in enumerate(fh, start=1):
            text = strip_one_newline(raw)
            if not keep(text):
                continue
            if list_files:
                results.append(fname)
                break          # this file is done
            parts = []
            if multi:
                parts.append(fname)
            if numbered:
                parts.append(str(lineno))
            parts.append(text)
            results.append(":".join(parts))
return "".join(line + "\n" for line in results)
```

### Output shapes

| condition | format per hit |
|-----------|----------------|
| 1 file, no `-n`, no `-l` | `{line}\n` |
| 1 file, `-n` | `{lineno}:{line}\n` |
| N>1 files, no `-n`, no `-l` | `{file}:{line}\n` |
| N>1 files, `-n` | `{file}:{lineno}:{line}\n` |
| `-l` (1 or N files) | `{file}\n` once per file with ≥1 kept line |

Colon joins filename, optional number, then the line body. Number sits after filename when both present (`-n` + multiple files).

## Edge cases

- **No matches / all inverted away**: `""`.
- **Several matches in one file**: emit in file order; do not dedupe lines.
- **`-l` + `-v`**: file is listed if it has at least one non-matching line (including empty files? empty file has no lines → not listed).
- **`-l` + `-n`**: `-l` wins; numbers omitted.
- **`-i` + `-x`**: fold case, then full-line equality.
- **`-v` + `-x`**: keep lines that are not exactly the pattern.
- **Last line without newline in file**: still emit with trailing `\n` in the return value.
- **Pattern with spaces / punctuation**: literal; no regex metacharacters.
- **File order**: results follow `files` order, then line order inside each file.
- **Missing file**: not specified; let `open` raise (tests only open known names).
- **Single-file search never prefixes filename**, except under `-l`.

## Structure (keep grep.py small)

One module-level `grep`. Optional tiny helpers in the same file:

- `_parse_flags(flags) -> frozenset[str]` or a 5-tuple of bools
- `_matches(text, pattern, *, ignore_case, whole_line) -> bool`

No classes. No regex. No third-party imports.

## Verification (implementer)

Run `python -m unittest public_test.py`. The checked-in suite has one case; behavior above is the full README contract and must hold for combinations of all five flags, one and many files, zero/one/many hits.
