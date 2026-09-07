# Implementation Guide: `grep.py`

This document is the complete architecture and implementation plan for the simplified `grep` in this workspace. Implement only `grep.py`. Do not change tests.

Source of truth used to design this plan:

- `README.md` — behavior, flags, output rules
- `public_test.py` — function signature, return type, I/O mocking, fixture files
- `grep.py` — current stub: `def grep(pattern, flags, files): pass`

---

## 1. Goal and public contract

Search one or more files for lines that contain a **fixed string** (not a regular expression) and return the matching lines as a single string, in the order they were found.

### Function signature

```python
def grep(pattern, flags, files):
    ...
```

| Parameter | Type | Meaning |
|-----------|------|---------|
| `pattern` | `str` | The fixed search string. May be empty. Must **not** be treated as a regex. |
| `flags` | `str` | Zero or more flags. Empty string `""` means no flags. Typical form: `"-n"`, `"-l"`, `"-n -i -x"`. |
| `files` | `list[str]` | File names to search, in caller order. One or more names in normal use. |

### Return value

- Type: `str` (tests use `assertMultiLineEqual`).
- Concatenation of all output records, each ending in `\n`.
- No matches → `""` (empty string, not `None`).
- Never return a `list`.

### I/O constraint (critical)

`public_test.py` patches **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

The mock `open` looks up `fname` in an in-memory dict and returns `io.StringIO(...)`. Therefore:

- Call the builtin **`open(filename)`** (or `open(filename, "r")`) from inside `grep.py`.
- Do **not** use `pathlib.Path.open`, `io.open` as a different lookup, or any HTTP/filesystem helper that bypasses `grep.open`.
- `with open(fname) as f:` is valid: `io.StringIO` is a context manager.
- Extra kwargs (`encoding=...`) are acceptable because the mock is `*args, **kwargs`, but keep the call simple: `open(fname)` or `open(fname, "r")`.
- If a name is unknown, the mock raises `RuntimeError`. Do not catch that.

---

## 2. Architecture

Keep `grep.py` as a small, pure-Python module with no third-party imports and no regex engine.

Recommended layout (all in `grep.py`):

```
grep(pattern, flags, files)          # public entry
  _parse_flags(flags) -> Options     # flag decoding
  _line_matches(line, pattern, opt)  # match predicate (before invert)
  _format_hit(...)                   # prefix filename / line number
  per-file loop using open()         # I/O + aggregation
```

A single module-level function plus 2–3 private helpers is enough. A tiny `@dataclass` (or a simple namespace / named tuple) for parsed flags is preferred over scattering booleans.

Do **not** use `re`. The README requires fixed-string search. Characters like `. * [ ]` in `pattern` are literal.

---

## 3. Data structures

### 3.1 `Options`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Options:
    line_numbers: bool   # -n
    files_with_matches: bool  # -l
    ignore_case: bool    # -i
    invert: bool         # -v
    exact_line: bool     # -x
