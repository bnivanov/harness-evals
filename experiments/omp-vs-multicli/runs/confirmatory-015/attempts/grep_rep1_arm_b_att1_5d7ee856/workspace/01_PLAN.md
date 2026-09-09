# Implementation Guide: `grep.py`

## 1. Goal

Implement `grep(pattern, flags, files)` so it searches one or more files for **fixed-string** (not regex) line matches and returns a single newline-terminated output string.

This is a simplified Unix `grep`. Behavior must match the README, the public test, and the usual Exercism-style cases built from the same three fixture files (`iliad.txt`, `midsummer-night.txt`, `paradise-lost.txt`).

Do **not** use the `re` module. Do **not** treat `pattern` as a regular expression.

---

## 2. Public contract

```python
def grep(pattern, flags, files):
    """Search files for lines matching a search string.

    :param pattern: str  – literal string to search for
    :param flags:   str  – space-separated flags, or ""
    :param files:   list[str] – one or more file paths, in search order
    :return:        str  – concatenated matching records, each ending in '\\n';
                           "" if there are no matches
    """
```

The stub is currently `pass`. Replace it with a real implementation. Keep this exact function name and signature.

### How tests call the function

From `public_test.py`:

```python
grep("Agamemnon", "", ["iliad.txt"])
# expected: "Of Atreus, Agamemnon, King of men.\n"
```

Held-out tests will use the same shape:

- `pattern`: a Python `str`
- `flags`: `""` or a string such as `"-n"`, `"-l"`, `"-i"`, `"-v"`, `"-x"`, `"-n -i"`, `"-n -l"`, `"-x -v"`, `"-n -i -x"`
- `files`: a list of one or more filenames
- assertion style: `assertMultiLineEqual` on the **entire** returned string

### How files are opened

`public_test.py` patches **`grep.open`**:

```python
@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
```

Therefore the implementation **must** call the builtin `open(...)` inside `grep.py` (so the name `open` is looked up on the `grep` module). Do not use `pathlib.Path.read_text`, `io.open` as a different lookup, or pre-read helpers that bypass `open`.

A matching loop of this form is required:

```python
with open(filename) as handle:
    for line_number, line in enumerate(handle, start=1):
        ...
```

`io.StringIO` is also patched with `wraps=io.StringIO`. Using the mocked `open` (which already returns `io.StringIO`) is enough; do not construct extra file objects.

---

## 3. Flags

`flags` is a single string. Parse it with whitespace split:

```python
flag_tokens = flags.split()   # "" -> []
```

Recognize these five tokens (order does not matter; duplicates are harmless):

