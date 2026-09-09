# Implementation Guide: `grep.py`

## Goal

Implement `grep(pattern, flags, files) -> str` in `grep.py`.

This is a **fixed-string** line search (not a regex engine). Read the given files in order, select lines according to the flags, and return a single string of output records. Each record ends with `\n`. If nothing is selected, return `""` (never `None`).

Do **not** change tests. The public test patches `grep.open`; the function must call the builtin `open()` so that patch applies.

---

## Function Contract

```python
def grep(pattern, flags, files):
    ...
```

| Argument  | Type        | Meaning |
|-----------|-------------|---------|
| `pattern` | `str`       | Literal search string. Not a regular expression. May be empty. |
| `flags`   | `str`       | Space-separated flag tokens such as `""`, `"-n"`, `"-l -i"`, or clustered `"-nix"`. |
| `files`   | `list[str]` | One or more file paths, in search order. |

**Return:** concatenation of selected output records. Every record, including `-l` filenames, ends with `\n`.

---

## Architecture

Keep the implementation small and linear. Three phases:

1. **Parse flags** from the `flags` string into a set of option letters.
2. **Scan files** in the given order. For each file, read lines, decide which lines are selected, and emit records.
3. **Join** the records into one string.

Suggested helpers (names are not mandatory):

- `parse_flags(flags) -> set[str]` — letters such as `{"n", "i"}`.
- `line_selected(content, pattern, opts) -> bool` — match/invert decision on a newline-stripped line.
- `format_record(filepath, line_no, raw_line, opts, multi_file) -> str` — one output record for a selected line (not used when `-l`).

A single function with inlined helpers is also fine if it stays readable.

```
grep(pattern, flags, files)
  opts = parse_flags(flags)
  multi = len(files) > 1
  out = []
  for path in files:
      lines = read via open(path)
      for i, raw in enumerate(lines, start=1):
          if line_selected(stripped(raw), pattern, opts):
              if "l" in opts:
                  out.append(path + "\n")
                  break
              out.append(format_record(...))
  return "".join(out)
```

---

## Flag Parsing

Treat `flags` as a string (the public test passes `""`).

Rules:

- Split on whitespace. Empty / all-whitespace → no flags.
- Each token is expected to start with `-`. Consume every character after the leading `-` as an independent flag letter.
- Support both separated (`"-n -i"`) and clustered (`"-ni"`) forms.
- Unknown letters can be ignored or treated as present; the specified letters are only `n`, `l`, `i`, `v`, `x`.

```python
def parse_flags(flags):
    opts = set()
    for token in flags.split():
        if token.startswith("-"):
            opts.update(token[1:])
        else:
            opts.update(token)
    return opts
```

Do **not** assume `flags` is a list. If a list were ever passed, `"".join` / iteration would be a later adaptation; the documented API is a string.

### Flag meanings

| Letter | Effect |
|--------|--------|
| `n` | Prefix each **line** record with its 1-based line number and a colon. |
| `l` | Do not print line text. Print each matching **file name** once, then stop scanning that file. |
| `i` | Case-insensitive comparison (`casefold` or `lower` on both pattern and line). |
| `v` | Invert selection: keep lines that **fail** the match test. |
| `x` | The pattern must equal the **entire** line (after stripping the line terminator), not a substring. |

Flags combine independently except:

- **`-l` dominates output shape.** When `l` is set, ignore `n` for formatting. Do not print line numbers, file prefixes on lines, or line bodies. Only `filename\n`.
- **`-v` inverts the boolean**, including when combined with `-x` and/or `-i`.
- **`-l` + `-v`:** a file is listed if it has **at least one non-matching line** (a selected line under invert). An empty file has no selected lines, so it is not listed.

---

## File I/O (critical for tests)

```python
with open(filepath) as fh:
    lines = fh.readlines()
```

Requirements:

- Call **`open`**, not `pathlib`, `io.open`, or a captured `__builtins__["open"]`. Tests do `@mock.patch("grep.open", ..., create=True)`.
- Text mode is enough. Do not pass encoding unless needed; the mock returns `io.StringIO`.
- Preserve line order. `readlines()` keeps the trailing `\n` on each line (and `\r\n` if present).
- Do not swallow `FileNotFoundError` / the mock’s `RuntimeError`. Let I/O errors propagate.
- Close via `with`. The mock `StringIO` is fine inside a context manager.