```

A `set[str]` of flag letters (`{'n', 'i'}`) is also fine if the main loop reads clearly.

### 3.2 Accumulators

- `results: list[str]` — each element is one complete output record **including** its trailing `\n`.
- Final return: `"".join(results)`.

Do not mutate a giant string in the loop.

### 3.3 Per-file line stream

- `f.readlines()` or `for line in f:` both preserve each line’s original text, including its trailing `\n` when present.
- Enumerate with **1-based** line numbers: `enumerate(lines, start=1)`.

Line numbers count **every** physical line in the file, including lines that do not match.

---

## 4. Flag parsing

### 4.1 Input shape

`flags` is a single string:

| Input | Meaning |
|-------|---------|
| `""` | No flags (public test). |
| `"-n"` | One flag. |
| `"-n -i -x"` | Several flags, space-separated. |
| `"-l"` / `"-v"` / `"-x"` / `"-i"` | Other single flags. |

Whitespace-only should be treated as no flags (`flags.split()` → `[]`).

### 4.2 Decoding algorithm

1. `tokens = flags.split()` — splits on any whitespace; empty string yields `[]`.
2. For each token, if it starts with `-`, take the remainder as flag letters; otherwise treat the whole token as letters.
3. Collect letters into a set. This accepts both `"-n -i"` and clustered `"-ni"` without extra code.

```text
Options.line_numbers        = 'n' in letters
Options.files_with_matches  = 'l' in letters
Options.ignore_case         = 'i' in letters
Options.invert              = 'v' in letters
Options.exact_line          = 'x' in letters
```

Unknown letters: ignore them (do not crash). The specified flag set is only `-n -l -i -v -x`.

### 4.3 Precedence

| Combination | Behavior |
|-------------|----------|
| `-l` and `-n` | `-l` wins. Output only file names, never `N:` prefixes. |
| `-l` and `-x` / `-i` / `-v` | `-l` only changes **what is printed**. Match logic still honors `-x`, `-i`, `-v`. |
| `-v` and `-x` | Invert applies **after** the exact-line (or substring) test. |
| `-i` and `-x` | Case-insensitive **whole-line** equality. |
| `-i` and substring | Case-insensitive **containment**. |

When `-l` is set, stop scanning a file after the first selected line (first match, or first non-match if `-v`). Each file is emitted at most once.

---

## 5. Matching algorithm

Matching is a predicate on a **single line**, then optionally inverted.

### 5.1 Normalize the line for comparison

File contents in the public fixture end with `\n`, and each physical line from `readlines()` / iteration typically includes a trailing `\n` except possibly a last line without one.

The search `pattern` does **not** include that newline. Compare against the line **without** a single trailing `\n`:

```python
text = line[:-1] if line.endswith("\n") else line
```

Equivalent: `line.removesuffix("\n")` (Python 3.9+) or `line.rstrip("\n")`.

**Do not** use `str.strip()` or `str.rstrip()` with no arguments. Leading/trailing spaces and tabs are significant, especially for `-x`.

Do not strip `\r` unless you already removed `\n` and want to be extra-safe. Fixtures use `\n` only. If you strip, only strip a trailing `\n` (and optionally a trailing `\r` left from `\r\n`). Recommended: `removesuffix("\n")` only.

### 5.2 Case folding (`-i`)

If `ignore_case`:

```python
text = text.lower()
needle = pattern.lower()
```

Otherwise `needle = pattern`.

ASCII is sufficient for the fixture texts (`Agamemnon`, `FORBIDDEN`, `ACHILLES`). `.lower()` is the intended tool. Apply folding to **both** sides. Do not use locale-dependent case conversion.

### 5.3 Exact line vs substring

```text
if exact_line:          # -x
    raw_hit = (text == needle)
else:
    raw_hit = (needle in text)
```

Notes:

- Empty `pattern` (`""`):
  - substring: `"" in text` is **True** for every line (including empty lines).
  - `-x`: True only when the line body is empty.
- This is **not** regex. `needle in text` and `==` are the whole matcher.
- Containment is anywhere in the line body, not only at a word boundary.

### 5.4 Invert (`-v`)

```python
selected = (not raw_hit) if options.invert else raw_hit
```

Invert is a boolean not of the match, not a second search. A selected line is one that will be printed (or that qualifies the file under `-l`).

### 5.5 Reference truth table

Assume pattern `"Of"`, line body `"Of Mans First Disobedience, and the Fruit"`.

| Flags | raw_hit | selected |
|-------|---------|----------|
| (none) | True (substring) | True |
| `-x` | False (not entire line) | False |
| `-v` | True | False |
| `-x -v` | False | True |
| `-i` with pattern `"of"` | True | True |

---

## 6. Output formatting

Build each output record from the **original** line text (keep the original trailing `\n` if present).

If a selected line does **not** end in `\n`, append `\n` so every record is a full line. Fixture files all end with `\n`, so this is defensive.

### 6.1 File-name listing (`-l`)

For a file that has **at least one** selected line:

```text
"<filename>\n"
```

- No line content.
- No line number.
- No colon after the name.
- Same format for one file or many files.
- File names appear in the order of `files`.
- A file with zero selected lines is omitted.

### 6.2 Content lines (no `-l`)

Prefixes, left to right, separated by `:`:

1. **File name** — include iff `len(files) > 1`.
2. **Line number** — include iff `-n`. 1-based decimal, no padding.
3. **Original line** — including its `\n`.

Examples (pattern match on iliad line 9):

| Situation | Output record |
|-----------|----------------|
| 1 file, no flags | `Of Atreus, Agamemnon, King of men.\n` |
| 1 file, `-n` | `9:Of Atreus, Agamemnon, King of men.\n` |
| N files, no flags | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| N files, `-n` | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |
| any, `-l` | `iliad.txt\n` |

Construction:

```python
parts = []
if multi_file:
    parts.append(filename)
if options.line_numbers:
    parts.append(str(line_number))
prefix = ":".join(parts)
if prefix:
    record = prefix + ":" + line_with_newline
else:
    record = line_with_newline
