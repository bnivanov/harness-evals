# grep.py implementation guide

## Contract

```python
def grep(pattern: str, flags: str, files: list[str]) -> str:
```

- `pattern`: fixed substring (not a regex). Match literally.
- `flags`: space-separated flag tokens, or `""`. Tokens are exactly `-n`, `-l`, `-i`, `-v`, `-x`. Combinations appear as e.g. `"-n -i -x"`.
- `files`: one or more filenames, in search order.
- Return: one string of result lines, each terminated by `\n`. No matches → `""`.

Tests patch `grep.open`. Use builtin `open(filename)` (text mode, default encoding). Do not use `pathlib`, `io.open`, or `builtins.open` via a different binding.

## Algorithm

1. Parse flags once: `flag_set = set(flags.split())`. Membership tests for `-n`, `-l`, `-i`, `-v`, `-x`.
2. Prepare the comparison pattern: if `-i`, `needle = pattern.lower()`, else `needle = pattern`.
3. `multi = len(files) > 1`. Filename prefix is required iff `multi` **and** not `-l`.
4. Accumulate output pieces in a list; `return "".join(pieces)` at the end.
5. For each `filename` in `files` (given order):
   - `with open(filename) as fh:`
   - Enumerate lines 1-based: `for lineno, raw in enumerate(fh, start=1)`.
   - Strip only a trailing `\n` for matching and for emitted content: `line = raw.rstrip("\n")`. Do not strip other whitespace.
   - Haystack: `line.lower()` if `-i` else `line`.
   - Match:
     - `-x`: `haystack == needle`
     - else: `needle in haystack` (empty needle matches every line)
   - If `-v`: invert the boolean.
   - On a match:
     - If `-l`: append `filename + "\n"` and **stop scanning this file** (still process later files). `-l` wins over `-n`; never emit line text or numbers.
     - Else format one output line (see below) and continue.

## Output format (non-`-l`)

Concatenate prefixes then the line body then `\n`:

| Condition | Prefix |
|---|---|
| single file, no `-n` | (none) |
| single file, `-n` | `"{lineno}:"` |
| multiple files, no `-n` | `"{filename}:"` |
| multiple files, `-n` | `"{filename}:{lineno}:"` |

Body is the line **without** the original newline. Always append `\n` after the body.

Examples:

- `grep("Agamemnon", "", ["iliad.txt"])` → `Of Atreus, Agamemnon, King of men.\n`
- `grep("Forbidden", "-n", ["paradise-lost.txt"])` → `2:Of that Forbidden Tree, whose mortal tast\n`
- multiple files, same hit → `iliad.txt:Of Atreus, Agamemnon, King of men.\n`
- multiple files + `-n` → `iliad.txt:9:Of Atreus, Agamemnon, King of men.\n`
- `-l` even for one file → `paradise-lost.txt\n`

## Flag semantics and combinations

| Flag | Effect |
|---|---|
| `-i` | Compare lowercased pattern and lowercased line. Original line casing is still emitted. |
| `-x` | Whole-line equality after newline strip, not substring. |
| `-v` | Keep lines that **fail** the (possibly `-x`/`-i`) test. |
| `-n` | 1-based line numbers; ignored when `-l` is set. |
| `-l` | File names only, one per file that has ≥1 selected line; skip rest of that file. |

Independence:

- `-i` applies before invert/whole-line: `-x -i` is case-insensitive full-line equality; `-v -i` inverts the case-insensitive substring test.
- `-v -x`: emit lines that are **not** exactly the pattern.
- `-n -l`: emit only filenames (`-l` takes precedence).
- `-l -v`: list files that contain at least one non-matching line (a file whose every line matches is omitted).
- Several matches in one file: emit in file order; with `-l`, still one name.

## Data structures

- `set` of flag tokens: O(1) checks, order-independent.
- `list[str]` of output fragments: avoid quadratic string concat.
- No extra indexes. Sequential scan is enough.

No classes. One function plus, if useful, a tiny local helper `matches(line) -> bool` that applies `-i`/`-x`/`-v`. Keep helpers in `grep.py` only if they simplify the loop; inlining is fine.

## File / line edge cases

- Files are read fully in argument order. Do not sort names.
- Test fixtures end with `\n`; still use `rstrip("\n")` so a last line without newline does not keep a phantom character or miss a match.
- Do not rstrip `\r` unless it is part of `\n` handling; fixtures are Unix `\n`.
- Preserve internal spaces and punctuation exactly (`Heav'nly`, `Ades`, etc.).
- Empty `pattern`: substring match is true for every line; `-x` matches only empty lines.
- No matches (or `-v` that excludes everything): return `""`, not `"\n"`.
- Unknown filenames: let `open` raise (tests only open known names).
- Do not interpret `pattern` as regex: no `re`, no glob in the needle.
- `flags.split()` already treats `""` and extra spaces as no tokens. Do not strip the leading `-` or accept bundled `-nix`.
- `-l` output never includes `:` or line numbers, single or multi file.

## Suggested loop (reference shape, not copy-paste requirement)

```text
flags_set = set(flags.split())
needle = pattern.lower() if "-i" in flags_set else pattern
out = []
multi = len(files) > 1

for name in files:
    with open(name) as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            hay = line.lower() if "-i" in flags_set else line
            hit = (hay == needle) if "-x" in flags_set else (needle in hay)
            if "-v" in flags_set:
                hit = not hit
            if not hit:
                continue
            if "-l" in flags_set:
                out.append(name + "\n")
                break
            prefix = ""
            if multi:
                prefix += name + ":"
            if "-n" in flags_set:
                prefix += f"{n}:"
            out.append(prefix + line + "\n")

return "".join(out)
```

## Verification targets (beyond the one public test)

Public test only covers one file, one substring hit, no flags. The implementation must also satisfy:

1. One file, `-n` / `-i` / `-l` / `-x` / `-v` each alone.
2. One file, several hits; `-x` that matches none of the substrings → `""`.
3. Combined `-n -i -x`.
4. `-n -l` → filename only.
5. `-v -x` (and `-v -i`).
6. Zero hits under any flag mix → `""`.
7. Two or three files: prefix `file:`; only files with hits appear; order preserved.
8. Multi-file `-l`: each matching file once, in input order, no content.
9. Multi-file `-n`: `file:lineno:content\n`.
10. Multi-file `-i` / `-v` / `-x` same prefix rules as unflagged multi-file.

Do not add tests in this planning step. Implement only `grep.py` later.
