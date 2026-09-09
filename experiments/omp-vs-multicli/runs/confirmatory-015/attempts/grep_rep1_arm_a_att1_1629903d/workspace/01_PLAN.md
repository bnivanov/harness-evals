# grep.py — Implementation Guide

Implement `grep(pattern, flags, files)` in `grep.py` only. Do not touch tests.

This is Exercism “grep”: **fixed-string** search (not regex), POSIX-ish output. Held-out tests cover every flag combo, single vs multiple files, and invert/exact/case-insensitive matching. Public test is only `grep("Agamemnon", "", ["iliad.txt"])`.

---

## 1. Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

| Arg | Shape | Notes |
|---|---|---|
| `pattern` | `str` | Literal substring (or whole line if `-x`). Never a regex. |
| `flags` | `str` | Space-separated tokens, e.g. `""`, `"-n"`, `"-n -i"`, `"-l -x -i"`. |
| `files` | `list[str]` | One or more filenames, search **in list order**. |

**Return:** one string. Matching output lines concatenated, **each ending in `\n`**. No matches → `""` (not `None`, not `"\n"`).

Tests `assertMultiLineEqual` against this string.

---

## 2. Hard constraint: `open`

Tests patch **`grep.open`**:

```python
@mock.patch("grep.open", ..., create=True)
```

- Read files with the builtin **`open(filename)`** inside `grep.py`.
- `with open(fname) as fh:` then iterate lines (or `.read()` / `.readlines()`).
- **Do not** use `pathlib`, `io.open`, or any other reader — they bypass the mock and fail.
- Do not catch “missing file”: the mock raises if the name is unknown.

File contents in tests always use `\n` line endings and a trailing newline on the last line.

---

## 3. Flag parsing

`flags` is a **string**, not a list.

```python
flag_set = set(flags.split())
```

`"".split()` → `[]` → empty set. Never `set(flags)` (that splits characters).

Recognized tokens (each independently present or absent):

| Flag | Meaning |
|---|---|
| `-n` | Prepend 1-based line number and `:` |
| `-l` | Emit **file names only** (one per file that has ≥1 selected line) |
| `-i` | Case-insensitive compare |
| `-v` | Invert: select lines that **fail** the match |
| `-x` | Match **entire line**, not substring |

Unknown flags will not appear. Order in the string does not matter. Duplicates do not matter.

**Precedence:** `-l` **wins over** `-n` (and over filename:line formatting). If `-l` is set, output is only `filename\n` per matching file — no line text, no line numbers.

---

## 4. Matching (per line)

Work on the line **without** its trailing newline (and optional `\r`):

```text
text = line.rstrip("\n").rstrip("\r")   # or line.rstrip("\r\n")
```

Do **not** strip leading/trailing spaces; they are significant for `-x`.

Let `needle = pattern`. If `-i`, compare using a case-folded copy of both sides (`.lower()` is enough; tests are ASCII). **Never mutate the original line** — output must keep original casing and spacing.

Match predicate:

```text
if -x:
    matched = (folded_text == folded_needle)
else:
    matched = (folded_needle in folded_text)   # substring, not regex
```

Then:

```text
selected = (not matched) if -v else matched
```

Empty `pattern`:

- without `-x`: empty string is a substring of every line → every line matches (unless `-v`).
- with `-x`: only empty lines match.

Literal metacharacters (`.*[]` etc.) are ordinary characters. Use `in` / `==` only — no `re`.

---

## 5. Output format

Let `multi = len(files) > 1`. Filename prefix depends on how many files were **passed**, not how many actually matched.

### 5.1 `-l` (names only)

For each file that has **at least one selected line**, append:

```text
{filename}\n
```

Stop scanning that file after the first selected line. Do not emit `:` or line numbers. File order = `files` order. Each name once.

### 5.2 Normal line output (no `-l`)

For every selected line, append:

```text
{prefix}{original_line_including_newline}
```

`prefix` concatenation order:

1. If `multi`: `{filename}:`
2. If `-n`: `{line_number}:`  (1-based, counts **all** physical lines, including non-selected)

Examples (single file `iliad.txt`):

| Flags | Example line |
|---|---|
| none | `Of Atreus, Agamemnon, King of men.\n` |
| `-n` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `-l` | `iliad.txt\n` |

Same match, **two or more files** in `files`:

| Flags | Example line |
|---|---|
| none | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `-n` | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |
| `-l` | `iliad.txt\n` |

