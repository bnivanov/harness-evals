# grep.py Implementation Guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: literal fixed string (never a regex).
- `flags`: space-separated flag tokens, e.g. `""`, `"-n"`, `"-n -i -x"`. Unknown tokens ignored.
- `files`: one or more filenames, searched in given order.
- Return: concatenated result lines, each terminated by `\n`. No matches → `""`.

Public tests patch `grep.open` (`create=True`) and feed `io.StringIO`. **Must call builtin `open(filename)`** (text mode, default encoding). Do not use `pathlib`, `io.open`, or `Path.open` — the mock will not intercept them.

Do not import extra packages. Stdlib only if needed (none required).

---

## Flag semantics

Parse once:

```python
flag_set = set(flags.split())  # "" → empty set
n_flag = "-n" in flag_set  # prepend 1-based line number
l_flag = "-l" in flag_set  # emit filenames only
i_flag = "-i" in flag_set  # case-insensitive
v_flag = "-v" in flag_set  # invert match
x_flag = "-x" in flag_set  # whole-line match
```

Flags combine independently except:

| Combination | Behavior |
|---|---|
| `-l` + anything | `-l` wins on **output shape**. Still honor `-i`/`-v`/`-x` for *whether* a file matches. Ignore `-n` (no line numbers). |
| `-n` without `-l` | Line numbers after optional filename, before the text. |
| `-i` + `-x` | Case-insensitive equality of the full line. |
| `-v` + `-x` | Keep lines that are **not** exact (possibly case-insensitive) matches. |
| `-n` + `-v` | Numbers are **original file line numbers**, not output-row indices. |

Filename prefix: when `len(files) > 1` **and not** `-l`, every content line is prefixed with `{filename}:`. With `-l`, always print the bare filename (even for a single file).

Output shapes (each record ends with `\n`):

| files | flags | one record |
|---|---|---|
| 1 | (none) | `{line}` |
| 1 | `-n` | `{lineno}:{line}` |
| >1 | (none) | `{file}:{line}` |
| >1 | `-n` | `{file}:{lineno}:{line}` |
| any | `-l` | `{file}` |

Colon placement: number comes **after** filename when both apply: `iliad.txt:9:Of Atreus, ...`

---

## Matching algorithm

For each file, iterate lines in order. `for line in f` keeps the terminator on every line except a possible last line without `\n`.

**Compare against the line with a single trailing `\n` or `\r\n` removed.** Do not strip other whitespace. Apostrophes and punctuation stay.

```python
def line_body(raw: str) -> str:
    if raw.endswith("\r\n"):
        return raw[:-2]
    if raw.endswith("\n"):
        return raw[:-1]
    return raw
```

Needle / haystack:

1. `hay = line_body(raw)`
2. `needle = pattern`
3. If `-i`: `hay = hay.lower()`; `needle = needle.lower()` (`.casefold()` also fine; tests are ASCII).
4. `matched = (hay == needle) if x_flag else (needle in hay)`
5. If `-v`: `matched = not matched`

Literal search: `in` / `==` only. Never `re`. A pattern like `a.*b` is four characters, not a regex.

Empty `pattern`:

- Without `-x`: `"" in hay` is True for every line → all lines match (or none, if `-v`).
- With `-x`: only empty bodies match.

---

## File loop and output

```
results = []  # list of strings that already include trailing \n
multi = len(files) > 1

for filename in files:
    with open(filename) as f:
        if l_flag:
            for raw in f:
                if matches(raw):
                    results.append(filename + "\n")
                    break
            continue

        for lineno, raw in enumerate(f, start=1):
            if not matches(raw):
                continue
            body = line_body(raw)
            parts = []
            if multi:
                parts.append(filename)
            if n_flag:
                parts.append(str(lineno))
            prefix = (":".join(parts) + ":") if parts else ""
            results.append(prefix + body + "\n")

return "".join(results)
```

Always emit `\n` after the body even if the source line lacked one. Test fixtures all end with `\n`; this keeps the return value uniform.

`-l` stop-at-first-match is required for correctness only in the sense that each matching file appears **once**, in file-list order.

Do not close/reopen beyond the `with`. Do not read files not in `files`.

---

## Worked examples (same fixtures as public_test.py)

`iliad.txt` lines 1–9, `midsummer-night.txt` 1–7, `paradise-lost.txt` 1–8.

