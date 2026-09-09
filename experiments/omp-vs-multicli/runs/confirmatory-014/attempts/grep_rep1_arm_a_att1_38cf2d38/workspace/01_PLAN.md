# grep.py implementation guide

Implement `grep(pattern, flags, files)` in `grep.py`. Do not change tests.

Public contract (from stub + `public_test.py`):

```python
def grep(pattern: str, flags: str, files: list[str]) -> str: ...
```

Call shape: `grep("Agamemnon", "", ["iliad.txt"])`.

- `pattern`: fixed string (not a regex).
- `flags`: a single string of zero or more space-separated short options (`""`, `"-n"`, `"-i -v"`, …).
- `files`: one or more filenames, searched in list order.
- Return: one string of output lines (each ending in `\n`), or `""` if nothing matched.

Tests patch `grep.open` (`create=True`) and feed in-memory text. Use the builtin `open(filename)` (text mode is fine). Do not use `pathlib`, `io.open`, or a locally rebound name that would miss the patch.

---

## Behavior (README)

1. Read each file in `files` order.
2. Keep lines that contain `pattern` as a literal substring.
3. Emit kept lines in the order found.
4. If `len(files) > 1` and `-l` is not set, prefix every emitted line with `filename:`.
5. Single-file search does **not** prefix the filename (except `-l`, which prints names only).

### Flags (independent; combine freely)

| Flag | Effect |
|------|--------|
| `-n` | Prefix 1-based line number and `:` (after filename if present). |
| `-l` | Emit each matching **filename** once (`filename\n`), then stop that file. |
| `-i` | Case-insensitive compare. |
| `-v` | Invert: keep lines that **fail** the match test. |
| `-x` | Whole-line match (equality), not substring. |

Unknown tokens in `flags` will not appear in tests; ignore extras or treat only the five above.

---

## Data structures

Keep it boring. No classes required.

```text
opts: set[str]          # e.g. {"-n", "-i"} from flags.split()
multi: bool             # len(files) > 1
out: list[str]          # pieces joined at the end
```

Optional tiny helpers (names free):

- `parse_flags(flags: str) -> set[str]`
- `line_matches(content: str, pattern: str, opts: set[str]) -> bool`
- `format_hit(filename, lineno, raw_line, multi, opts) -> str`  # unused when `-l`

Do not compile regexes. Do not copy file bodies except as read from `open`.

---

## Algorithms

### 1. Parse flags

```python
opts = set(flags.split())
```

Empty `flags` (`""`) → empty set. Order of flags does not matter.

### 2. Match test (per line)

Work on the line **without** its trailing newline. Do **not** `.strip()`: leading/trailing spaces are significant.

```text
content = line[:-1] if line.endswith("\n") else line
needle, hay = pattern, content
if "-i" in opts:
    needle, hay = needle.lower(), hay.lower()
matched = (hay == needle) if "-x" in opts else (needle in hay)
if "-v" in opts:
    matched = not matched
```

Fixed-string rules:

- Never `re.search`. Characters like `. * [ ]` in `pattern` are literal.
- Empty `pattern`: substring match is true for every line; `-x` matches only an empty line (`content == ""`).
- `-i` applies to both substring and whole-line compares.

### 3. Per-file scan

```text
for filename in files:
    with open(filename) as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line_matches(...):
                continue
            if "-l" in opts:
                out.append(filename + "\n")
                break
            out.append(format_hit(...))
return "".join(out)
```

- Line numbers count **every** physical line (1-based), including non-matches and lines kept only because of `-v`.
- `-l`: first matching line (after `-v`/`-i`/`-x`) emits the name once; skip the rest of that file. Files with zero matching lines emit nothing.
- Preserve file order. Preserve in-file order.

### 4. Output format (`-l` not set)

`raw_line` is the line as read (keep its `\n` if present).

| Situation | Format |
|-----------|--------|
| 1 file, no `-n` | `{raw_line}` |
| 1 file, `-n` | `{lineno}:{raw_line}` |
| N files, no `-n` | `{filename}:{raw_line}` |
| N files, `-n` | `{filename}:{lineno}:{raw_line}` |

