# Implementation Guide: `grep.py`

## Goal

Implement `grep(pattern, flags, files)` in `grep.py`: a **fixed-string** (not regex) line search over one or more files, with POSIX-inspired flags `-n`, `-l`, `-i`, `-v`, and `-x`.

Do **not** change tests. The public suite currently has one case; hidden tests will cover flag combinations, multi-file output, inversion, exact-line matching, and empty results. Implement the full README contract, not only the public example.

---

## Function Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

| Argument | Meaning |
|---|---|
| `pattern` | Literal substring to find. Never treat as a regular expression. |
| `flags` | Space-separated short flags, e.g. `""`, `"-n"`, `"-n -l -i"`. |
| `files` | One or more file names, in the order they must be read and reported. |

**Return value:** a single string. Each reported record ends with `\n`. If nothing is selected, return `""` (empty string, **not** `None`, **not** `"\n"`).

Public example:

```python
grep("Agamemnon", "", ["iliad.txt"])
# -> "Of Atreus, Agamemnon, King of men.\n"
```

---

## I/O Constraints (tests mock `open`)

The public tests patch **`grep.open`** (and wrap `io.StringIO`).

**Required:**

- Read files with the builtin `open(filename)` (text mode is fine: `open(filename)` or `open(filename, "r")`).
- Prefer `with open(filename) as fh:` and iterate lines or `readlines()`.

**Forbidden (would bypass the mock and fail):**

- `pathlib.Path.read_text` / `Path.open`
- `io.open(...)`
- `builtins.open(...)`
- `os.open` / binary reads unless you still go through `open()` in this module

File names are exact keys such as `"iliad.txt"`. Do not glob, recurse, or interpret paths.

Iterate `files` in list order. Do not sort.

---

## Flag Parsing

`flags` is a **string**, not a list.

```text
""                -> no flags
"-n"              -> {-n}
"-n -l -i"        -> {-n, -l, -i}
```

Recommended parse:

```python
flag_set = set(flags.split())
```

Then:

| Flag | Name | Effect |
|---|---|---|
| `-i` | ignore case | Compare with case folded (`.lower()` is enough; inputs are ASCII). |
| `-v` | invert | Select lines that **do not** match. |
| `-x` | entire line | Match only if the whole line equals the pattern (after stripping the line terminator). |
| `-n` | line number | Prefix each **content** line with `N:` (1-based). |
| `-l` | files with matches | Output each matching **file name once**, not line contents. |

Ignore unknown tokens. Tests use space-separated flags (`"-n -l"`), not bundled `"-nl"`. Supporting bundled flags is optional and unused.

Store booleans once after parsing:

```python
ignore_case = "-i" in flag_set
invert      = "-v" in flag_set
exact_line  = "-x" in flag_set
show_number = "-n" in flag_set
names_only  = "-l" in flag_set
```

---

## Matching Algorithm (per line)

1. Read the raw line from the file. File iterators keep the trailing `\n` when present.
2. Define **content** = the line with the terminator removed: `line.rstrip("\n")`. If a `\r\n` line ever appears, `rstrip("\r\n")` is safer; fixture files use `\n` only.
3. Build compare strings:
   - `needle = pattern.lower() if ignore_case else pattern`
   - `haystack = content.lower() if ignore_case else content`
4. **Positive match:**
   - If `-x`: `haystack == needle`
   - Else: `needle in haystack`  (literal substring; empty `pattern` matches every line)
5. **Selected line:** `matched != invert`  
   (`-v` keeps lines that failed the positive match).

**Do not use `re`.** Characters like `. * [ ]` in `pattern` are literal.

Line numbers are **1-based** and count **every** physical line, including those not selected.

---

## Output Formatting

Two independent decisions: **what** to emit, and **how to prefix** content lines.

### 1. `-l` (files with matches) — highest output priority

If `-l` is set:

- For each file, if **at least one** selected line exists, emit `f"{filename}\n"` **once**.
- Do **not** emit line text, line numbers, or a `filename:` prefix on those names.
- `-n` has no effect when `-l` is set.
- You may stop reading a file after the first selected line.

`-l` + `-v`: emit the file name if the file has at least one **non-matching** line (a selected line under invert). An empty file has no lines, so it is not listed.

### 2. Content lines (no `-l`)

For each selected line, emit one record:

```
[filename:][lineno:]content\n
```

Rules:

| Condition | Prefix |
|---|---|
| `len(files) == 1` and not `-n` | no prefix — just `content\n` |
| `len(files) == 1` and `-n` | `{lineno}:{content}\n` |
| `len(files) > 1` and not `-n` | `{filename}:{content}\n` |
| `len(files) > 1` and `-n` | `{filename}:{lineno}:{content}\n` |

**Filename prefix depends on how many files were *passed in*, not on how many actually matched.** Searching two files and matching only one still prefixes `iliad.txt:`.

Always terminate the record with `\n`, even if the source line had no trailing newline.

Preserve source **order**: files in argument order; within a file, increasing line number.

Concatenate records with no extra blank lines.

---

## Suggested Architecture

Keep `grep.py` as one module, three small pieces:

```
parse_flags(flags) -> frozenset[str] or a small FlagSet
line_selected(pattern, content, flags) -> bool
format_record(...) -> str
grep(...) -> str   # orchestration
```

### `grep` orchestration (pseudocode)