| Call | Result |
|---|---|
| `grep("Agamemnon", "", ["iliad.txt"])` | `Of Atreus, Agamemnon, King of men.\n` |
| `grep("Forbidden", "-n", ["paradise-lost.txt"])` | `2:Of that Forbidden Tree, whose mortal tast\n` |
| `grep("FORBIDDEN", "-i", ["paradise-lost.txt"])` | `Of that Forbidden Tree, whose mortal tast\n` |
| `grep("Forbidden", "-l", ["paradise-lost.txt"])` | `paradise-lost.txt\n` |
| `grep("With loss of Eden, till one greater Man", "-x", ["paradise-lost.txt"])` | that full line + `\n` |
| `grep("OF ATREUS, Agamemnon, KING OF MEN.", "-n -i -x", ["iliad.txt"])` | `9:Of Atreus, Agamemnon, King of men.\n` |
| `grep("may", "", ["midsummer-night.txt"])` | lines 3, 5, 6 (substring `may`) |
| `grep("may", "-n", ["midsummer-night.txt"])` | `3:...`, `5:...`, `6:...` |
| `grep("may", "-x", ["midsummer-night.txt"])` | `""` |
| `grep("ACHILLES", "-i", ["iliad.txt"])` | lines 1 and 8 |
| `grep("Of", "-v", ["paradise-lost.txt"])` | lines that do **not** contain `Of` (case-sensitive): 3, 5, 6, 8 |
| `grep("Gandalf", "-n -l -x -i", ["iliad.txt"])` | `""` |
| `grep("ten", "-n -l", ["iliad.txt"])` | `iliad.txt\n` (`-l` beats `-n`) |
| `grep("Illustrious into Ades premature,", "-x -v", ["iliad.txt"])` | all iliad lines except line 4 |
| `grep("Agamemnon", "", [iliad, midsummer, paradise])` | `iliad.txt:Of Atreus, Agamemnon, King of men.\n` |
| `grep("who", "-l", [all three])` | `iliad.txt\nparadise-lost.txt\n` |
| `grep("WITH LOSS OF EDEN, TILL ONE GREATER MAN", "-n -i -x", [all three])` | `paradise-lost.txt:4:With loss of Eden, till one greater Man\n` |
| `grep("who", "-n -l", [all three])` | `iliad.txt\nparadise-lost.txt\n` |

`-i` substring `TO` across three files matches `to`/`To`/`into` (because `to` is in `into`). Include those lines.

---

## Edge cases

1. **No matches** — return `""`, never `None`.
2. **Single vs multiple files** — filename prefix iff `len(files) > 1` and not `-l`.
3. **`-l` + no hits in a file** — omit that file; later files still scanned.
4. **`-l` + `-v`** — file is listed if **any** line fails the (possibly `-i`/`-x`) match. Empty file: no line fails → omit.
5. **Line numbers** — 1-based, every physical line counts, including non-matches skipped by `-v`.
6. **Trailing newline on last line** — fixtures include it; still rstrip only one terminator for compare, always re-add `\n` on emit.
7. **Literal metacharacters** — `"."` matches a period character, not “any char”.
8. **Overlapping flags string** — parse tokens (`flags.split()`), not substring. `"-n" in "-n"` is fine; do **not** use `"-n" in flags` if that could false-positive; `split()` tokens are the spec.
9. **File order** — output order = `files` order, then line order inside each file.
10. **Missing file** — not in public fixtures; let `open` raise. Do not catch.
11. **`pattern` with spaces** — whole string is the needle; do not split it.
12. **Windows `\r\n`** — strip `\r\n` as one terminator so `-x` still matches.

---

## Structure (keep grep.py small)

One module, no classes required:

1. `_parse_flags(flags) -> frozenset` or five booleans.
2. `_body(raw) -> str` — terminator strip.
3. `_is_match(body, pattern, i_flag, x_flag, v_flag) -> bool`.
4. `_format_line(filename, lineno, body, multi, n_flag) -> str`.
5. `grep(...)` — orchestration above.

No regex, no global mutable state, no prints. Return the string.

---

## Verification (implementer, not planner)

- `python -m unittest public_test.py` must pass (open mock + one-file no-flag case).
- Mentally / locally cover: `-n`, `-l`, `-i`, `-v`, `-x`, combos, 1 file vs 3 files, empty result.
- Do not add tests in this repo unless asked.

## Out of scope

- Regex, recursive directories, stdin, binary files, color, `-c`/`-o`/`-A`/`-B`.
- Editing tests or fetching canonical-data.json.
- Changing `grep.py` in the planning step.
