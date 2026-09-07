# grep.py Implementation Guide

Implement `grep(pattern, flags, files)` in `grep.py` only. Do not change tests.

Source of truth: `README.md` + `public_test.py`. Held-out tests are generated from Exercism `canonical-data.json` (2023-07-19) and will exercise every flag, flag combination, single- vs multi-file output, and no-match cases. Cover all of that here even though `public_test.py` only contains one case.

## Contract

```python
def grep(pattern, flags, files):
    ...
```

| Arg | Type | Meaning |
|---|---|---|
| `pattern` | `str` | Fixed string (not a regex). |
| `flags` | `str` | Zero or more flags, space-separated. Empty string `""` means none. |
| `files` | `list[str]` | One or more filenames, in search order. |

Return: a single `str`. Each emitted record ends with `\n`. No matches → `""` (not `"\n"`). Never print; never write files.

Public test (must pass as written):

```python
grep("Agamemnon", "", ["iliad.txt"])
# == "Of Atreus, Agamemnon, King of men.\n"
```

File I/O is mocked as `grep.open` (`create=True`, `side_effect` returns `io.StringIO`). The implementation **must** call the builtin name `open(...)` inside `grep.py` so the patch applies. Do not use `io.open`, `pathlib`, `__builtins__.open`, or a captured `open` at import time.

## Flags

Parse with `flags.split()` → a set/list of tokens. Recognized tokens:

| Flag | Effect |
|---|---|
| `-n` | Prefix **1-based** line number and `:` before the line text. If a filename prefix is also present, the number goes **after** the filename (README). |
| `-l` | Emit each matching **file name** once, then stop scanning that file. No line text, no line numbers. |
| `-i` | Case-insensitive compare (`str.lower()` on both pattern and line; ASCII test data). |
| `-v` | Invert: select lines that **fail** the match. |
| `-x` | Match the **entire** line, not a substring. |
| (absent) | Substring match, case-sensitive, emit matching line text. |

Unknown tokens: ignore (tests only send the five above).

Multiple flags arrive as one string, e.g. `"-n -i -x"`, `"-n -l"`. Split on whitespace; do not require a particular order.

### Precedence

1. **`-l` wins over `-n` and over line-text formatting.** If `-l` is set, output is only `"{filename}\n"` for each file that has at least one selected line. Do not prefix another copy of the filename; do not include line numbers or content.
2. Match predicate is: start with (`-x` ? full-line equality : substring), apply `-i` to both sides, then invert if `-v`.
3. Filename prefix on **content** lines is independent of `-l`: it applies when `len(files) > 1` and we are emitting line text (not in `-l` mode).

## Match algorithm

Work on the line **without** its trailing newline. Do **not** use `str.strip()` / `rstrip()` of all whitespace: trailing/leading spaces are significant under `-x`. Only strip a terminator:

```python
text = line[:-1] if line.endswith("\n") else line
# equivalently: line.rstrip("\n")  # OK for these fixtures (\n only)
```

```
hay, needle = text, pattern
if ignore_case:
    hay, needle = hay.lower(), needle.lower()
hit = (hay == needle) if exact_line else (needle in hay)
selected = (not hit) if invert else hit
```

- Fixed strings: use `in` / `==`. **Never** `re`. A pattern of `.` or `*` is literal.
- Empty pattern: `"" in hay` is true for every line; `-x` then matches only empty lines. Not in public tests; keep the natural string semantics.
- `-v` inverts the boolean **after** `-x`/`-i`, not before.

## Per-file scan

Process `files` in list order. For each path:

```python
with open(path) as fh:          # mock returns StringIO; context manager is fine
    for lineno, raw in enumerate(fh, start=1):
        text = raw.rstrip("\n")
        if not selected(text):
            continue
        if files_only:          # -l
            emit path + "\n"
            break               # one name per file, first selected line is enough
        emit format_line(...)
```

Line numbers count **every** physical line (1-based), including lines not selected.

Do not assume files exist beyond the mock; do not catch `RuntimeError` from the mock.

## Output format

Let `multi = len(files) > 1`.

### `-l` set

For each file with ≥1 selected line, in file-list order:

```
{filename}\n
```

Same shape for one file or many. A file with zero selected lines contributes nothing.

### `-l` unset (line content)

Each selected line:

```
{filename_prefix}{number_prefix}{text}\n
```

- `filename_prefix` = `"{filename}:"` if `multi` else `""`
- `number_prefix` = `"{lineno}:"` if `-n` else `""`
- `text` is the line **without** the original terminator; we always append exactly one `\n`

Concrete shapes:

