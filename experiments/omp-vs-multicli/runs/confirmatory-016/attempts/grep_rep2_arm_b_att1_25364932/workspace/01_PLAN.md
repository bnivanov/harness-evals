# Implementation Guide: `grep.py`

This document is the full design for implementing `grep()` in `grep.py`. Implement exactly this contract. Do not edit tests. Do not fetch canonical solutions or files outside the workspace.

## 1. Problem

Implement a simplified, **fixed-string** (not regex) grep:

```python
def grep(pattern, flags, files):
    """Search files for lines matching pattern under flags. Return formatted matches."""
```

- `pattern`: `str` — the literal search string (never a regular expression).
- `flags`: `str` — space-separated flag tokens, or `""` when none. Examples: `""`, `"-n"`, `"-n -i -x"`, `"-n -l -x -i"`.
- `files`: `list[str]` — one or more filenames, in the order they must be processed.
- Return: `str` — matching output lines joined together. Every emitted line ends with `\n`. If there are no matches, return `""` (not `"\n"`).

Do **not** print to stdout. Do **not** use `re`. Substring and equality checks must treat `pattern` as literal text (a pattern of `"."` matches a period, not any character).

## 2. Public test constraints (must follow)

`public_test.py` patches **`grep.open`** (`@mock.patch("grep.open", ...)`). Therefore:

- Open files with the builtin **`open(filename)`** inside `grep.py` (a `with open(filename) as fh:` loop is correct).
- Do **not** use `pathlib.Path.read_text`, `io.open`, or a locally imported `open` that bypasses the module global.
- Read as **text**, not binary (`"r"` / default). Tests feed `io.StringIO`.
- Iterate lines (`for line in fh` or `fh.readlines()`). File contents in tests always use `\n` and include a trailing newline on the last line.

The public test only covers one case (`grep("Agamemnon", "", ["iliad.txt"])` → `"Of Atreus, Agamemnon, King of men.\n"`), but hidden tests cover every flag, combination, single-file vs multi-file formatting, inversion, and empty results. Implement the full README behavior, not just the one public case.

## 3. Flag parsing

Parse `flags` by splitting on whitespace and testing membership of the five tokens:

| Token | Meaning |
| ----- | ------- |
| `-n`  | Prefix **1-based file line number** and `:` on each content line. |
| `-l`  | Emit **only filenames** that contain at least one selected line; one name per such file. |
| `-i`  | Case-insensitive match (`str.lower()` on both pattern and line text is sufficient; test data is ASCII). |
| `-v`  | Invert: select lines that **fail** the match. |
| `-x`  | The (newline-stripped) line must **equal** the pattern, not merely contain it. |

Recommended:

```python
flag_tokens = set(flags.split())  # "" -> empty set; extra spaces are fine
want_line_numbers = "-n" in flag_tokens
want_filenames_only = "-l" in flag_tokens
ignore_case = "-i" in flag_tokens
invert = "-v" in flag_tokens
entire_line = "-x" in flag_tokens
```

- Unknown tokens: ignore.
- Do not require clustered POSIX forms (`-nix`). Tests pass **separate** tokens with spaces.
- Do not parse flags out of `pattern`.

## 4. Matching rules

For each physical line in a file:

1. Strip **only** a trailing `\n` for comparison (keep the original text for output, or re-append `\n` later).

   ```python
   text = line[:-1] if line.endswith("\n") else line
   ```

   Do **not** use `str.strip()` or `str.rstrip()` without arguments — that would drop leading/trailing spaces, which are significant. Prefer not to use `rstrip("\n")` on content that might theoretically contain other trailing characters you want to keep; the slice above is exact. Test files use `\n` only (no `\r\n`).

2. Build comparison strings:

   ```python
   needle = pattern.lower() if ignore_case else pattern
   haystack = text.lower() if ignore_case else text
   ```

3. Base match (before invert):

   - If `-x`: `matched = (haystack == needle)`
   - Else: `matched = (needle in haystack)`  # substring, including empty pattern → every line matches

4. If `-v`: `matched = not matched`.