If a source line already ends with `\n`, do not add another. If a last line has no newline, still terminate the output record with `\n` (tests always include the newline).

Preserve the original line body exactly (after any `rstrip` used only for matching). Easiest: iterate `for line in fh` and, when selected, emit `prefix + line` when `line.endswith("\n")` else `prefix + line + "\n"`.

---

## 6. Algorithm

```
parse flags into booleans: n, l, i, v, x
multi = len(files) > 1
chunks = []

for each filename in files:                  # given order
    with open(filename) as fh:
        for lineno, line in enumerate(fh, start=1):
            if not selected(line, pattern, i, v, x):
                continue
            if l:
                chunks.append(filename + "\n")
                break
            prefix = ""
            if multi:
                prefix += filename + ":"
            if n:
                prefix += str(lineno) + ":"
            chunks.append(prefix + ensure_newline(line))

return "".join(chunks)
```

Complexity: O(total bytes). No extra data structures beyond a list of output fragments (or concatenate as you go).

---

## 7. Edge cases (held-out coverage)

Implement all of these; public_test.py only checks one.

1. **Several matches in one file** — all selected lines, file order, no extra blanks.
2. **No matches** — `""`.
3. **`-i`** — `Agamemnon` matches `agamemnon`; output original text.
4. **`-x`** — substring-only lines must **not** match; exact full-line must.
5. **`-x -i`** — full-line compare, ignore case.
6. **`-v`** — every non-matching line; with `-x`, invert the exact-line test.
7. **`-v -x`** — exclude only exact (possibly case-folded) lines.
8. **`-n` + several matches** — numbers are physical indices (`2:`, `6:`, …), not 1..k among hits.
9. **`-l` + `-n`** — names only (`-l` wins). Canonical: “file flag takes precedence over line number flag”.
10. **`-l` + `-i` / `-x` / `-v`** — name emitted iff the file has ≥1 line that survives those match rules.
11. **Multiple files, one match** — still prefix `filename:` on that one line (because `len(files) > 1`).
12. **Multiple files, several matches** — prefix every line; files in argument order; lines in file order.
13. **Multiple files, `-l`** — one name per matching file, each with `\n`.
14. **Multiple files, no matches** — `""`.
15. **Same line matching rules across files** — no global state; reset line numbers per file.
16. **Pattern with spaces** — `pattern` is the whole string; do not split it. Flags are the only space-separated field.

---

## 8. Suggested shape in `grep.py`

Keep it boring: one public function, two tiny helpers.

```python
def grep(pattern, flags, files):
    ...

def _parse_flags(flags: str) -> ...:
    # returns booleans or a small namespace/tuple

def _line_selected(line: str, pattern: str, ignore_case: bool, invert: bool, exact: bool) -> bool:
    ...
```

No classes, no regex, no argparse, no third-party imports. Stdlib only if you want (`dataclasses` optional; not needed).

Do not print. Do not write files. Return the string.

---

## 9. Invariants

- Search is **literal**. `pattern in text` / `==`.
- Line numbers are **1-based** and count every line in the file.
- Filename colon appears iff **more than one file argument** and **not** `-l`.
- `-n` colon is after the filename colon when both apply: `file:N:line`.
- `-l` short-circuits per file after first hit.
- Original line text (case, punctuation) is what gets printed.
- Final return is `str`; last character is `\n` iff there was at least one output record.

---

## 10. Verification (implementer)

After coding `grep.py`:

```text
python -m unittest public_test.py
```

That only proves the no-flag single-file path. Mentally / with a local scratch script **inside this directory only** you may exercise:

- `grep("Agamemnon", "-n", ["iliad.txt"])` → `9:Of Atreus, Agamemnon, King of men.\n`
- `grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])` → `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
- `grep("Agamemnon", "-l", ["iliad.txt"])` → `iliad.txt\n`

Do **not** edit `grep.py` in the planning phase. Do **not** add tests. Do **not** fetch canonical-data.json or other repos.

---

## 11. Non-goals

- Regex, PCRE, `re.escape`.
- Recursive directory walk, stdin, binary files.
- Flag clustering (`-nlx`); tests pass **separate** tokens in one string.
- Locale-aware case folding beyond `.lower()` on the ASCII fixtures.
- Color, context lines (`-A/-B/-C`), count-only (`-c`) — not in this exercise.