| Situation | Record |
|---|---|
| 1 file, no flags | `{text}\n` |
| 1 file, `-n` | `{lineno}:{text}\n` |
| N files, no flags | `{filename}:{text}\n` |
| N files, `-n` | `{filename}:{lineno}:{text}\n` |

Join records with `"".join(...)` (each already has `\n`). Preserve discovery order: file order, then line order within a file.

## Worked examples (from README + public fixtures)

Fixtures are the three poems in `public_test.py` (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`). Each file’s last line includes a trailing `\n`.

1. **Public test.** `pattern="Agamemnon"`, `flags=""`, `files=["iliad.txt"]` → substring on line 9 → `"Of Atreus, Agamemnon, King of men.\n"`.
2. **`-n`, one file.** `"Forbidden"` in `paradise-lost.txt` is line 2 → `"2:Of that Forbidden Tree, whose mortal tast\n"`.
3. **`-i`.** `"FORBIDDEN"` vs that same line → same text, no number.
4. **`-l`, one file.** `"Forbidden"` in `paradise-lost.txt` → `"paradise-lost.txt\n"` (name even for a single file).
5. **`-x`.** Full line `"With loss of Eden, till one greater Man"` matches that line only. `"may"` with `-x` on `midsummer-night.txt` matches nothing (those lines only *contain* `may`).
6. **Combined `-n -i -x`.** Pattern `"OF ATREUS, Agamemnon, KING OF MEN."` on `iliad.txt` → `"9:Of Atreus, Agamemnon, King of men.\n"`.
7. **`-v`.** Select lines where the predicate fails. Example: `"Of"` (case-sensitive substring) on `paradise-lost.txt` drops lines that contain capital `Of`, keeps the rest, still with trailing `\n` on each.
8. **`-n -l`.** `-l` wins: `"ten"` on `iliad.txt` → `"iliad.txt\n"`, not a numbered line.
9. **Multi-file, no flags.** Same Agamemnon search over all three files → `"iliad.txt:Of Atreus, Agamemnon, King of men.\n"` (only one file hits; still prefixed because `len(files) > 1`).
10. **Multi-file `-n`.** `{filename}:{lineno}:{text}\n`.
11. **Multi-file `-l`.** One `{filename}\n` per file that has a selected line, in `files` order.
12. **No matches** (e.g. `"Gandalf"`) → `""`.

## Suggested structure (keep `grep.py` small)

No extra types needed. Booleans from the flag set are enough.

```
parse flags → five booleans
out = []
multi = len(files) > 1
for path in files:
    with open(path) as fh:
        for lineno, raw in enumerate(fh, 1):
            text = raw.rstrip("\n")
            if not line_selected(text, pattern, booleans):
                continue
            if list_files:
                out.append(path + "\n")
                break
            record = text + "\n"
            if show_number:
                record = f"{lineno}:" + record
            if multi:
                record = f"{path}:" + record
            out.append(record)
return "".join(out)
```

Helpers are optional; a single function is fine. Prefer boring string ops.

## Edge cases to handle (do not add extra tests)

| Case | Behavior |
|---|---|
| `flags == ""` | No options. |
| Several matches in one file | All selected lines, in order. |
| `-l` + several matches | Filename once; early `break`. |
| `-l` + `-v` | File is listed if it has ≥1 **non-matching** line (invert applies to selection). |
| `-l` + `-n` | Names only. |
| `-x` + `-i` | Case-fold, then full-line equality. |
| `-x` + `-v` | All lines that are **not** exactly the pattern. |
| One file vs many | Filename prefix only when `len(files) > 1` and not `-l`. |
| Last line with/without `\n` | Compare without terminator; always emit `\n` on output records. |
| Pattern with regex metacharacters | Literal substring. |
| Empty match set | `""`. |

## Non-goals / pitfalls

- Do not compile regexes or call `fnmatch`.
- Do not print to stdout.
- Do not skip the filename prefix when multiple files are passed but only one matches.
- Do not omit the filename under `-l` for a single file.
- Do not `strip()` the whole line.
- Do not 0-index lines.
- Do not insert spaces around `:`.
- Do not add a trailing extra newline after the last record (`join` of records that already end in `\n` is correct; empty `out` stays `""`).
- Do not read files from disk by constructing paths; the mock keys on the filename string as given (`"iliad.txt"`).

## Verification

After implementation (not this planning step):

```text
python -m unittest public_test.py
```

Expect `test_one_file_one_match_no_flags` to pass. Held-out tests will cover the rest of the matrix above; implementing the full matrix is required for those to pass.