5. A line is **selected** iff `matched` is true after inversion.

Notes:

- Line numbers (`-n`) count **every** physical line, starting at 1, including lines that are not selected.
- Empty pattern `""`: without `-x`, every line contains it; with `-x`, only a line whose text is empty matches. Hidden tests may or may not use this; handle it anyway.
- Matching is **not** regex. Use `in` / `==` only.

## 5. Output format

Collect a list of strings (each already ending in `\n`) and `return "".join(parts)`.

Let `multiple_files = len(files) > 1`.

### 5.1 `-l` (filenames only) — highest precedence for format

When `-l` is set, **do not** emit line content or line numbers (`-n` is ignored for formatting).

For each file, if **at least one** selected line exists:

- Append `f"{filename}\n"`.
- Stop reading that file (further matches cannot change the result).
- Do **not** prefix anything else.

File order is the order of `files`. A file with zero selected lines contributes nothing.

With `-v` and `-l`: list files that have at least one **non-matching** line (i.e. at least one selected line under inversion). An empty file has no selected lines, so it is omitted.

### 5.2 Content lines (no `-l`)

For each selected line, emit:

```
[filename:][linenum:]<line text>\n
```

Rules:

- `filename:` is included **if and only if** `len(files) > 1`. A single-file search never prefixes the filename (except in the `-l` mode above).
- `linenum:` is included **if and only if** `-n` is set. Numbers are 1-based, decimal, no padding.
- Order of prefixes: filename first, then line number, then content. Examples:
  - 1 file, no flags: `Of Atreus, Agamemnon, King of men.\n`
  - 1 file, `-n`: `2:Of that Forbidden Tree, whose mortal tast\n`
  - N files, no flags: `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
  - N files, `-n`: `paradise-lost.txt:4:With loss of Eden, till one greater Man\n`
  - 1 file, `-n -i -x` on a full-line match: `9:Of Atreus, Agamemnon, King of men.\n`
- Preserve the line text **exactly** (after removing the file’s trailing newline, then writing exactly one `\n`). Do not strip inner spaces, punctuation, or case. `-i` affects matching only, not output text.

### 5.3 Empty result

If nothing is selected, return `""`.

## 6. Algorithm

Process files left to right; within a file, lines top to bottom. No sorting.

```
parse flags into booleans (section 3)
needle = pattern.lower() if ignore_case else pattern
multiple_files = len(files) > 1
parts = []

for filename in files:
    with open(filename) as fh:
        for line_no, line in enumerate(fh, start=1):
            text = line[:-1] if line.endswith("\n") else line
            haystack = text.lower() if ignore_case else text
            is_match = (haystack == needle) if entire_line else (needle in haystack)
            if invert:
                is_match = not is_match
            if not is_match:
                continue
            if want_filenames_only:
                parts.append(filename + "\n")
                break
            prefix = ""
            if multiple_files:
                prefix += filename + ":"
            if want_line_numbers:
                prefix += str(line_no) + ":"
            parts.append(prefix + text + "\n")

return "".join(parts)
```

This is sufficient. No extra classes are required. A tiny helper for “does this line match?” keeps `grep()` readable.

## 7. Data structures

Keep it minimal:

- `set[str]` — parsed flag tokens.
- `list[str]` — output chunks (or a single list of result lines).
- Scalars: lowered pattern, booleans, 1-based integer line counter.
- No inverted index, no compiled regex, no buffering beyond one file’s line iterator.

Optional helper:

```python
def line_matches(text, needle, entire_line, invert) -> bool:
    ...
