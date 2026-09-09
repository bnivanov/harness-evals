# Implementation Guide: `grep.py`

## 1. Goal

Implement a simplified Unix `grep` that searches files for a **fixed string** (not a regular expression) and returns matching lines as a single string.

Public entry point (do not change the signature):

```python
def grep(pattern, flags, files):
    ...
```

| Argument   | Type         | Meaning |
|-----------|--------------|---------|
| `pattern` | `str`        | Literal search string. Never interpret as regex. |
| `flags`   | `str`        | Zero or more flags, typically space-separated (e.g. `""`, `"-n"`, `"-i -x"`). |
| `files`   | `list[str]`  | One or more file names, searched in the given order. |

**Return type:** `str`. Never `None`. Concatenate every output record; each record ends with `\n`. If nothing matches, return `""`.

The public test mocks `grep.open`, so all file reads **must** go through the builtin `open` called from this module (`open(filename)` / `with open(filename) as ...`). Do not use `pathlib`, `io.open` via another name, or a helper module.

---

## 2. Behavioral contract (from README + public test)

1. Read each file in `files` order.
2. Decide, line by line, whether the line **matches** the pattern under the active flags.
3. Emit matching lines in the order found.
4. When **more than one file** is searched **and** the output is line content (not `-l`), prepend `filename:` to each line.
5. Flags customize matching and/or output format (see below). Flags combine independently except where output mode `-l` replaces line content.

### Flags

Parse `flags` into a set of letters. Recommended approach:

```python
flag_set = set()
for token in flags.split():
    if token.startswith("-"):
        flag_set.update(token[1:])
```

This accepts `""`, `"-n"`, `"-n -l"`, and compact forms such as `"-ilx"`. Ignore unknown letters.

| Flag | Effect |
|------|--------|
| `-n` | Prepend 1-based line number and `:` to each **content** line. Number comes **after** the filename (if a filename is printed). Ignored when `-l` is active. |
| `-l` | Do not print line content. Print each matching **file name once**, followed by `\n`, in file-list order. |
| `-i` | Case-insensitive match. Compare folded copies of pattern and line text (e.g. `.casefold()` or `.lower()` on both). |
| `-v` | Invert: keep lines that **fail** the match predicate. |
| `-x` | Whole-line match: the line text (without its newline) must equal the pattern (after optional case folding). Without `-x`, the pattern is a **substring** of the line text. |

Default (no flags): case-sensitive substring search; print matching line bodies; prefix filename only if `len(files) > 1`.

---

## 3. Data structures

Keep the implementation small and explicit. Suggested locals inside `grep`:

```text
flag_set: set[str]          # e.g. {"n", "i"}
list_only: bool             # "l" in flag_set
invert: bool                # "v" in flag_set
entire_line: bool           # "x" in flag_set
ignore_case: bool           # "i" in flag_set
show_line_numbers: bool     # "n" in flag_set
multi_file: bool            # len(files) > 1
needle: str                 # pattern, or pattern.casefold() if -i
results: list[str]          # output records, each already ending with \n
```

No extra classes are required. Do not compile a regex; matching is string equality / `in`.

---

## 4. File I/O and line identity

```python
with open(filename) as handle:
    lines = handle.readlines()
```

`readlines()` yields each line **including** its terminator (`\n`, or `\r\n` if present). A file that ends with a single trailing newline does **not** produce an extra empty line (unlike `content.split("\n")`, which would). **Do not** use `split("\n")`.

For matching, use the line **without** the terminator:

```python
text = line.rstrip("\r\n")
```

Do **not** strip spaces or other characters. Trailing/leading spaces are significant for `-x` and for substring search.

Line numbers are **1-based** in file order: `enumerate(lines, start=1)`.

If a line has no terminator (last line of a file that does not end in newline), `text` is the whole line; when emitting content, still terminate the output record with `\n` so every printed line matches the “each result ends with newline” contract. The fixture files all end with `\n`, so `line` already includes it; using `text + "\n"` as the body is equivalent and simpler.

---

## 5. Matching algorithm

Match against `text` (terminator stripped), never against the raw buffer that still contains `\n`.

```text
haystack = text.casefold() if ignore_case else text
# needle already folded the same way when ignore_case

if entire_line:
    matched = (haystack == needle)
else:
    matched = (needle in haystack)

if invert:
    matched = not matched
```

Notes:

- Empty `pattern`: substring match succeeds for **every** line (including empty lines). With `-x`, only empty lines match. `-v` inverts as usual.
- Matching is **literal**. Characters like `.`, `*`, `[` have no special meaning. Do not call `re.search` unless the pattern is fully escaped **and** you still implement `-x` as full-string equality; the `in` / `==` approach is the intended one.
- `-i` applies only to comparison, not to the text written to output. Printed lines keep original case.

---

## 6. Output formatting

Two output modes. Decide once from flags.

### 6.1 File-name mode (`-l`)

When a file has **at least one** matching line (after `-v` / `-x` / `-i`):

```text
results.append(filename + "\n")
```

Then **stop scanning that file** (later matches cannot change the output). Do not print line numbers or line bodies. Filename prefix rules for multi-file search do **not** apply; `-l` always prints the name, even when `files` has length 1.

If the file has no matching line, print nothing for it.

### 6.2 Line mode (no `-l`)

For each matching line, build one record:

