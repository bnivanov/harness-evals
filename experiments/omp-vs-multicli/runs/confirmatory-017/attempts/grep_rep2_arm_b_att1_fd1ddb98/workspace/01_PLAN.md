# Implementation Guide: `grep.py`

## Goal

Implement `grep(pattern, flags, files)` so it searches files for a **fixed string** (not a regex) and returns matching lines as a single string.

This is a simplified Unix grep:

- Search is a literal substring (or whole-line) comparison.
- Flags customize matching and output.
- Files are processed in the given order.
- Return value is the concatenated output, **not** a printed side effect.

Do **not** call the system `grep` binary. Do **not** use `re` for matching (patterns may contain regex metacharacters and must be treated as literals).

---

## Public contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
    ...
```

| Argument | Meaning |
|---|---|
| `pattern` | Fixed search string. May be empty, mixed-case, or contain punctuation/spaces. |
| `flags` | Zero or more flags as a single string (see Flag parsing). Empty string `""` means no flags. |
| `files` | One or more file names, in search order. |

**Return:** all selected output lines joined together. Every emitted line, including file-name-only lines from `-l`, ends with `\n`. If nothing is selected, return `""`.

The public test (and the rest of the suite) compares with `assertMultiLineEqual`, so trailing newlines and exact spacing must match.

Tests patch **`grep.open`** (`@mock.patch("grep.open", ..., create=True)`). File reads **must** go through the builtin `open()` used inside `grep.py`. Do not use `pathlib`, `io.open`, or subprocess.

---

## Flags

| Flag | Effect |
|---|---|
| `-n` | Prefix each **content** line with its 1-based line number and a colon. Number comes **after** the filename (if present). |
| `-l` | Output only the names of files that have **at least one selected line**. One name per such file, in file order. Takes **precedence** over `-n` and over filename-prefixed content lines. |
| `-i` | Case-insensitive match (`str.casefold()` or `.lower()` on both pattern and line). |
| `-v` | Invert: select lines that **fail** the match. |
| `-x` | Match the **entire line**, not a substring. Combined with `-i`, compare whole lines case-insensitively. Combined with `-v`, select lines that are **not** an entire-line match. |

Flags may appear together, e.g. `"-n -i -x"` or `"-n -l"`.

**Precedence**

1. Matching is determined first (`-i`, `-x`, then `-v`).
2. A line is “selected” if the (possibly inverted) match is true.
3. Formatting is determined after selection:
   - If `-l` is set: as soon as a file has one selected line, emit `"{filename}\n"` once and stop scanning that file (optional optimization; correctness only requires once per file).
   - Else if multiple files: prefix `"{filename}:"`.
   - Else (single file): no filename prefix.
   - If `-n` is set (and not `-l`): also prefix `"{line_number}:"`.
   - Then the original line text and `\n`.

`-l` wins over `-n`. A call like `grep("ten", "-n -l", ["iliad.txt"])` returns `"iliad.txt\n"`, not a numbered content line.

---

## Architecture

Keep the implementation as a small pipeline with three stages. No classes are required.

```
parse_flags(flags)
    -> options: {n, l, i, v, x}

for each filename in files (given order):
    open + iterate lines
    for each line (1-based index):
        selected = match(line, pattern, options) XOR options.v
        if selected:
            collect formatted record  OR  (if -l) collect filename and break

join collected records into one string
```

Suggested helpers (names are advisory):

1. `parse_flags(flags: str) -> set[str]` or a small namespace/bools.
2. `line_matches(line: str, pattern: str, case_insensitive: bool, entire_line: bool) -> bool`
3. `format_line(filename, line_number, line, *, show_file, show_number) -> str`
4. `grep(...)` orchestrates I/O, selection, and formatting.

Keep matching pure (no I/O). Keep formatting independent of matching. That makes `-v` / `-l` / `-n` combinations straightforward.

---

## Data structures

Use only simple, local structures:

- **Flag set:** `set` of characters `{'n','l','i','v','x'}` or five booleans. Do not store the raw flag string after parsing.
- **Prepared pattern:** if `-i`, store `pattern.casefold()` (or `.lower()`) once; do not re-casefold per line beyond the line itself.
- **Results:** a `list[str]` of already-formatted output chunks (each including its trailing `\n`). Join with `""` at the end.
- **Per-file state for `-l`:** a boolean “already emitted this file” or simply `break` after the first selected line.

Do not build regexes, index maps, or inverted indexes. Files in this exercise are tiny.

---

## Flag parsing

`flags` is a string, not a list.

Observed forms:

- `""`
- `"-n"`
- `"-l"`
- `"-i"`
- `"-v"`
- `"-x"`
- `"-n -i -x"`
- `"-n -l"`
- `"-n -l -x -i"`
- `"-x -v"`

**Recommended parser (robust, still simple):**

1. Split on whitespace: `tokens = flags.split()`.
2. For each token, if it starts with `-`, take the rest of the characters as individual flag letters.
3. Ignore unknown letters (should not appear) or treat them as no-ops.

This accepts both `" -n -i "` and a combined token like `"-ni"` if it ever appears.

Do **not** use `' -n' in flags` / `'-n' in flags` naively without tokenization: `'-n' in '-nope'` would be a false positive if unknown clusters appeared. Tokenizing is cheap and clear.

Empty / whitespace-only `flags` ⇒ no options set.

---

## File I/O and line iteration

```python
with open(filename) as fh:
    for line_number, raw in enumerate(fh, start=1):
        line = raw.rstrip("\n")
        ...