```

README wording: *“placing the number after the filename (if present)”* → `filename:number:line`, never `number:filename:line`.

### 6.3 Multi-file detection

```python
multi_file = len(files) > 1
```

Use the **length of the `files` argument**, not “how many files actually contained a match”. One file in the list ⇒ never prefix content lines with the file name (unless `-l`, which prints only the name).

### 6.4 Ordering

1. Files in the given `files` list order.
2. Within a file, selected lines in ascending line-number order.
3. Do not sort, reverse, or uniquify content lines. Duplicate lines in a file are printed twice if both match.

---

## 7. Main control flow

```text
grep(pattern, flags, files):
    opt = parse flags
    multi = len(files) > 1
    out = []

    for filename in files:
        with open(filename) as fh:
            # iterate lines in order
            for line_no, line in enumerate(fh, start=1):
                if not selected(line, pattern, opt):
                    continue
                if opt.files_with_matches:
                    out.append(filename + "\n")
                    break
                out.append(format content record)
    return "".join(out)
```

### 7.1 Why `break` on `-l`

Once a file has a selected line, further lines cannot change the `-l` result. Breaking is required for correctness of “at most one name per file” and is the natural reading of the README.

### 7.2 Empty `files`

If `files` is `[]`, the loop runs zero times and the function returns `""`. Do not raise.

### 7.3 Reading strategy

Prefer iterating the file object rather than `f.read().split("\n")`:

- `split("\n")` drops information about a trailing newline and can invent an extra empty field after a final `\n`.
- Iteration/`readlines()` matches Unix line semantics used by the tests.

---

## 8. Worked example (public fixture + public test)

`iliad.txt` (1-based):

```
1 Achilles sing, O Goddess! Peleus' son;
2 His wrath pernicious, who ten thousand woes
3 Caused to Achaia's host, sent many a soul
4 Illustrious into Ades premature,
5 And Heroes gave (so stood the will of Jove)
6 To dogs and to all ravening fowls a prey,
7 When fierce dispute had separated once
8 The noble Chief Achilles from the son
9 Of Atreus, Agamemnon, King of men.
```

Public test:

```python
grep("Agamemnon", "", ["iliad.txt"])
```

- Flags: none → substring, case-sensitive, no invert, not exact, not names-only, no numbers.
- Single file → no filename prefix.
- Line 9 contains `"Agamemnon"`.
- Return: `"Of Atreus, Agamemnon, King of men.\n"`

Further checks the same fixtures imply:

- `"may"` in `midsummer-night.txt` hits lines 3, 5, 6 (substring `"may"` inside `may` / `may` / `may`).
- `"Forbidden"` in `paradise-lost.txt` is line 2; with `-n` that is `2:Of that Forbidden Tree, whose mortal tast\n`.
- `"FORBIDDEN"` with `-i` hits the same line without requiring exact case.
- `"Gandalf"` with any flags against `iliad.txt` → `""`.

---

## 9. Edge-case catalog

Handle all of the following in the implementation. None of these should require special-case branches beyond the algorithms above, but verify them mentally when coding.

| Case | Expected behavior |
|------|-------------------|
| No matches | `""` |
| Empty pattern, no `-x` | Every line is selected (unless `-v`, then none) |
| Empty pattern, `-x` | Only empty line bodies |
| Empty pattern, `-v` | No lines (every line contains `""`) |
| Pattern equals full line, no `-x` | Still a match (substring of itself) |
| Pattern equals full line, `-x` | Match |
| Pattern is a proper substring, `-x` | Not a match |
| `-x` and trailing spaces on the line | Spaces are part of the line; they must be in `pattern` too |
| Case-only difference, no `-i` | Not a match |
| Case-only difference, `-i` | Match |
| `-i` + `-x` | Whole-line equality under `.lower()` |
| `-v` | Print lines that fail the (possibly `-i`/`-x`) test |
| `-v` + `-x` | Print every line whose body is not exactly the pattern |
| `-l` + matches | One `filename\n` per file that has a selected line |
| `-l` + no matches in that file | Skip the file |
| `-l` + `-n` | Names only; ignore `-n` for formatting |
| `-l` + `-v` | Names of files that contain **at least one non-matching** line |
| `-l` + multiple matches in one file | Print the file name **once** |
| Multiple files, mixed hits | Prefix every content line with `file:`; preserve file order |
| Multiple files, `-n` | `file:N:line` |
| One file in the list | Never prefix content with the file name |
| Same file name twice in `files` | Process twice (two independent opens) |
| Last line without `\n` | Still match on body; emit a record that ends with `\n` |
| Line containing regex metacharacters | Literal; e.g. pattern `"."` matches a period, not any char |
| Pattern longer than the line | Substring fail; `-x` fail unless equal |
| Flags string with extra spaces | `split()` ignores them |
| Clustered flags `-nix` | Treat as `-n`, `-i`, `-x` if you collect letters after `-` |
| Missing file | Let `open` raise; do not substitute empty content |

### Empty file (zero lines)

- No `-v`, `-l`: not listed (no matching line).
- `-v`, `-l`: not listed (no non-matching line either).
- Content mode: contribute nothing.

---

## 10. File I/O details

```python
with open(filename) as handle:
    for line_no, line in enumerate(handle, start=1):
        ...