```text
body = text + "\n"

if multi_file and show_line_numbers:
    record = f"{filename}:{line_no}:{body}"
elif multi_file:
    record = f"{filename}:{body}"
elif show_line_numbers:
    record = f"{line_no}:{body}"
else:
    record = body
```

`multi_file` is `len(files) > 1`, **not** “more than one file actually produced hits”. If the caller passed three files and only one has a match, that match is still prefixed with `filename:`.

Join with no extra separators:

```python
return "".join(results)
```

---

## 7. Control flow (reference)

```text
parse flags
needle = pattern.casefold() if -i else pattern
multi_file = len(files) > 1
results = []

for filename in files:
    with open(filename) as handle:
        lines = handle.readlines()
    for line_no, line in enumerate(lines, start=1):
        text = line.rstrip("\r\n")
        if line_matches(text):
            if list_only:
                results.append(filename + "\n")
                break
            else:
                results.append(format_line(...))

return "".join(results)
```

Processing order is part of the spec: files in list order, lines in file order.

---

## 8. Edge cases and combinations

| Situation | Required behavior |
|-----------|-------------------|
| No matches | `""` |
| Single file, no flags | Raw matching lines, no filename prefix |
| Multiple files, no flags | `filename:line\n` for each hit |
| `-n` single file | `N:line\n` |
| `-n` multiple files | `filename:N:line\n` |
| `-l` single or multiple | `filename\n` once per file that has a hit |
| `-l -n` | `-l` wins: names only, no numbers |
| `-i` | Fold both sides; print original line |
| `-i -x` | Whole-line equality after folding |
| `-x` substring-only pattern | No match (pattern must be the entire line) |
| `-v` | Emit lines that do **not** satisfy the (possibly `-x`/`-i`) predicate |
| `-v -x` | Emit lines whose full text is not equal to the pattern |
| `-l -v` | List files that contain **at least one** non-matching line. An empty file has no such line → omit it. |
| `-l` and first-line hit | May `break` after recording the file name |
| Empty file, no `-v` | No output for that file |
| Pattern appears multiple times on one line | The line is emitted **once** |
| Same line would match overlapping flags | One output record per matching line |
| Trailing spaces on the line | Part of the text; `-x` requires they be in the pattern |
| File names in `files` | Use exactly as given (fixtures: `iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`) |
| `open` | Must be the builtin invoked in `grep.py` so `@mock.patch("grep.open", ...)` works |

Do not invent extra CLI features (recursive search, stdin, regex, color, count-only `-c`). Unknown flags can be ignored.

---

## 9. Suggested helper layout (optional)

A single function is enough. If split for clarity, keep helpers in `grep.py` and do not change the public signature:

```python
def _parse_flags(flags: str) -> set[str]:
    ...

def _matches(text: str, needle: str, entire_line: bool, invert: bool) -> bool:
    ...

def _format_line(filename, line_no, text, multi_file, show_line_numbers) -> str:
    ...

def grep(pattern, flags, files):
    ...
```

`needle` should already be case-folded when `-i` is on; `_matches` then compares `text` folded the same way, or fold inside `_matches` if you pass the raw pattern and an `ignore_case` bit. Pick one place to fold and do it consistently.

---

## 10. Worked examples (fixture text)

The public test (and the standard exercise fixtures) use three in-memory files. Use these as mental test vectors while implementing.

**`iliad.txt` last line** contains `Agamemnon`:

```text
grep("Agamemnon", "", ["iliad.txt"])
→ "Of Atreus, Agamemnon, King of men.\n"
```

Same search over three files (filename prefix required because `len(files) == 3`):

```text
grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])
→ "iliad.txt:Of Atreus, Agamemnon, King of men.\n"
```

**`-n`** on `paradise-lost.txt` for `Forbidden` (line 2):

```text
"2:Of that Forbidden Tree, whose mortal tast\n"
```

**`-l`**:

```text
grep("Forbidden", "-l", ["paradise-lost.txt"])
→ "paradise-lost.txt\n"
```

**`-x`**: `"With loss of Eden"` does not match the full line `With loss of Eden, till one greater Man`; the full line as pattern does.

**`-i`**: pattern `FORBIDDEN` matches `Forbidden` in the original line; output keeps `Forbidden`.

**`-v`** with substring `"Of"` on `paradise-lost.txt` (case-sensitive): drop lines whose text contains `Of`; keep the others (including lines that only contain lowercase `of`).

**`-l` over multiple files** for `"who"`: `iliad.txt` and `paradise-lost.txt` contain it; `midsummer-night.txt` does not → two name lines in that order.

---

## 11. Implementation order

1. Flag parsing + `open`/`readlines` loop; substring match; return joined lines (unblocks the public test).
2. Multi-file filename prefix (`len(files) > 1`).
3. `-n` line numbers and the `filename:N:body` order.
4. `-l` (short-circuit per file; always print names).
5. `-i`, then `-x`, then `-v`, then combinations (`-i -x`, `-n -v`, `-l -v`, `-x -v`, `-l -n`).
6. Confirm empty result is `""`, not `"\n"` or `None`.
7. Confirm matching uses terminator-stripped text so a pattern never has to include `\n`.

---

## 12. Constraints

- Edit only `grep.py` when implementing (this plan must not be treated as a request to change tests).
- No network, no extra packages, no reading held-out tests.
- Stay compatible with the mocked `open` used in `public_test.py`.