Colon placement: filename (if any), then line number (if `-n`), then the original line text. No extra spaces.

If a physical line has no trailing `\n` (last line of a file without a final newline), still emit a trailing `\n` on that output record so every result line is newline-terminated. The public fixture files all end with `\n` on the last line; `io.StringIO` + iteration will include those newlines.

`-l` output is **only** `"{filename}\n"` per matching file — no colon, no line number, no file contents. `-n` does not change `-l` output. Filename prefixing for multi-file mode does not apply under `-l` (the name *is* the output).

Empty result: `""` (not `"\n"`).

---

## Flag combinations (required)

All combinations are valid. Evaluation order:

1. Compute raw match (`-x` / substring, then `-i`).
2. Invert if `-v`.
3. If still a hit: `-l` short-circuits to the filename; else format with `-n` / multi-file prefix.

Notable cases:

- `-l -v`: file name if **any** line fails the (possibly `-i`/`-x`) match.
- `-l -n`: names only.
- `-v -x`: keep lines that are not exactly `pattern` (case-folded if `-i`).
- `-i -x`: whole-line compare after lowercasing both sides.
- `-n -v`: numbers of the **non-matching** lines.
- Multiple files + `-l`: `"a.txt\nb.txt\n"` for those that hit, in `files` order.

---

## I/O and test constraints

- `open(filename)` must be the `open` visible as `grep.open` after import. Module-level builtin is correct: `with open(filename) as f:`.
- Do not swallow `open` errors; tests only open the three fixture names (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`).
- Do not write files. Do not print. Return the string.
- `flags` is a string, not a list. `files` is a list, possibly length 1.

Reading options (either is fine):

- `for line in fh:` (preferred; streaming).
- `fh.readlines()`.

Do not use `fh.read().split("\n")`: that drops the last empty slot / mishandles the trailing newline and can invent an extra empty line.

---

## Edge cases

| Case | Handling |
|------|----------|
| No matches | `""` |
| Several matches in one file | All kept lines, original order |
| Pattern appears more than once on a line | Line emitted once |
| Pattern equals a mid-line substring | Match unless `-x` |
| Case differs | Miss unless `-i` |
| Empty `files` | `""` (won’t be tested; safe) |
| Duplicate filenames in `files` | Scan each occurrence independently |
| `-l` and a file that matches | One name line, even if many matching lines |
| Inverted match on a file where every line matches | No output for that file |
| Whole-line match with trailing spaces on the file line | Not a match unless `pattern` includes those spaces |
| Regex-looking pattern e.g. `a.*b` | Literal characters only |

---

## Suggested implementation sketch

Single function is enough; helpers only if they stay tiny.

```python
def grep(pattern, flags, files):
    opts = set(flags.split())
    invert = "-v" in opts
    whole = "-x" in opts
    insensitive = "-i" in opts
    names_only = "-l" in opts
    number = "-n" in opts
    multi = len(files) > 1
    needle = pattern.lower() if insensitive else pattern
    out = []

    for filename in files:
        with open(filename) as fh:
            for lineno, line in enumerate(fh, start=1):
                content = line[:-1] if line.endswith("\n") else line
                hay = content.lower() if insensitive else content
                hit = (hay == needle) if whole else (needle in hay)
                if invert:
                    hit = not hit
                if not hit:
                    continue
                if names_only:
                    out.append(filename + "\n")
                    break
                prefix = f"{filename}:" if multi else ""
                if number:
                    prefix = f"{prefix}{lineno}:"
                emitted = line if line.endswith("\n") else line + "\n"
                out.append(prefix + emitted)

    return "".join(out)
```

This is the complete behavior. Implement it (or an equivalent) in `grep.py` only.

---

## Verification (for the implementer; planner does not run/edit tests)

After implementation, `python -m unittest public_test` should pass the single public case:

- `grep("Agamemnon", "", ["iliad.txt"])` → `"Of Atreus, Agamemnon, King of men.\n"`

Held-out tests will cover flags, multi-file prefixes, `-l`, inversions, and whole-line matches as specified above. Do not add test files in this slice unless a later agent is asked to.