```

- Text mode (default) so lines are `str`, matching the mock `StringIO`.
- Do not read as `bytes`.
- Do not call `read()` and then regex-split unless you faithfully reconstruct the same lines `io.StringIO` would yield. Iteration is the safe choice.
- Close via the context manager. The mock `StringIO` supports it.

The second patch in tests (`io.StringIO` wrapped) is not something `grep.py` should call. Only `open` is required.

Do not print. Do not write files. The function is a pure string-returning API aside from reading inputs.

---

## 11. Suggested helper specs

### `_parse_flags(flags: str) -> Options`

- Input: the raw `flags` argument.
- Output: frozen options object.
- No I/O.

### `_selected(line: str, pattern: str, opt: Options) -> bool`

- Strip at most one trailing `\n` for comparison.
- Apply `-i`, then `-x` or substring, then `-v`.
- Return whether this line should be emitted / should qualify the file.

### `_format_line(filename, line_no, line, opt, multi_file) -> str`

- Used only when not `-l`.
- Guarantee a trailing `\n`.
- Apply prefixes as in §6.2.

`-l` formatting is a one-liner at the call site (`filename + "\n"`) and does not need a helper.

---

## 12. Implementation sketch

This is the intended algorithm, not a mandate to copy identifiers.

```python
def grep(pattern, flags, files):
    opt = _parse_flags(flags)
    multi = len(files) > 1
    chunks = []

    for name in files:
        with open(name) as fh:
            for n, line in enumerate(fh, start=1):
                if not _selected(line, pattern, opt):
                    continue
                if opt.files_with_matches:
                    chunks.append(name + "\n")
                    break
                chunks.append(_format_line(name, n, line, opt, multi))

    return "".join(chunks)
```

`_selected`:

```python
def _selected(line, pattern, opt):
    text = line.removesuffix("\n")
    needle = pattern
    if opt.ignore_case:
        text = text.lower()
        needle = needle.lower()
    hit = (text == needle) if opt.exact_line else (needle in text)
    return (not hit) if opt.invert else hit
```

`_format_line`:

```python
def _format_line(name, n, line, opt, multi):
    if not line.endswith("\n"):
        line = line + "\n"
    parts = []
    if multi:
        parts.append(name)
    if opt.line_numbers:
        parts.append(str(n))
    if parts:
        return ":".join(parts) + ":" + line
    return line
```

---

## 13. What not to do

- Do not import or use `re`.
- Do not shell out to the system `grep`.
- Do not read files via `pathlib` in a way that skips `grep.open`.
- Do not return a list of lines.
- Do not strip or rstrip whitespace for matching.
- Do not zero-index line numbers.
- Do not prefix the file name when `len(files) == 1` except for `-l`.
- Do not emit `filename:` on `-l` output (no colon).
- Do not keep scanning a file after a `-l` hit.
- Do not treat `-l` as changing the match predicate.
- Do not add CLI / `argparse` / `sys.argv`. The tests call `grep()` directly.
- Do not create packages, extra modules, or edit `public_test.py`.

---

## 14. Self-check before finishing `grep.py`

Mentally (or with a short local scratch, not by editing tests) verify:

1. `grep("Agamemnon", "", ["iliad.txt"])` equals the public-test string, including the final `\n`.
2. One file + `-n` → `N:line`, not `file:N:line`.
3. Two files + match in the first → `iliad.txt:...`.
4. `-l` on a matching single file → `paradise-lost.txt\n`.
5. `-i` matches `FORBIDDEN` to `Forbidden`.
6. `-x` does not match a substring-only line.
7. `-v` emits the complement, still with the same prefixes.
8. `-n -l` emits only the file name.
9. No match → `""`.
10. Builtin `open` is used so the mock in `public_test.py` intercepts it.

---

## 15. Complexity and scope

- Time: O(total characters in all files × 1), with substring search at CPython’s `in` (efficient enough; files are tiny).
- Memory: store output records; may also hold one file’s lines if using `readlines()`. Streaming iteration is enough.
- No concurrency, no caching, no index.

This is the entire feature set. After `grep.py` implements the above, the public test and the remaining flag/file combinations described in the README should pass.