```

Rules:

- Use `open(filename)` with no extra mode/encoding arguments so the test mock (`io.StringIO` of the fixture text) works.
- Strip **only** a trailing `\n` (and, if you want POSIX friendliness, a trailing `\r`). Do **not** use `.strip()` — leading/trailing spaces are part of the line.
- Line numbers are **1-based** and count every physical line, selected or not.
- Files in the fixtures all end with a final `\n`. `splitlines()` or iterating the file object both work; iterating the file object is the most grep-like.
- Do **not** treat a trailing newline as an extra empty line. `for line in fh` already does the right thing.

Process `files` left to right. Open each file independently.

---

## Matching algorithm

Let `text` be the line with newline removed.

**Normalize for comparison** (do not mutate the original line used for output):

- If `-i`: `haystack = text.casefold()`, `needle = pattern.casefold()`.
- Else: `haystack = text`, `needle = pattern`.

`str.lower()` is also acceptable for the Latin-only fixtures; `casefold()` is the better default.

**Match predicate (before invert):**

- If `-x`: `haystack == needle`
- Else: `needle in haystack`  (literal substring; empty needle matches every line)

**Invert:**

- If `-v`: selected = `not matched`
- Else: selected = `matched`

Truth table worth keeping in mind:

| `-x` | `-v` | Selected when |
|---|---|---|
| no | no | pattern occurs as substring |
| no | yes | pattern does **not** occur as substring |
| yes | no | line equals pattern (after `-i` folding) |
| yes | yes | line does **not** equal pattern |

`-i` only changes how equality/substring is computed.

**Literal matching:** `"a.b"` must **not** match `"axb"`. Use `in` / `==`, never `re.search`.

---

## Output formatting

Let `multi = len(files) > 1`.

### `-l` (file-name mode)

For each file that has ≥1 selected line, append:

```
{filename}\n
```

- Single-file `-l` still prints the name, not the matching content.
- Multiple-file `-l` prints each matching name once, in the order those files appear in `files`.
- Non-matching files are omitted.
- Do not prefix line numbers.
- Combined with `-v`: a file is listed if it has at least one **non-matching** line (i.e. at least one selected line after invert). A file whose every line matches the pattern is omitted under `-l -v`.

### Content mode (no `-l`)

Each selected line becomes:

```
[ {filename}: ][ {line_number}: ]{text}\n
```

| Situation | Format |
|---|---|
| 1 file, no `-n` | `{text}\n` |
| 1 file, `-n` | `{n}:{text}\n` |
| N files, no `-n` | `{filename}:{text}\n` |
| N files, `-n` | `{filename}:{n}:{text}\n` |

There is **no** space around colons.

The `{text}` is the original line **without** its newline; then add exactly one `\n`.

Order of records = file order, and within a file, increasing line number.

### Empty result

If no file produces a selected line, return `""` (not `"\n"`).

---

## Worked examples from the fixtures / public test

Fixture files (same as `public_test.py`): `iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`.

**Single file, one match, no flags** (public test):

```text
grep("Agamemnon", "", ["iliad.txt"])
→ "Of Atreus, Agamemnon, King of men.\n"
```

**Single file, `-n`:**

```text
grep("Forbidden", "-n", ["paradise-lost.txt"])
→ "2:Of that Forbidden Tree, whose mortal tast\n"
```

**Single file, `-i`:**

```text
grep("FORBIDDEN", "-i", ["paradise-lost.txt"])
→ "Of that Forbidden Tree, whose mortal tast\n"
```

**Single file, `-l`:**

```text
grep("Forbidden", "-l", ["paradise-lost.txt"])
→ "paradise-lost.txt\n"
```

**Single file, `-x`:**

```text
grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])
→ "With loss of Eden, till one greater Man\n"
```

**Single file, several flags:**

```text
grep("OF ATREUS, AGAMEMNON, KING OF MEN.", "-n -i -x", ["iliad.txt"])
→ "9:Of Atreus, Agamemnon, King of men.\n"
```

**Several matches, no flags:**

```text
grep("may", "", ["midsummer-night.txt"])
→ "Nor how it may concern my modesty,\n"
  "But I beseech your grace that I may know\n"
  "The worst that may befall me in this case,\n"
