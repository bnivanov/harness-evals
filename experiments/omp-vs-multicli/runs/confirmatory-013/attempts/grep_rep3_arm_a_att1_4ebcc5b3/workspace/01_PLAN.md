# grep.py — Implementation Guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- **pattern**: fixed string (literal substring / whole-line equality). Never treat as regex.
- **flags**: space-separated flag tokens (e.g. `""`, `"-n"`, `"-n -i -x"`). Use `flags.split()`; empty/whitespace-only → no flags. Do not support bundled tokens like `-ni` unless they appear as separate `-n` and `-i`.
- **files**: one or more paths, searched in the given order.
- **return**: a single string. Every emitted record ends with `\n`. No matches → `""`.

Tests patch `grep.open` (`create=True`). The implementation **must** call the builtin `open(filename)` (text mode, default encoding) so the patch intercepts it. Do not use `io.open`, `pathlib`, or `open` from another module.

---

## Flag model

Parse once into booleans (a small dataclass or five locals):

| Token | Meaning |
|-------|---------|
| `-n`  | Prefix 1-based line number. |
| `-l`  | Emit each matching **file name** once; suppress line text and `-n`. |
| `-i`  | Case-insensitive match. |
| `-v`  | Invert: keep lines that **fail** the match predicate. |
| `-x`  | Match the **entire** line, not a substring. |

Unknown tokens: ignore (tests only send the five above).

Matching still uses `-i` / `-x` / `-v` when `-l` is set. `-l` only changes **what is printed** and **when to stop** reading a file.

---

## Matching

For each physical line from the file:

1. Drop a single trailing `\n` (use `line[:-1] if line.endswith("\n") else line`). Do **not** strip other whitespace; leading/trailing spaces are significant for `-x`.
2. Build the predicate on the stripped text `text` and `pattern`:

   ```
   left, right = (text.lower(), pattern.lower()) if case_insensitive else (text, pattern)
   matched = (left == right) if whole_line else (right in left)
   keep = (not matched) if invert else matched
   ```

3. Fixed-string only: `in` / `==`, never `re`.

Line numbers are 1-based and count **every** line, including those discarded by `-v`.

---

## Per-file scan

```
for filename in files:          # given order
    with open(filename) as fh:
        for lineno, raw in enumerate(fh, start=1):
            ...
```

- Read sequentially; do not slurp unless convenient (either is fine).
- `-l`: on the first kept line, append `filename + "\n"` and **break** (do not list the same file twice).
- Without `-l`: for each kept line, append one formatted record (see below).
- File with zero kept lines: emit nothing for that file.
- Empty file: no lines → no output (even with `-v`).

Missing files are out of scope (the mock raises if the name is unknown). Do not catch `open` errors.

---

## Output format

`multi = len(files) > 1`  — filename prefix depends on how many files were **passed**, not how many matched.

Without `-l`, each kept line becomes:

| Condition | Record |
|-----------|--------|
| single file, no `-n` | `{text}\n` |
| single file, `-n` | `{lineno}:{text}\n` |
| multiple files, no `-n` | `{filename}:{text}\n` |
| multiple files, `-n` | `{filename}:{lineno}:{text}\n` |

With `-l` (any number of files, `-n` ignored):

| Record |
|--------|
| `{filename}\n` |

Concatenate records in scan order. Do not add a trailing extra newline beyond those records.

---

## Algorithm (reference)

```
parse flags → n, l, i, v, x
multi ← len(files) > 1
out ← []

for filename in files:
    with open(filename) as fh:
        for lineno, raw in enumerate(fh, 1):
            text ← strip trailing \n only
            if not keep(text, pattern, i, v, x):
                continue
            if l:
                out.append(filename + "\n")
                break
            prefix ← ""
            if multi:
                prefix += filename + ":"
            if n:
                prefix += str(lineno) + ":"
            out.append(prefix + text + "\n")

return "".join(out)
```

Helpers (keep them small; one module is enough):

- `_parse_flags(flags: str) ->` booleans or a tiny namespace.
- `_matches(text, pattern, ignore_case, whole_line) -> bool`  (no invert here).
- Invert applied at the call site: `keep = _matches(...) != invert`.

No classes required. No regex. No extra files.

---

## Edge cases (must handle)

- **Literal metacharacters** in `pattern` (`.`, `*`, `[`, etc.) match as characters.
- **Empty pattern**: substring `"" in text` is true for every line → keep all lines; with `-x`, keep only empty lines (`text == ""`). `-v` inverts those rules.
- **`-x` vs substring**: `"Agamemnon"` does not `-x`-match a longer line that merely contains it.
- **`-i` + `-x`**: case-fold both sides, then full-line equality.
- **`-i` substring**: `"AGAMEMNON"` matches `"... Agamemnon ..."`.
- **`-v`**: emit non-matching lines; combine with `-n` (numbers of those lines) and with `-x` (emit lines that are not exact matches).
- **`-v` + `-l`**: list files that contain **at least one** non-matching line (almost every non-empty file).
- **`-l` + `-n`**: names only; never `file:1:...`.
- **Several matches in one file**: one output record per kept line (or one name if `-l`).
- **Multiple files, mixed hits**: prefix every line record with its file; skip files with no hits; `-l` lists only files that hit, in argv order.
- **Same line, multiple occurrences** of the pattern: still one record (line-oriented).
- **Last line without `\\n`**: still eligible; output record always ends with `\\n`.
- **Whitespace-only flags string**: treat as no flags.
- **Single-file invocation**: never prefix `filename:` even if the name looks like a path.

---

## Verification notes (implementer)

- Public test: `grep("Agamemnon", "", ["iliad.txt"])` → `"Of Atreus, Agamemnon, King of men.\n"`.
- After implementation, that case plus flag combinations above are the acceptance surface. Do not add tests in this planning step.

## Out of scope

- Regex, recursive directories, stdin (`-` / no files), binary files, encodings, exit codes, color, context (`-A`/`-B`/`-C`).
- Do not edit `grep.py` in the planning phase; this document is the sole deliverable here.