Process files in **`files` order**. Never sort or unique the path list. If the same path appears twice, scan it twice.

---

## Matching Algorithm

Work on the line **without its terminator**.

```python
def strip_terminator(raw_line):
    if raw_line.endswith("\r\n"):
        return raw_line[:-2]
    if raw_line.endswith("\n") or raw_line.endswith("\r"):
        return raw_line[:-1]
    return raw_line
```

Prefer explicit terminator stripping over `rstrip("\n")` / `rstrip()`:

- `str.rstrip()` would drop trailing spaces, which must remain significant for `-x`.
- Only remove a single trailing `\n` or `\r\n` (or lone `\r`).

### Compare

Let `text = strip_terminator(raw_line)` and `pat = pattern`.

1. If `i` in opts: compare using `text.lower()` and `pat.lower()` (or `casefold()`). Do not mutate the original line used for output.
2. Match predicate:
   - If `x` in opts: `text == pat` (after optional case fold).
   - Else: `pat in text` (literal substring; **not** `re.search`).
3. If `v` in opts: negate the predicate.
4. Empty `pattern`:
   - Without `-x`: `"" in text` is True for every line, so every line matches; with `-v`, nothing matches.
   - With `-x`: only an empty line (`text == ""`) matches; with `-v`, all non-empty lines match.

Regex metacharacters in `pattern` are ordinary characters. Never compile `pattern` with `re`.

A line is emitted at most once even if the substring occurs several times.

---

## Output Formatting

### `-l` (file-name mode)

On the first selected line of a file:

```
{filepath}\n
```

Then `break` to the next file. In multi-file searches, still print **only** the path, never `path:path` or line text.

### Line mode (no `-l`)

Build a prefix, then the original line body.

Prefix pieces, left to right, joined by `:`:

1. If `len(files) > 1`: the file name.
2. If `n` in opts: the 1-based line number as a decimal string (no padding).

Then:

- If the prefix is non-empty: `prefix + ":" + body`
- If the prefix is empty (single file, no `-n`): `body` only

`body` is the original file line, **not** the case-folded copy.

**Newline on the body:** tests compare with `assertMultiLineEqual` and expected strings end in `\n`. After formatting:

- If `raw_line` already ends with `\n`, keep it.
- If it does not (last line without terminator), append `\n` so every record is a complete line.

Do not strip or add spaces around colons.

### Format matrix

Assume matching line text `LINE\n` at line `N`.

| Files | Flags | Record |
|-------|--------|--------|
| 1 | (none) | `LINE\n` |
| 1 | `-n` | `N:LINE\n` |
| 1 | `-l` | `file\n` |
| >1 | (none) | `file:LINE\n` |
| >1 | `-n` | `file:N:LINE\n` |
| >1 | `-l` | `file\n` |
| any | `-l -n` | `file\n` (`-l` wins) |

Invert (`-v`) and case/exact (`-i`, `-x`) change **which** lines are selected, not this layout. Line numbers always refer to the original file (they do not restart, and they are not “match indices”).

---

## Multi-file vs Single-file

`multi_file = len(files) > 1`.

- One path: never prefix the file name on line records.
- Two or more paths: always prefix the file name on line records (unless `-l`).
- This depends on the **length of the `files` argument**, not on how many files actually produced hits. Searching two files with matches in only one still prefixes that hit with the file name.

---

## Edge Cases

| Case | Behavior |
|------|----------|
| No matches | `""` |
| Empty `files` | `""` (nothing to scan). Spec says one or more files; still be safe. |
| Empty file | No lines → no output; `-l` does not list it. |
| Empty pattern | See matching rules above. |
| Pattern equals full line | Matches with or without `-x`. |
| Pattern is proper substring | Matches only without `-x` (or with `-v -x`). |
| Case differs | Matches only with `-i`. |
| `-i` + `-x` | Full-line equality ignoring case. |
| `-v` + `-x` | Lines whose full text is not equal to the pattern. |
| `-i` + `-v` + `-x` | Invert of case-insensitive full-line equality. |
| `-l` + `-n` | File names only. |
| `-l` + `-i` / `-x` / `-v` | File names of files that have ≥1 selected line under those match rules. |
| Multiple hits in one file | All matching lines, in file order (unless `-l`, then one name). |
| Same substring twice on one line | One output line. |
| Overlapping files in `files` | Scan each occurrence independently. |
| Trailing spaces on a line | Part of the line; `-x` must include them. |
| `\r\n` terminators | Strip for matching; when reprinting, keep original bytes/text and still end the record with `\n` if you normalize, **or** keep `\r\n` if you reprint `raw_line` unchanged. Reprinting `raw_line` unchanged is simplest; if the last character is `\n`, do not add another. |
| Leading/trailing spaces in `pattern` | Significant. Do not trim `pattern`. |
| Binary / missing files | Not specified; let `open` fail. |
| Flags with extra spaces | `str.split()` handles them. |

