# Implementation Guide: `grep.py`

Implement a simplified, **fixed-string** (not regex) `grep` in `grep.py`. Do **not** edit tests. Do **not** use `re`.

Public contract from `README.md` and `public_test.py`:

```python
def grep(pattern, flags, files) -> str:
    ...
```

- `pattern`: string to search for (literal substring, or entire line when `-x`).
- `flags`: a single string of zero or more space-separated options (e.g. `""`, `"-n"`, `"-n -i -x"`).
- `files`: non-empty list of file path strings, searched **in the given order**.
- Return: one concatenated string of output lines. Each emitted record ends with `\n`. No matches → `""`.

`public_test.py` mocks `grep.open` (and wraps `io.StringIO`). Read files with the builtin `open(...)` inside `grep.py` so the mock applies. Do not use `pathlib`, `io.open`, or other openers.

---

## 1. Architecture

Keep four small pieces. `grep` is the only public function.

```
grep(pattern, flags, files)
  ├─ parse_flags(flags) -> Flags
  ├─ for each filename in files (stable order):
  │     search_file(filename, pattern, flags, prefix_filename)
  │       ├─ open(filename) as text
  │       ├─ for each line (1-based index):
  │       │     line_matches(...)?
  │       │     if -l: emit filename once and stop this file
  │       │     else: format_line(...) and collect
  └─ return "".join(chunks)
```

Suggested helpers (names are not required; behavior is):

| Helper | Responsibility |
| --- | --- |
| `parse_flags(flags)` | Interpret the flags string into booleans. |
| `normalize_line(line)` | Strip at most the line terminator for matching. |
| `line_matches(pattern, text, flags)` | Apply `-i`, `-x`, then `-v`. |
| `format_line(...)` | Build `filename:` / `N:` prefixes and keep the original line body. |
| `search_file(...)` | Scan one file, honor `-l` early-exit. |

Do not share mutable global state. A frozen dataclass / `NamedTuple` for flags is enough.

---

## 2. Data structures

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Flags:
    line_number: bool   # -n
    filename_only: bool # -l
    ignore_case: bool   # -i
    invert: bool        # -v
    exact_line: bool    # -x
```

Parse flags by **whitespace split**, then membership:

```text
tokens = flags.split()          # "" → []
# recognize exactly: -n -l -i -v -x
```

Held-out tests use this shape: `""`, `"-n"`, `"-l"`, `"-i"`, `"-v"`, `"-x"`, and combinations such as `"-n -l"`, `"-n -i -x"`. Extra spaces are harmless because `str.split()` collapses whitespace.

Unknown tokens: ignore them (do not crash). Clustered flags like `-nix` are **not** required.

Collect output in a `list[str]` of complete records (each already ending in `\n`), then `"".join(...)`. Never `print`.

---

## 3. File I/O

```python
with open(filename) as fh:
    for line_no, raw in enumerate(fh, start=1):
        ...
