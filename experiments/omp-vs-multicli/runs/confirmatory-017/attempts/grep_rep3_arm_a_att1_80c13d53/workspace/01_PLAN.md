# grep.py Implementation Plan

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: fixed string (not a regex).
- `flags`: zero or more options, as a single string (public test uses `""`; combinations are space-separated, e.g. `"-n -i -x"`).
- `files`: one or more file names, searched in list order.
- Return: concatenation of result lines, each terminated by `\n`. No matches → `""`.

Tests patch `grep.open` (and wrap `io.StringIO`). Open files only via the builtin `open` so the mock applies. Do not import a different `open`.

## Flags (parse once)

| Flag | Meaning |
|------|---------|
| `-n` | Prefix 1-based line number and `:` before the line text (after filename if present). |
| `-l` | Emit each matching file name once; ignore line text and `-n`. |
| `-i` | Case-insensitive compare. |
| `-v` | Invert: a line is selected iff it fails the match. |
| `-x` | Whole-line match instead of substring. |

Parse by splitting `flags` on whitespace and collecting tokens into a set (e.g. `flag_set = set(flags.split())`). Unknown tokens should not appear. Empty `flags` → empty set.

Do not implement clustered short options (`-nix`) unless a token is exactly that form; the specified interface uses separate tokens.

Independence: `-i`, `-v`, `-x` affect *which* lines/files match. `-n` and `-l` affect *how* results are formatted. `-l` wins over `-n`: if `-l` is set, never print numbers or line bodies.

## Algorithm

```
parse flags
multi = len(files) > 1
out = []

for each file in files (given order):
    matched_this_file = False
    with open(file) as fh:
        for 1-based lineno, raw in enumerate(fh, start=1):
            text = raw.rstrip("\n")          # match and emit without embedded newline
            selected = line_selected(text, pattern, flags)
            if not selected:
                continue
            if -l:
                matched_this_file = True
                break                        # one hit is enough
            out.append(format_line(file, lineno, text, multi, -n))
    if -l and matched_this_file:
        out.append(file + "\n")

return "".join(out)
```

`open` must be the function looked up as `open` inside `grep.py` (builtin). Use a context manager. Read sequentially; do not load extra copies beyond the current line.

## Matching (`line_selected`)

Work only on newline-stripped `text` and the original `pattern`. Never treat `pattern` as a regex (`re` unused).

1. If `-i`: compare `text.casefold()` vs `pattern.casefold()` (or `.lower()` on both; `casefold` is the more correct Unicode fold; ASCII-only fixtures make them equivalent).
2. Needle/haystack:
   - `-x`: equality (`folded_text == folded_pattern`).
   - else: substring (`folded_pattern in folded_text`).
3. If `-v`: return `not matched`; else return `matched`.

Apply `-v` after `-x`/`-i`, not before. Combinations:

- `-x -i`: case-insensitive full-line equality.
- `-v -x`: keep lines that are *not* exactly the pattern.
- `-v -i`: invert after case-fold substring (or full-line if `-x`).
- `-v -l`: list files that have at least one *non*-matching line (because selection is inverted).

Empty `pattern`: substring match is true for every line; `-x` matches only empty lines (`text == ""`).

## Output formatting (`format_line`)

Always end with `\n`. Use stripped `text` then add a single `\n` so missing final newlines in a file still produce POSIX-style output lines.

Let `show_file = (len(files) > 1)` — computed from the original list, not from how many files actually matched.

| Condition | Format |
|-----------|--------|
| `-l` | `{filename}\n` (once per matching file; handled in the outer loop) |
| `show_file` and `-n` | `{filename}:{lineno}:{text}\n` |
| `show_file` and not `-n` | `{filename}:{text}\n` |
| not `show_file` and `-n` | `{lineno}:{text}\n` |
| not `show_file` and not `-n` | `{text}\n` |

Filename prefix is *only* when searching multiple files, except `-l`, which always prints names (even for one file). README: “When searching in multiple files, each matching line is prepended by the file name and a colon.”

`-n` places the number after the filename (if present), then `:`, then the line.

## File I/O details

- Search `files` in the given order; emit in discovery order.
- Line numbers are per-file, 1-based, counting every physical line (including lines later rejected by the match).
- `rstrip("\n")` only; do not strip spaces or `\r` unless you also normalize `\r\n`. Fixture data is `\n`-terminated. If a line is `foo\r\n`, `rstrip("\n")` leaves `foo\r`, which would break `-x`. Prefer `line.rstrip("\r\n")` so CRLF still matches the visible content. Fixtures use `\n` only; either is fine if applied consistently to every line.
- Do not rstrip interior spaces; leading/trailing spaces on the line are significant for `-x`.

## Edge cases

| Case | Behavior |
|------|----------|
| No matching lines | `""` |
| One file, one/several matches, no flags | Bodies only, order preserved |
| One file, `-l` | `{name}\n` if any selected line, else `""` |
| One file, `-n` | `{n}:{text}\n` |
| Several files, any line output | Always `{file}:` prefix (and `{file}:{n}:` if `-n`) |
| Several files, `-l` | Matching names, one per file, input order, each `\n`-terminated |
| `-l` plus `-n` | `-l` only (file flag takes precedence) |
| `-x` with a substring that is not the full line | No match |
| `-i` | Fold both sides; do not mutate caller strings beyond local copies |
| `-v` | Selected set is the complement of the matcher |
| Multiple flags | Parse all; matching flags compose; format flags: `-l` overrides `-n` |
| Pattern appears more than once on a line | Still one output line (line-oriented) |
| Same line content in two files | Both emitted, each with its own prefix when multi-file |
| File with no trailing newline on last line | Still emit that line with a trailing `\n` if selected |
| Empty file | No lines → not selected (even with `-v`, there is no line to invert) |
| `files` length 1 vs 2 | Prefix rule uses `len(files)`, not match count |

## Structure (single module, no extra public API)

Keep everything in `grep.py`. Suggested private helpers (names optional):

- `_parse_flags(flags: str) -> set[str]`
- `_matches(text: str, pattern: str, case_insensitive: bool, whole_line: bool) -> bool`
- `_format(filename: str, lineno: int, text: str, *, show_file: bool, show_lineno: bool) -> str`

`grep` remains the only export. No classes required.

## Non-goals

- Regex, context (`-A`/`-B`/`-C`), recursive search, stdin, exit codes, binary files.
- Writing to stdout; **return** the string (callers/tests compare return values).
- Touching tests or reading files other than those named in `files` via `open`.

## Verification against the public test

`grep("Agamemnon", "", ["iliad.txt"])` must return exactly:

```
Of Atreus, Agamemnon, King of men.\n
```

Single file, no flags, substring match, line 9 of `iliad.txt`.

## Implementation order

1. Flag parse + match helper (substring / `-x` / `-i` / `-v`).
2. Single-file scan and join.
3. Multi-file name prefix via `len(files) > 1`.
4. `-n` prefix.
5. `-l` short-circuit per file.
6. Confirm `-l` suppresses `-n` and still uses inverted/case/whole-line selection.