```
flag_set = parse(flags)
multi = len(files) > 1
out = []

for filename in files:
    with open(filename) as fh:
        if names_only:
            for content in lines_of(fh):
                if line_selected(pattern, content, flag_set):
                    out.append(filename + "\n")
                    break
        else:
            for lineno, content in enumerate(lines_of(fh), start=1):
                if line_selected(pattern, content, flag_set):
                    prefix_parts = []
                    if multi:
                        prefix_parts.append(filename)
                    if show_number:
                        prefix_parts.append(str(lineno))
                    if prefix_parts:
                        out.append(":".join(prefix_parts) + ":" + content + "\n")
                    else:
                        out.append(content + "\n")

return "".join(out)
```

`lines_of` should yield terminator-stripped content (and not skip empty lines).

No classes required. A `FlagSet` namedtuple/dataclass is optional sugar.

---

## Fixture Files (for reasoning; tests inject via mock)

Three in-memory texts (each ends with a final `\n`):

**iliad.txt** (9 lines) — last line is `Of Atreus, Agamemnon, King of men.`

**midsummer-night.txt** (7 lines)

**paradise-lost.txt** (8 lines)

Use these to sanity-check combinations locally; do not hard-code fixture contents in `grep.py`.

---

## Worked Behaviors (expected shapes)

Assume the public `iliad.txt` unless noted.

| Call | Result shape |
|---|---|
| `grep("Agamemnon", "", ["iliad.txt"])` | `Of Atreus, Agamemnon, King of men.\n` |
| `grep("Agamemnon", "-n", ["iliad.txt"])` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("Agamemnon", "-l", ["iliad.txt"])` | `iliad.txt\n` |
| `grep("AGAMEMNON", "-i", ["iliad.txt"])` | same content line as the first row |
| `grep("Agamemnon", "-x", ["iliad.txt"])` | `""` (pattern is only a substring of the line) |
| `grep("Of Atreus, Agamemnon, King of men.", "-x", ["iliad.txt"])` | the full line + `\n` |
| `grep("Agamemnon", "-n -l", ["iliad.txt"])` | `iliad.txt\n` (`-l` wins) |
| `grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt"])` | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `grep("Agamemnon", "-n", [two files])` | `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("NOPE", "", ["iliad.txt"])` | `""` |
| several matches of `"of"` (case-sensitive) | every line containing lowercase `of`, in order, each ending in `\n` |
| `-v` | every line that does **not** contain the pattern |
| `-i -x` | whole-line match, case-insensitive |
| `-l` on several files | each matching file name once, in argument order, each with `\n` |

---

## Edge Cases (must handle)

1. **No matches** → `""`.
2. **Empty pattern** `""`: without `-x`, every line is a substring match; with `-x`, only empty lines; `-v` inverts those rules.
3. **Empty file** → no selected lines; `-l` does not print it (including `-l -v`).
4. **Empty line** in a non-empty file is a real line (number it; `-x` with `""` selects it).
5. **Last line without `\n`**: still match on stripped content; still emit `\n` in the result.
6. **Literal metacharacters** in pattern (`a.c`, `*`, `[`): use `in` / `==`, never regex.
7. **`-i` only affects matching**, never the emitted text (preserve original case).
8. **`-x` is exact on the full stripped line** — leading/trailing spaces in the file are significant.
9. **Multi-file prefix even when only one file hits.**
10. **`-l` deduplicates per file** (one name even if many matching lines).
11. **Flag combinations** all compose: matching flags (`-i -x -v`) then output flags (`-n` or `-l`). Only conflict: `-l` suppresses `-n` and content.
12. **Multiple files + `-v`**: still prefix filenames; emit every non-matching line from every file.
13. **Duplicate file names** in `files`: process each occurrence independently (search and possibly print twice).
14. **Do not strip interior whitespace**; only the line terminator.
15. **Do not add a filename prefix for a single-file search**, even with `-n`.
16. **Stable order**; no unique-sorting of lines.
17. **`flags` with extra spaces**: `split()` already collapses them.
18. **Return type is `str`**, suitable for `assertMultiLineEqual`.

---

## What Not To Implement

- Regex, extended regex, or `-E`/`-F` (this tool is always fixed-string).
- Recursive `-r`, context `-A/-B/-C`, count `-c`, color, stdin-when-no-files.
- Exit codes (the function returns a string, not a process status).
- Writing to stdout (`print`); **return** the string.
- Network, package installs, or reading files other than those named in `files`.

---

## Implementation Notes / Pitfalls

- `str.find` / `in` is correct; do not compile a regex with `re.escape` unless you fully disable regex features — simpler not to import `re`.
- `.lower()` vs `.casefold()`: fixtures are ASCII; either works. Apply to **both** pattern and line.
- Building prefixes with `":".join(parts) + ":" + content` avoids missing or doubled colons.
- Collect a list of strings and `"".join` at the end; do not `+=` in a tight loop if you want to stay tidy (functionally fine at this size).
- Close files (`with` statement) even though `StringIO` does not require it.

---

## Verification

After implementation (done by the implementer, not this plan):

```text
python -m unittest public_test.py
```

That file only asserts the single-file, no-flag `Agamemnon` case. Mentally (or with throwaway checks **inside this workspace only**) walk the tables above: `-n`, `-l`, `-i`, `-x`, `-v`, multi-file prefixes, empty output, and `-l` winning over `-n`.

---

## File Touch List

| File | Action |
|---|---|
| `grep.py` | Implement `grep`; keep the existing function name and signature. |
| `public_test.py` | Do not edit. |
| `README.md` | Do not edit. |

No extra modules are required.