```

- Text mode, default encoding (the tests inject `io.StringIO`).
- Iterate the file object (or `readline` in a loop). Do not read the whole file as one string and `split("\n")` in a way that drops a trailing empty line incorrectly. File iteration is the correct line model.
- Process `files` left to right. Never sort.
- Missing files: let `open` raise. Do not invent error messages.
- Empty file: zero lines → no output for that file (including with `-v`, because there is nothing to invert).

---

## 4. Matching algorithm

For each raw line from the file:

1. **Comparison text** = the line with its terminator removed:

   ```python
   text = raw.rstrip("\r\n")
   ```

   Only strip `\n` / `\r`. Do **not** strip spaces. Leading/trailing spaces are significant for `-x`.

2. **Needle** = `pattern` as given (do not strip it).

3. **Case folding** (only if `-i`): compare `text.casefold()` and `pattern.casefold()` (`.lower()` is acceptable; all fixture text is ASCII). Fold copies only; do not mutate the original line used for output.

4. **Positive match** (before invert):

   | `-x` | Rule |
   | --- | --- |
   | off | `needle in haystack` (literal substring; empty pattern matches every line) |
   | on  | `haystack == needle` (entire comparison text, not including terminator) |

5. **Invert** (if `-v`): `matched = not matched`.

6. `-v` composes with `-i` and `-x` in that order: compute the positive match with `-i`/`-x`, then flip.

This is **not** regex. Characters such as `. * [ ]` are literal.

### Worked examples (from `public_test.py` fixtures)

File `iliad.txt` line 9: `Of Atreus, Agamemnon, King of men.`

| Call | Match? |
| --- | --- |
| `pattern="Agamemnon"`, no flags | yes (substring) |
| `pattern="agamemnon"`, no flags | no |
| `pattern="agamemnon"`, `-i` | yes |
| `pattern="Of Atreus, Agamemnon, King of men."`, `-x` | yes |
| `pattern="Agamemnon"`, `-x` | no (not the whole line) |
| `pattern="Agamemnon"`, `-v` | no (line matches, invert drops it) |
| `pattern="Gandalf"`, `-v` | yes (line does not contain it) |

---

## 5. Output formatting

A **selected** line is one for which `line_matches` is true.

### 5.1 `-l` (files with matches) — highest output precedence

If `-l` is set:

- When a file has **at least one** selected line, emit **exactly** `{filename}\n`.
- Do not emit line text or line numbers (`-n` is ignored).
- Emit the name only once, at the first selected line, then **stop scanning that file**.
- Still scan later files.
- Filename is printed even when only one path was passed.

`-l` uses the same selected-line predicate as content mode, so `-l -v` means “files that contain at least one **non-matching** line”, not “files with no matches”.

### 5.2 Content mode (no `-l`)

For each selected line, emit:

```text
[filename:][line_number:][original_line_body][\n]
```

**Filename prefix** — include `f"{filename}:"` if and only if `len(files) > 1`.

This depends on how many paths were **passed**, not on how many actually matched. One match among three files still gets a filename prefix. A single-file search never gets a filename prefix in content mode.

**Line-number prefix** — if `-n`, include `f"{line_no}:"` immediately after the optional filename prefix. `line_no` is **1-based** and counts every line in the file (skipped / non-selected lines still increment it).

**Body** — the original line content without relying on regex. Preserve the text as stored.

**Terminator** — every emitted record must end with a single `\n`:

- If `raw` already ends with `\n`, use it as-is after prefixes (prefixes go before the body, not after the newline).
- If the last line of a file has no terminator, append `\n` so records do not fuse.

Concrete shapes:

| Situation | Example |
| --- | --- |
| 1 file, no flags | `Of Atreus, Agamemnon, King of men.\n` |
| 1 file, `-n` | `9:Of Atreus, Agamemnon, King of men.\n` |
| 1 file, `-l` | `iliad.txt\n` |
| 3 files, no flags | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| 3 files, `-n` | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |
| 3 files, `-l` | `iliad.txt\n` |

Several matches: concatenate in file order, and within a file in line order. No extra blank lines.

Public test that must pass:

```python
grep("Agamemnon", "", ["iliad.txt"])
# → "Of Atreus, Agamemnon, King of men.\n"
```

---

## 6. Flag combination matrix

Apply matching flags independently of formatting flags.

| Flags | Matching | Output |
| --- | --- | --- |
| (none) | substring, case-sensitive | body only (or `file:body` if multi-file) |
| `-n` | same | add `N:` |
| `-l` | same | filenames only |
| `-i` | case-insensitive substring | same as content mode |
| `-v` | keep lines that fail the positive match | same as content mode |
| `-x` | whole-line equality | same as content mode |
| `-n -l` | same as `-l` | **`-l` wins**; no numbers |
| `-i -x` | whole-line equality, case-insensitive | content |
| `-v -x` | lines that are **not** exact matches | content |
| `-i -v` | lines that do not contain pattern ignoring case | content |
| `-n -i -x` | case-insensitive whole line | numbered (and `file:` if multi) |
| `-n -l -x -i` | case-insensitive whole line | filenames only |
| `-l -v` | files with ≥1 non-matching line | filenames only |

Unknown / future combinations should still compose: matching (`-i -x -v`) then formatting (`-l` else optional `-n` + optional filename).

---

## 7. Edge cases (must handle)

1. **No matches** (including “match entire line” with a substring-only pattern): return `""`.
2. **Empty pattern `""`**: substring mode matches every line; `-x` matches only blank lines (comparison text `""`); `-v` inverts those rules.
3. **Empty `files`**: return `""` (no crash).
4. **Empty file**: no lines emitted; `-l` does not print its name.
5. **Last line without `\n`**: still match on unterminated text; emit with a trailing `\n`.
6. **`\\r\\n`**: strip both for matching; do not leave `\\r` in the comparison text for `-x`.
7. **Multiple files, matches in a later file only**: still prefix `filename:` because `len(files) > 1`.
8. **`-l` with multiple matching files**: one name per matching file, input order, each with `\\n`.
9. **Line numbers and `-v`**: numbers are original file line numbers, not a recount of selected lines.
10. **Substring vs word**: `may` matches inside `may`, `maybe` would also match if present; there is no word-boundary flag.
11. **Pattern equal to a filename**: still search file **contents**, not names (except `-l` output *is* the name).
12. **Literal metacharacters**: `Fruit` matches `Fruit`; `.` does not mean “any char”.
13. **Invert + no-match file**: `-v` on a file whose every line matches → that file contributes nothing (and `-l` does not list it).
14. **Invert + mixed file**: `-v` selects the non-matching lines; `-l -v` lists the file.
15. **Stable order**: never reorder files or lines.

Out of scope (do not implement unless forced by a test): recursive search, binary mode, color, regex, stdin (`-` as file), context lines (`-A/-B/-C`), count (`-c`).

---

## 8. Recommended implementation sketch

This is guidance, not required wording.

```python
def grep(pattern, flags, files):
    opts = parse_flags(flags)
    show_name = len(files) > 1
    out = []
    for name in files:
        out.extend(_search_one(name, pattern, opts, show_name))
    return "".join(out)
