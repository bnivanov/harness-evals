# grep.py implementation guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: fixed string (not a regex). Match with substring/`==`, never `re`.
- `flags`: a single string of zero or more space-separated tokens (`""`, `"-n"`, `"-n -i"`, `"-l -x -v"`, …). Presence is `"-n" in flags` (and likewise for `-l`, `-i`, `-v`, `-x`). Order of tokens does not matter. Combined short flags (`"-ni"`) are not required; still, `"in"` membership works for the documented spaced form.
- `files`: one or more file names, searched in list order.
- Return: one output record per result, each terminated by `\n`. No matches → `""`. Never `None`.

Tests patch `grep.open`, so read files with the builtin `open(filename)` (text mode). Do not use `pathlib`, `io.open`, or a different module’s `open`.

## Output shape

Build a list of record strings (no trailing newline on the record itself), then:

```python
return "".join(record + "\n" for record in records)
```

Record format depends on flags and how many files were passed (the original `files` length, not how many matched):

| Mode | Single file (`len(files) == 1`) | Multiple files |
|---|---|---|
| default | `{line}` | `{filename}:{line}` |
| `-n` | `{n}:{line}` | `{filename}:{n}:{line}` |
| `-l` | `{filename}` | `{filename}` |

- Line numbers are **1-based** and counted over every physical line in the file, including lines that do not match.
- Filename, if present, comes first; then line number (if `-n`); then the line text. Join those parts with `:`.
- `-l` wins over `-n` and over line text: emit each matching file name **once**, then stop reading that file.
- `-l` still uses the same “did this file produce at least one selected line?” predicate as the line-oriented modes (after `-i`/`-x`/`-v`).

## Line reading

```python
with open(filename) as fh:
    text = fh.read()
lines = text.splitlines()
```

- `splitlines()` (no `keepends`): drops the terminator, keeps genuine empty lines, does not invent a trailing empty line after a final `\n`.
- Do **not** use `str.split("\n")` (`"a\nb\n"` would yield a spurious `""`).
- Match against the terminator-stripped line. Re-attach `\n` only when joining records.
- Preserve interior spaces and punctuation exactly; do not strip.

Fixture files in the public tests end with `\n` and use Unix newlines. `splitlines()` is still the right splitter if a file has no final newline.

## Match predicate

Given stripped `line` and `pattern`:

1. If `-i`: compare with `casefold()` (ASCII-safe; also correct if a later test uses non-ASCII). Apply to both sides. Do not use `re.IGNORECASE`.
2. If `-x`: selected iff `haystack == needle`.
3. Else: selected iff `needle in haystack`.
4. If `-v`: invert the boolean from step 2/3. `-v` applies **after** `-i` and `-x`, not instead of them.

Empty `pattern`:
- without `-x`: every line matches (`"" in line` is true), so `-v` selects nothing.
- with `-x`: only empty lines match.

Literal meaning: characters like `.`, `*`, `[` in `pattern` are ordinary text.

## Algorithm

Parse four booleans once from `flags`: `n_flag`, `l_flag`, `i_flag`, `v_flag`, `x_flag`.

```
records = []
multi = len(files) > 1

for filename in files:
    with open(filename) as fh:
        lines = fh.read().splitlines()
    for lineno, line in enumerate(lines, start=1):
        haystack = line.casefold() if i_flag else line
        needle = pattern.casefold() if i_flag else pattern
        hit = (haystack == needle) if x_flag else (needle in haystack)
        if v_flag:
            hit = not hit
        if not hit:
            continue
        if l_flag:
            records.append(filename)
            break
        parts = []
        if multi:
            parts.append(filename)
        if n_flag:
            parts.append(str(lineno))
        parts.append(line)
        records.append(":".join(parts))

return "".join(r + "\n" for r in records)
```

Complexity: one pass per file, O(total bytes). No extra indexes.

## Flag combinations (required)

All combinations of `{ -n, -l, -i, -v, -x }` are in scope. Notable interactions:

- `-i -x`: whole-line equality, case-insensitive.
- `-i` without `-x`: case-insensitive substring.
- `-v -x`: lines whose full text is not equal to `pattern` (case-folded if `-i`).
- `-v` without `-x`: lines that do not contain `pattern`.
- `-n -v`: inverted lines, still numbered from the original file (numbers are positions, not a dense 1..k of results).
- `-l -v`: file name if **any** line fails the match (i.e. would be printed under `-v`). A file whose every line matches is omitted.
- `-l -n`, `-l -x`, `-l -i`, `-l -v`: `-l` suppresses numbers and line text.
- `-n` on multiple files: `file:lineno:line`.
- Several matches in one file: emit in file order, no extra separators.
- Several files: concatenate in `files` order. A file with zero selected lines contributes nothing (and does not appear under `-l`).

## Edge cases

- **No matches** (including `-v` when every line matches): `""`.
- **One file vs many**: filename prefix is based on `len(files)`, even if only one file actually matches. `grep(p, "", ["a.txt", "b.txt"])` that hits only `a.txt` still prints `a.txt:...`.
- **`-l` uniqueness**: at most one record per file, first-match short-circuit.
- **Empty file**: `splitlines()` → `[]` → no records (unless we somehow matched; we cannot).
- **Empty line in file**: valid haystack `""`. Matches empty pattern; with `-x` matches only empty pattern; with `-v` included when it fails the predicate.
- **Pattern equals a full line that also appears as a substring of another line**: without `-x` both match; with `-x` only the exact line.
- **Overlapping / repeated files**: if the same name appears twice in `files`, process twice (tests are unlikely to do this; do not uniquify).
- **Missing file**: let `open` raise; tests only open known names.
- **Flags string extra spaces / empty**: `""` and `"   "` → all flags false. Do not require a leading space before the first flag.
- **Do not rstrip output**: last record still ends with `\n`. `assertMultiLineEqual` compares the whole string.
- **Do not add a trailing extra `\n`** beyond one per record.

## Structure in grep.py

Keep a single module-level `grep`. Optional tiny helpers (not required):

- `_parse_flags(flags) -> tuple[bool, bool, bool, bool, bool]`
- `_selected(line, pattern, i_flag, x_flag, v_flag) -> bool`
- `_format(filename, lineno, line, multi, n_flag) -> str`

No classes, no regex, no global mutable state. Do not write files; stdout is unused. The function’s return value is the entire interface.

## Verification (implementer, not this plan)

Public test: `grep("Agamemnon", "", ["iliad.txt"])` → `"Of Atreus, Agamemnon, King of men.\n"` with `open` mocked.

After implementation, that case plus the behaviors above (single/multi file, each flag, inversions, whole-line, case-fold, `-l` short-circuit, numbering) must hold. Do not add tests in this task.