```

## 8. Flag combinations (implement all)

| Flags | Behavior |
| ----- | -------- |
| none | Substring, case-sensitive; content only; filename prefix iff multiple files. |
| `-n` | Same, plus `N:` after optional filename. |
| `-i` | Case-insensitive substring. Output original casing. |
| `-x` | Whole-line equality (after newline strip). |
| `-v` | Select non-matches of the above. |
| `-l` | Filenames only; first hit wins per file. |
| `-n -l` | `-l` wins format: filenames only, no numbers. |
| `-n -i -x` | Case-insensitive full-line match; still print original line; with `-n`, prefix number (and filename if multi-file). |
| `-x -v` | Select every line that is **not** exactly equal to the pattern (case rules from `-i` if present). |
| `-n -l -x -i` | Filenames of files that have at least one case-insensitive full-line match. If none, `""`. |
| `-v` + `-l` | Filenames of files with at least one inverted-selected line. |

Several matches in one file: emit every selected content line in file order (unless `-l`, then once).

No matches (including “pattern never occurs”, or `-x` on a substring that is not a whole line): `""`.

## 9. Edge cases

- **Single vs multiple files:** filename prefix depends on `len(files)`, not on how many files actually produced hits. Searching three files with a hit in only one still prefixes that one hit with `filename:`.
- **`-x` on a substring that appears inside a longer line:** no match (unless `-v`, then that line is selected).
- **Case-insensitive substring:** `"TO"` matches `"to"`, `"To"`, and the `"to"` inside `"into"`.
- **Case-sensitive `"Of"`:** matches `"Of Mans..."` but not `"loss of Eden"` (`of` ≠ `Of`).
- **`-v` on a missing pattern:** every line of the file is selected (full file dump, formatted per other flags).
- **Last line / newlines:** tests include a trailing `\n` after the last line of each fixture. Always emit a trailing `\n` on every result line.
- **Empty `files`:** README says one or more; if it happens, return `""`.
- **Missing file:** tests only open the three fixture names via the mock; do not invent extra error handling beyond letting `open` raise.
- **Pattern equals a full fixture line** (used with `-x` and with `-n -i -x` on a case-changed copy of a full line).
- **`-l` must not repeat a filename** when many lines match.
- **Do not trim** punctuation or the trailing comma that several fixture lines have.

## 10. Fixture files (for reasoning, not for shipping)

Hidden tests reuse the same three texts as `public_test.py` (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`). Lines are 1-based in that order. You do not need to copy the texts into `grep.py`; `open()` is mocked.

Useful sanity checks after implementation (do not add these as committed test files unless asked):

- `grep("Agamemnon", "", ["iliad.txt"])` → `Of Atreus, Agamemnon, King of men.\n`
- `grep("Forbidden", "-n", ["paradise-lost.txt"])` → `2:Of that Forbidden Tree, whose mortal tast\n`
- `grep("FORBIDDEN", "-i", ["paradise-lost.txt"])` → `Of that Forbidden Tree, whose mortal tast\n`
- `grep("Forbidden", "-l", ["paradise-lost.txt"])` → `paradise-lost.txt\n`
- `grep("may", "", ["midsummer-night.txt"])` → three lines (3, 5, 6 of that file), each ending with `\n`
- `grep("may", "-x", ["midsummer-night.txt"])` → `""`
- `grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])` → `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
- `grep("who", "-l", [those three])` → `iliad.txt\nparadise-lost.txt\n`
- `grep("Gandalf", "-n -l -x -i", ["iliad.txt"])` → `""`

## 11. Implementation shape in `grep.py`

Keep a single module function. Suggested layout:

1. Parse flags (section 3).
2. Normalize pattern for case.
3. Loop files / lines (section 6).
4. Return joined string.

No CLI `argparse`, no `sys.argv`, no writes, no third-party packages. Standard library only if needed (`open` is enough).

Type hints optional. A docstring optional.

## 12. What not to do

- Do not implement regex, globbing, or recursive directory search.
- Do not read files from disk paths other than those passed in `files`.
- Do not skip the `grep.open` mock (must call `open` in this module).
- Do not return a `list`; tests use `assertMultiLineEqual` on a `str`.
- Do not put a filename prefix on single-file content results.
- Do not let `-n` leak into `-l` output.
- Do not use `print`.
- Do not modify `public_test.py` or add dependencies.

## 13. Verification

Run the public test from the workspace:

```bash
python -m unittest public_test.py
```

That file has one case. Correctness for the rest depends on following this guide (flags, multi-file prefixes, `-l` precedence, invert, exact line, empty string on no match).