```

`_search_one`:

- `open(name)` in a `with` block.
- `enumerate(..., 1)`.
- Compute `ok = line_matches(...)`.
- If not `ok`: continue.
- If `opts.filename_only`: append `name + "\n"` and `break`.
- Else: build prefix ` (name + ":") if show_name else "" ` plus ` (str(n) + ":") if opts.line_number else "" `, then body + newline.

`line_matches`:

```python
hay = raw.rstrip("\r\n")
needle = pattern
if opts.ignore_case:
    hay, needle = hay.casefold(), needle.casefold()
ok = (hay == needle) if opts.exact_line else (needle in hay)
if opts.invert:
    ok = not ok
return ok
```

---

## 9. Constraints and testing notes

- **Public API**: only `grep(pattern, flags, files)` must exist and remain importable as `from grep import grep`.
- **Return type**: `str`, never `None` or a list. The stub currently `pass`es (returns `None`); that fails `assertMultiLineEqual`.
- **No regex**, no third-party packages, stdlib only.
- **Use `open`** so `public_test.py`’s `@mock.patch("grep.open", ...)` intercepts reads. Fixture files are `iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt` (see `FILE_TEXT` in `public_test.py`).
- Do not write files, do not use the network, do not look outside the workspace.
- Local check: `python -m unittest public_test.py`. Held-out tests cover the flag matrix, multi-file prefixes, `-l` precedence, inverted/exact/case-insensitive matching, and empty results — implement the full spec above, not only the single public example.

---

## 10. Acceptance checklist for the implementer

- [ ] `grep("Agamemnon", "", ["iliad.txt"])` → `Of Atreus, Agamemnon, King of men.\n`
- [ ] `-n` prefixes 1-based numbers; multi-file form is `file:N:line\n`
- [ ] `-l` prints each matching file once and ignores `-n`
- [ ] `-i` / `-x` / `-v` compose as specified
- [ ] Filename prefix iff `len(files) > 1`, content mode only
- [ ] Empty result is `""`
- [ ] Builtin `open` used for every file
- [ ] Literal string match only