---

## Worked Examples (from README + public fixture)

Fixture line 9 of `iliad.txt`:

`Of Atreus, Agamemnon, King of men.`

Public test:

```python
grep("Agamemnon", "", ["iliad.txt"])
# "Of Atreus, Agamemnon, King of men.\n"
```

Further expected shapes (implement to this; not present in `public_test.py` but required by the README):

```python
grep("Agamemnon", "-n", ["iliad.txt"])
# "9:Of Atreus, Agamemnon, King of men.\n"

grep("Agamemnon", "-l", ["iliad.txt"])
# "iliad.txt\n"

grep("AGAMEMNON", "-i", ["iliad.txt"])
# "Of Atreus, Agamemnon, King of men.\n"

# substring, not whole line → no hit with -x
grep("Agamemnon", "-x", ["iliad.txt"])
# ""

# two files, line mode prefixes names
grep("the", "", ["iliad.txt", "midsummer-night.txt"])
# each hit as "filename:line\n", files in argument order, lines in file order

# two files, -n
# "filename:N:line\n"

# two files, -l, pattern that hits both
# "iliad.txt\nmidsummer-night.txt\n"  (only files with a hit)
```

Use the three poems in `public_test.py` (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`) as mental fixtures when checking combinations.

---

## Reference Implementation Sketch

This is a complete algorithm, not a canonical copy. Implement equivalently in `grep.py`.

```python
def grep(pattern, flags, files):
    opts = set()
    for token in flags.split():
        body = token[1:] if token.startswith("-") else token
        opts.update(body)

    casefold_match = "i" in opts
    invert = "v" in opts
    whole_line = "x" in opts
    names_only = "l" in opts
    show_number = "n" in opts
    multi = len(files) > 1

    needle = pattern.lower() if casefold_match else pattern
    records = []

    for path in files:
        with open(path) as fh:
            raw_lines = fh.readlines()

        for line_no, raw in enumerate(raw_lines, start=1):
            text = raw[:-2] if raw.endswith("\r\n") else raw[:-1] if raw.endswith(("\n", "\r")) else raw
            hay = text.lower() if casefold_match else text
            hit = (hay == needle) if whole_line else (needle in hay)
            if invert:
                hit = not hit
            if not hit:
                continue

            if names_only:
                records.append(path + "\n")
                break

            prefix_parts = []
            if multi:
                prefix_parts.append(path)
            if show_number:
                prefix_parts.append(str(line_no))
            body = raw if raw.endswith("\n") else raw + "\n"
            if prefix_parts:
                records.append(":".join(prefix_parts) + ":" + body)
            else:
                records.append(body)

    return "".join(records)
```

Notes on the sketch:

- `needle in hay` is correct for fixed strings, including when `needle` is empty.
- `break` after `-l` is required so a file is listed at most once.
- `show_number` is evaluated only when not `names_only`.
- Always return a `str`.

---

## What Not To Do

- Do not use the `re` module for matching.
- Do not print to stdout; **return** the string.
- Do not sort lines or files.
- Do not prefix a file name when `len(files) == 1` (except `-l`, which *is* the file name).
- Do not apply `-n` formatting under `-l`.
- Do not strip interior or trailing spaces from lines or from `pattern`.
- Do not write tests or edit `public_test.py`.
- Do not read files outside this workspace or look up held-out tests / canonical solutions.

---

## Verification (for the implementer)

1. `grep("Agamemnon", "", ["iliad.txt"])` equals the public-test string.
2. Mentally walk `-n`, `-l`, `-i`, `-v`, `-x` and the combinations above against the three fixture files.
3. Confirm the function still calls `open` so the mock patch works.
4. Confirm the return is `""` when there are no hits, not `None`.

After implementation, `python -m unittest public_test` should pass. Hidden tests will exercise flag combinations, multi-file prefixes, and invert/exact/case behavior described here.
