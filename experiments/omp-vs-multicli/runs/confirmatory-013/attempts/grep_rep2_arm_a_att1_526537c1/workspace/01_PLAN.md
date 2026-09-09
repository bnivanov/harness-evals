# grep.py implementation guide

Implement `grep(pattern, flags, files) -> str` in `grep.py` only. Fixed-string search (not regex). Match Unix-grep output conventions used by the Exercism-style tests.

## Contract

```python
def grep(pattern, flags, files):
    """Return matching lines as a single string.

    pattern: str — literal search string
    flags:   str | iterable[str] — see Flag parsing
    files:   list[str] — paths, searched in given order
    """
```

Return value is the concatenation of result rows, each terminated by `\n`. No matches → `""` (not a lone newline).

Files are read with the builtin `open` **as a name looked up in the `grep` module** (`open(path)` or `open(path, "r")` inside `grep.py`). Tests patch `grep.open`. Do not use `io.open`, `pathlib`, or a local alias that bypasses that lookup.

## Data structures

Keep it boring. No classes.

| Name | Type | Role |
|---|---|---|
| `opts` | `set[str]` | Flag letters present, e.g. `{"n", "i"}` |
| `pattern` | `str` | Search needle; if `-i`, compare via `.lower()` copies, do not mutate the original used for output |
| `files` | `list[str]` | Search order; `multi = len(files) > 1` controls filename prefix |
| `out` | `list[str]` | Result rows **without** trailing `\n` |
| per-file lines | iterator of `str` | Raw lines from `open`; strip at most one trailing `\n` (and `\r` if present) for matching/output body |

Line numbers are 1-based integers, stringified only when formatting `-n` output.

## Flag parsing

Public test passes `flags=""`. Hidden tests may pass `"-n"`, `"-n -i"`, `"-nxi"`, or a list like `["-n", "-i"]`. Parse all of those:

1. Falsy (`""`, `[]`, `None`) → empty set.
2. `str` → `flags.split()` (whitespace-separated tokens).
3. Otherwise treat as an iterable of tokens.
4. For each token, if it starts with `-`, take `token[1:]`; else take the token. Add every remaining character to the set.

Recognized letters: `n`, `l`, `i`, `v`, `x`. Ignore anything else. Duplicates are harmless because of `set`.

## Matching

Work on the line body with the line terminator removed (`line.rstrip("\n").rstrip("\r")` or `line[:-1] if line.endswith("\n")` plus optional `\r`). Never use `re`.

Let `hay`, `needle` be the line body and pattern, both `.lower()`’d when `i in opts`.

- Default: `needle in hay` (substring; empty pattern matches every line).
- `-x`: `hay == needle` (whole line; empty pattern matches only empty lines).
- `-v`: invert the boolean from the chosen comparison **after** `-i`/`-x` are applied.

`-i` + `-x` is case-insensitive equality. `-v` + `-x` inverts whole-line match. `-v` + `-i` inverts the case-insensitive substring/equality test.

## Per-file algorithm

```
opts = parse(flags)
multi = len(files) > 1
out = []

for path in files:
    with open(path) as fh:          # must be grep.open
        enumerate lines starting at 1
        for each line:
            body = strip one trailing newline
            hit = match(body, pattern, opts)
            if v: hit = not hit
            if not hit: continue
            if l in opts:
                out.append(path)
                stop scanning this file
            else:
                out.append(format_row(path, lineno, body, multi, n in opts))
return "".join(row + "\n" for row in out)
```

Scan files in list order. Within a file, emit matches in file order. `-l` emits each matching file at most once, then moves to the next file.

### Row format (non-`-l`)

Join with `:` (no spaces):

| | single file (`len(files)==1`) | multiple files |
|---|---|---|
| no `-n` | `{body}` | `{path}:{body}` |
| `-n` | `{lineno}:{body}` | `{path}:{lineno}:{body}` |

Filename prefix depends on **how many files were requested**, not how many produced hits. One requested file never gets a `path:` prefix, even if that is surprising.

`-l` **wins** over `-n`: output is only `{path}` per matching file, never line numbers or bodies. `-l` still respects `-i`/`-v`/`-x` for whether the file counts as a match.

Original line text is the body only (terminator stripped). Always re-terminate result rows with `\n`. Do not preserve a missing final newline from the source file in the output row.

## Edge cases

- **No hits:** `""`.
- **Empty pattern:** substring match hits every line; with `-x`, only empty bodies; with `-v`, the complement.
- **Empty line in file:** `"\n"` in the file is body `""`.
- **File ends with `\n`:** `readlines()` / iteration does not invent an extra empty line after the last terminator.
- **File with no trailing newline on last line:** still a candidate line; output row still ends with `\n`.
- **`-l` + `-v`:** file is listed if it contains at least one **non**-matching line (invert, then “any hit”).
- **`-l` + file with no qualifying line:** omit the file.
- **Several matches, one file:** all rows, order preserved.
- **Literal special characters in pattern:** `in` / `==`, never regex.
- **Case:** only `-i` folds case; default is case-sensitive.
- **Unknown flags / extra spaces:** ignore.
- **Missing file:** let `open` raise (tests mock known names).
- **`files` empty:** return `""` (not required by README; cheap).

Do not print, log, or write files. Do not mutate `files` or caller-owned strings.

## Structure in `grep.py`

Three small functions, one module, no extra files:

1. `_parse_flags(flags) -> set[str]`
2. `_is_match(body, pattern, opts) -> bool` — applies `-i` and `-x` only; caller applies `-v`
3. `grep(pattern, flags, files) -> str` — I/O, `-l` short-circuit, formatting

No regex, no third-party imports. `open` as a bare global in this module.

## Verification (for the implementer; planner does not run/edit tests)

Public: `grep("Agamemnon", "", ["iliad.txt"])` → `"Of Atreus, Agamemnon, King of men.\n"` using the mocked `iliad.txt`.

Manually reason through: `-n` line numbers 1-based; two files prefix `iliad.txt:`; `-l` returns `"iliad.txt\n"` and stops after first hit; `-i` matches `agamemnon`; `-x` rejects substring-only lines; `-v` returns the other lines of the file, still newline-terminated.