| Flag | Meaning |
|------|---------|
| `-n` | Prepend 1-based line number and `:` to each **content** line |
| `-l` | Output only the **file name** of each file that has ≥1 matching line |
| `-i` | Case-insensitive comparison |
| `-v` | Invert: keep lines that **fail** the match |
| `-x` | Match only if the search string equals the **entire** line (excluding the line's trailing newline) |

Store them as booleans once at the start of `grep()`:

```text
list_only     = "-l" in flag_tokens
print_numbers = "-n" in flag_tokens
ignore_case   = "-i" in flag_tokens
invert        = "-v" in flag_tokens
entire_line   = "-x" in flag_tokens
```

Unknown tokens: ignore.

Do not implement clustered short options (`-ni`) unless you want extra robustness. The documented/test interface uses space-separated tokens.

### Flag precedence

- `-l` **wins over** `-n` (and over filename/line-number prefixes). When `-l` is set, output is only `"{filename}\n"` for each file that has at least one match. Never print line text or line numbers.
- `-i`, `-v`, and `-x` compose. They all affect the boolean “does this line match?” predicate; they do not change output shape except through which lines/files are selected.
- `-n` only applies to content-line output (not to `-l` output).

---

## 4. Architecture

Keep the module small. Suggested internal structure (names are illustrative):

```text
grep(pattern, flags, files)
  ├─ parse flags into booleans
  ├─ multi_file = len(files) > 1
  ├─ for each filename in files (given order):
  │     open file
  │     for each line (1-based):
  │         if line_matches(...):
  │             if list_only: emit filename, stop this file
  │             else: emit formatted line
  └─ return "".join(emitted)
```

Three concerns, keep them separate:

1. **Match predicate** – given one line body + pattern + `-i/-x/-v`, return bool.
2. **Output formatter** – given filename, line number, raw line, flags, and `multi_file`, return one output record.
3. **Driver** – walk files and lines, collect records.

No classes are required. A few nested functions or module-private helpers are fine.

---

## 5. Reading lines

Iterate the file object directly. Each `line` usually includes a trailing `\n` because the fixtures all end with a newline.

### Line body vs raw line

- **Raw line**: exactly what the file iterator yields (used for output of the text itself).
- **Line body**: the raw line with **at most one trailing `\n` removed**. Do **not** use `str.strip()` or `rstrip()` without arguments — that would drop trailing spaces, which would break `-x`.

Recommended:

```python
body = line[:-1] if line.endswith("\n") else line
```

`rstrip("\n")` is also acceptable because it only strips the newline character, not spaces.

Do not strip `\r` unless you are being extra defensive; fixtures use `\n` only.

### Line numbers

`enumerate(handle, start=1)`. Numbers are decimal, no padding, no `0` prefix.

### Empty files

Zero iterations → no matches for that file (including under `-v`, because there are no lines that fail to match).

### Last line without newline

Fixtures always terminate files with `\n`, so every yielded line should already end in `\n`. For robustness: if you emit a raw line that does not end in `\n`, append `\n` so every output record is newline-terminated. The function’s return value is a concatenation of such records.

---

## 6. Match algorithm (fixed string)

Work only on `body` and `pattern`. Never include the trailing `\n` in the comparison (otherwise `-x` would never match).

### Case folding (`-i`)

If `ignore_case`, compare using `.lower()` on both sides. ASCII is sufficient (fixture text is ASCII). Do not use locale-dependent case conversion.

```text
left  = body.lower()    if ignore_case else body
right = pattern.lower() if ignore_case else pattern
```

### Positive match (before invert)

- If `entire_line` (`-x`): `left == right`
- Else (substring): `right in left`

This is ordinary Python membership. An empty `pattern` is a substring of every line (`"" in left` is `True`). That is correct fixed-string behavior.

**Not regex.** Characters like `.`, `*`, `[`, `(` in the pattern are literal.

### Invert (`-v`)

```text
matched = positive_match
if invert:
    matched = not matched
```

A line is collected iff `matched` is true **after** applying `-v`.

### Combinations (truth table)

| `-x` | `-i` | `-v` | Line is kept when… |
|------|------|------|--------------------|
| no   | no   | no   | `pattern` is a substring of `body` |
| no   | yes  | no   | `pattern.lower()` is a substring of `body.lower()` |
| yes  | no   | no   | `body == pattern` |
| yes  | yes  | no   | `body.lower() == pattern.lower()` |
| *    | *    | yes  | the corresponding positive test is **false** |

Example (from README / typical suite):

- Pattern `"OF ATREUS, AGAMEMNON, KING OF MEN."` with `-n -i -x` on `iliad.txt` matches line 9 because the whole line equals the pattern ignoring case.

---

## 7. Output format

Build a list of strings and `"".join` them. Do **not** join with `'\n'` after stripping newlines; keep each record self-terminated.

Let `text` be the raw file line, guaranteed to end with `\n` (append if missing).

### 7.1 `-l` (file-name mode)

For each file, if **any** line matches (after `-i/-x/-v`):

```text
"{filename}\n"
```

Then **stop reading that file** (further matches cannot change the result).

Files with no matching line contribute nothing.

Order: same as `files`. A file is emitted at most once, even if many lines match.

`-n` is ignored here. Filename is **not** repeated as `file:file`. Just the name.

This applies to both single-file and multi-file invocations. `-l` always prints names, even when `len(files) == 1`.

### 7.2 Content-line mode (no `-l`)

Prefix rules:

1. If `len(files) > 1`: start with `"{filename}:"`.
2. If `-n`: then `"{line_number}:"`.
3. Then the raw line text (which already includes `\n`).

The filename-vs-single-file decision is based on **`len(files)`**, not on how many files actually produced hits. Searching three files and matching in only one still prefixes that one hit with `iliad.txt:`.

Concrete shapes:

| Situation | Output record |
|-----------|----------------|
| 1 file, no `-n` | `{line}` |
| 1 file, `-n` | `{n}:{line}` |
| N>1 files, no `-n` | `{file}:{line}` |
| N>1 files, `-n` | `{file}:{n}:{line}` |

No extra spaces around `:`.

### 7.3 Empty result

If nothing was collected, return `""` (not `"\n"`).

### 7.4 Trailing newline of the whole result

Because every record ends with `\n`, a non-empty result always ends with `\n`. That matches `assertMultiLineEqual` expectations such as:

```text
"Of Atreus, Agamemnon, King of men.\n"
```

and multi-line results:

```text
"3:Nor how it may concern my modesty,\n5:But I beseech your grace that I may know\n..."
```

---

## 8. Worked examples (use these as mental tests)

Fixture contents are in `public_test.py` (`FILE_TEXT`). Line numbers below are 1-based.

### Single file, one match, no flags (public test)

```text
grep("Agamemnon", "", ["iliad.txt"])
→ "Of Atreus, Agamemnon, King of men.\n"
```

### Single file, `-n`

```text
grep("Forbidden", "-n", ["paradise-lost.txt"])
→ "2:Of that Forbidden Tree, whose mortal tast\n"
```

### Single file, `-i`

```text
grep("FORBIDDEN", "-i", ["paradise-lost.txt"])
→ "Of that Forbidden Tree, whose mortal tast\n"
```

### Single file, `-l`

```text
grep("Forbidden", "-l", ["paradise-lost.txt"])
→ "paradise-lost.txt\n"
```

### Single file, `-x`

```text
grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])
→ "With loss of Eden, till one greater Man\n"
```

### Single file, several matches, no flags

```text
grep("may", "", ["midsummer-night.txt"])
→ three lines (3, 5, 6 of that file), each with its original text + "\n"
```

### Single file, `-x` that misses substring-only hits

```text
grep("may", "-x", ["midsummer-night.txt"])
→ ""
```

### Single file, `-v`

```text
grep("Of", "-v", ["paradise-lost.txt"])
→ every line whose body does not contain the substring "Of"
  (case-sensitive: "Of" at start matches; "of" later does not count as a hit
   for the positive test, so those lines are kept under -v)
```

Be careful: `"Of"` is a substring of `"Of Mans..."`, `"Of that..."`, `"Of Oreb..."`. It is **not** a substring of `"Brought Death..."`. Implement substring, not “word”, matching.

### Single file, `-n -l` (`-l` wins)

```text
grep("ten", "-n -l", ["iliad.txt"])
→ "iliad.txt\n"
```

(`"ten"` is a substring of iliad line 2, `"His wrath pernicious, who ten thousand woes"`. Because `-l` is set, print only the file name; `-n` is ignored.)

### Single file, `-n -i -x`

```text
grep("OF ATREUS, AGAMEMNON, KING OF MEN.", "-n -i -x", ["iliad.txt"])
→ "9:Of Atreus, Agamemnon, King of men.\n"
```

### Multiple files, one match, no flags

```text
grep("Agamemnon", "", ["iliad.txt", "midsummer-night.txt", "paradise-lost.txt"])
→ "iliad.txt:Of Atreus, Agamemnon, King of men.\n"
```

Filename prefix is required because `len(files) == 3`.

### Multiple files, `-n`

Hits for `"that"` typically:

```text
midsummer-night.txt:5:But I beseech your grace that I may know
midsummer-night.txt:6:The worst that may befall me in this case,
paradise-lost.txt:2:Of that Forbidden Tree, whose mortal tast
paradise-lost.txt:6:Sing Heav'nly Muse, that on the secret top
```

Each followed by `\n`, concatenated in that order.

### Multiple files, `-l`

```text
grep("who", "-l", [iliad, midsummer, paradise])
→ "iliad.txt\nparadise-lost.txt\n"
```

(`who` appears in iliad and paradise-lost, not in midsummer-night.)

### Multiple files, `-n -i -x`

```text
grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", [all three])
→ "paradise-lost.txt:4:With loss of Eden, till one greater Man\n"
```

### No matches

```text
grep("Gandalf", "-n -l -x -i", ["iliad.txt"])
→ ""
```

---

## 9. Edge-case checklist

Implement and mentally verify all of these:

1. **Empty flags string** — `"".split() == []`; all flag booleans false.
2. **Flag order** — `"-i -n"` equals `"-n -i"`.
3. **Duplicate flags** — `"-n -n"` is just `-n`.
4. **`-l` + `-n`** — names only.
5. **`-l` + `-v`** — emit a file if it has **at least one non-matching line**. A file whose every line matches the pattern is omitted. An empty file is omitted.
6. **`-l` + `-x` + `-i`** — name-only output, match predicate still full-line case-insensitive.
7. **`-v` + `-x`** — keep every line whose body is **not** exactly the pattern (after optional case fold). This can emit almost the whole file.
8. **Multiple files, matches in a subset** — still prefix with filename.
9. **Single file without `-l`** — never prefix the filename.
10. **Line numbers** start at 1 and count **every** line, including lines that do not match. Numbers on output lines are the original file line numbers, not a match index.
11. **Case-insensitive substring** — `"ACHILLES"` / `-i` on `iliad.txt` hits `"Achilles sing..."` and `"The noble Chief Achilles..."`.
12. **Case-sensitive default** — `"agamemnon"` without `-i` does **not** match `"Agamemnon"`.
13. **Pattern contained in a longer word** — `"ten"` matches inside `"thousand"` if that substring occurs. Do not implement whole-word matching.
14. **Spaces in the pattern are significant** — leading/trailing spaces in `pattern` must be kept.
15. **Do not search the filename** as if it were content, except that `-l` prints names of files that had content matches.
16. **File order** is the order of `files`, not sorted.
17. **Within a file**, emit matches in file order.
18. **Return type is `str`**, never a `list`.
19. **Must use `open`** so `grep.open` mocking works.
20. **Do not close-then-reopen unnecessarily**; one pass per file is enough.
21. **Encoding**: default text mode is fine; fixtures are ASCII.
22. **Missing files**: tests only open the three known names. No need for custom error messages; letting `open` raise is acceptable if a name is unknown (the mock raises `RuntimeError`).
23. **Empty `files` list**: loop zero times, return `""`. Unlikely in tests, cheap to handle.
24. **Empty pattern**: without `-x`, every line matches; with `-x`, only empty bodies match; `-v` inverts as usual.

---

## 10. Suggested implementation sketch

This is a guide, not required wording. Logic must be equivalent.

```python
def grep(pattern, flags, files):
    tokens = flags.split()
    list_only = "-l" in tokens
    print_numbers = "-n" in tokens
    ignore_case = "-i" in tokens
    invert = "-v" in tokens
    entire_line = "-x" in tokens
    multi_file = len(files) > 1

    needle = pattern.lower() if ignore_case else pattern
    out = []

    for filename in files:
        with open(filename) as handle:
            for line_no, raw in enumerate(handle, start=1):
                body = raw[:-1] if raw.endswith("\n") else raw
                haystack = body.lower() if ignore_case else body
                positive = (haystack == needle) if entire_line else (needle in haystack)
                if invert:
                    keep = not positive
                else:
                    keep = positive
                if not keep:
                    continue

                if list_only:
                    out.append(filename + "\n")
                    break

                if not raw.endswith("\n"):
                    raw = raw + "\n"

                prefix = ""
                if multi_file:
                    prefix += filename + ":"
                if print_numbers:
                    prefix += str(line_no) + ":"
                out.append(prefix + raw)

    return "".join(out)
```

Notes on the sketch:

- `break` after a `-l` hit is an optimization and also the correct “one name per file” behavior.
- Prefix concatenation (`file:` then `n:`) produces `file:n:line` for multi-file `-n`.
- No regex, no extra dependencies, no writes, stdlib only.

---

## 11. What not to do

- Do not call the system `grep` binary.
- Do not compile `pattern` as a regular expression.
- Do not `strip()` full lines (would drop meaningful trailing spaces).
- Do not use 0-based line numbers.
- Do not prefix filenames when exactly one file was passed, unless `-l` is set.
- Do not omit the filename prefix when multiple files were passed, even if only one file hits.
- Do not return a list of lines.
- Do not add a trailing extra newline beyond per-record `\n` (no `"\n\n"` at end unless a matched line is empty).
- Do not read files from disk by constructing paths outside what `open(filename)` would do; tests intercept `open`.
- Do not import or read held-out tests, canonical JSON, or network resources.

---

## 12. Verification strategy (for the implementer)

1. Run `python -m unittest public_test.py` — must pass the single public case.
2. Mentally / locally (inside the workspace only) check the worked examples in §8 against `FILE_TEXT` in `public_test.py`.
3. Confirm `open` is used so the mock applies.
4. Confirm return values always either `""` or a string whose every record ends with `\n`.

The implementer should only edit `grep.py`. This plan file is the spec for that edit.