```

**Several matches, `-n`:** line numbers 3, 5, 6 for those three lines.

**Several matches, `-x` with a substring that is never a full line:** `"may"` + `-x` on `midsummer-night.txt` → `""`.

**`-v` without `-i`:** `"Of"` is case-sensitive. In `paradise-lost.txt`, lines starting with `"Of "` are excluded; a line containing only lowercase `"of"` (e.g. `"With loss of Eden, ..."`) is **kept**.

**No matches, noisy flags:**

```text
grep("Gandalf", "-n -l -x -i", ["iliad.txt"]) → ""
```

**`-n -l` together:** `-l` wins; only the file name is printed.

**Multiple files, one match:**

```text
grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])
→ "iliad.txt:Of Atreus, Agamemnon, King of men.\n"
```

Filename prefix appears because `len(files) > 1`, even though only one file actually matched.

**Multiple files, `-l`:**

```text
grep("who", "-l", [iliad, midsummer, paradise])
→ "iliad.txt\nparadise-lost.txt\n"
```

(`midsummer-night.txt` has no `"who"`.)

**Multiple files, `-n`:**

```text
filename:linenum:content\n
```

**Multiple files, `-n -i -x`:**

```text
grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", files)
→ "paradise-lost.txt:4:With loss of Eden, till one greater Man\n"
```

**Multiple files, `-x -v`:** every line that is **not** exactly the given line, each prefixed with `filename:`.

---

## Edge cases (must handle)

1. **No matches** — return `""`.
2. **Empty pattern `""`** — substring of every line, so all lines are selected unless `-x` (then only empty lines) or `-v` (then none, unless `-x` and non-empty lines).
3. **Empty files list** — return `""`. Unlikely in tests; cheap to handle.
4. **Single vs multiple files** — filename prefix depends on `len(files)`, **not** on how many files actually produced hits. One hit among three files still gets `filename:` prefixes.
5. **`-l` + first-match** — print each matching file at most once.
6. **`-l` + `-n`** — ignore `-n`.
7. **`-l` + `-v`** — list files that contain at least one non-matching line.
8. **`-i` + `-x`** — whole-line compare on folded strings; output the original casing.
9. **`-i` + `-v`** — invert the case-insensitive predicate.
10. **`-x` that fails** — substring-only hits must not appear.
11. **Pattern with punctuation / apostrophes** — fixtures include `Heav'nly`, `Peleus' son`, commas; match as literals.
12. **Do not rstrip spaces** — only newlines.
13. **Preserve original line text in output** — even when comparison used a casefolded copy.
14. **Line numbers skip nothing** — a match on line 9 is `9:` even if lines 1–8 did not match.
15. **Unknown extra kwargs on `open`** — call `open(name)` or `open(name, "r")` only; the mock is `open_mock(fname, *args, **kwargs)` so extra args are tolerated, but keep it simple.
16. **Never write files; never print.**

---

## Suggested implementation sketch

```python
def grep(pattern, flags, files):
    opts = set()
    for token in flags.split():
        if token.startswith("-"):
            opts.update(token[1:])

    insensitive = "i" in opts
    invert = "v" in opts
    entire = "x" in opts
    names_only = "l" in opts
    number = "n" in opts
    show_file = len(files) > 1

    needle = pattern.casefold() if insensitive else pattern
    out = []

    for filename in files:
        with open(filename) as fh:
            for lineno, raw in enumerate(fh, 1):
                text = raw.rstrip("\n")
                haystack = text.casefold() if insensitive else text
                matched = (haystack == needle) if entire else (needle in haystack)
                if invert:
                    matched = not matched
                if not matched:
                    continue
                if names_only:
                    out.append(filename + "\n")
                    break
                prefix = ""
                if show_file:
                    prefix += filename + ":"
                if number:
                    prefix += str(lineno) + ":"
                out.append(prefix + text + "\n")

    return "".join(out)
```

This sketch is complete enough to implement; an implementer may split helpers if they prefer.

---

## Testing notes

- `public_test.py` only covers the no-flag single-file happy path. Hidden tests cover every flag, combinations, multiple files, inverted whole-line match, and empty results.
- Tests mock `grep.open` with in-memory `FILE_TEXT`. Implementation must not depend on real files on disk.
- Do not edit `grep.py` in the planning phase; do not edit tests.

---

## Out of scope / do not do

- Regular expressions, `-E`/`-F`/`-P`, context flags (`-A`/`-B`/`-C`), recursive search, stdin, binary files.
- Colored output, stderr diagnostics, exit codes (the function returns a string).
- Accessing files outside the workspace, network, package registries, or held-out tests.
- Importing third-party packages.

---

## Acceptance checklist for the implementer

- [ ] `grep("Agamemnon", "", ["iliad.txt"])` equals the public-test expected string.
- [ ] Multiple files always prefix `filename:` on content lines.
- [ ] `-n` inserts `N:` after an optional filename colon.
- [ ] `-l` prints unique matching file names, one per line, and suppresses content/`-n`.
- [ ] `-i`, `-x`, `-v` compose correctly, including `-n -i -x` and `-x -v`.
- [ ] No matches → `""`.
- [ ] Literal substring only; `open()` used for reads; return a string of `\n`-terminated lines.
