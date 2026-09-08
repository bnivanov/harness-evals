# transpose.py — Implementation Guide

## Goal

Implement `transpose(text: str) -> str` in `transpose.py`.

Input is a newline-separated character matrix (ragged rows allowed). Output is that matrix with rows and columns swapped, joined by `\n`.

Do not change tests. Do not add files beyond this plan and the implementation.

## Public contract

```python
def transpose(text):
    ...
```

- **Input:** `str`. Rows separated by `\n`. No trailing `\n` is required after the last row. Characters are Python Unicode code points (iterate the string; do not encode).
- **Output:** `str`. Rows separated by `\n`. No trailing `\n` after the last output row.
- **Empty input:** `""` → `""` (this is the only public test; it must pass).

Type hints are optional. Match the stub: one function, no extra public API.

## Semantics (from README)

Treat the input as a matrix of characters.

```
ABC          AD
DEF    →     BE
             CF
```

Rows become columns. Column `c` of the input, read top-to-bottom, becomes output row `c`, left-to-right.

### Ragged rows

When input rows have unequal length:

1. **Pad to the left with spaces.** If input row `r` has no character at column `c`, but some row *below* `r` does, emit a space at that position in the output.
2. **Do not pad to the right.** If no row at or below `r` has a character at column `c`, omit the cell. Do not append trailing spaces that were never in the input and are not required by (1).

README examples:

```
ABC          AD
DE     →     BE
             C
```

```
AB           AD
DEF    →     BE
              F
```

(The last output row is a space then `F`.)

### Character preservation

Every non-newline input character must appear in the output, **including spaces**. If a column’s bottom-most cells are spaces, the corresponding output row must keep those spaces on the right. You may *insert* spaces (left-padding). You must not *drop* original spaces.

Consequence: never `rstrip()` an output row. That would delete real trailing spaces.

## Data structures

- `rows: list[str]` — `text.split("\n")`. One string per input row. Empty rows are `""`.
- Transposed columns: an iterator/list of tuples, one per output row.
- Sentinel for a missing cell: `None` (not `" "`). This is the only way to tell “pad” from “this space was in the input”.

Do not build a dense 2D list of characters unless you also track which cells are real vs padded.

**Do not use `str.splitlines()`.** It drops a trailing empty row (`"A\n".splitlines() == ["A"]`) and splits on other Unicode line breaks. The matrix separator is `\n` only. Output join is `\n` only.

## Recommended algorithm

`itertools.zip_longest` with `fillvalue=None` is the direct encoding of the padding rule.

```text
rows = text.split("\n")
for each tuple produced by zip_longest(*rows, fillvalue=None):
    drop trailing None  # nothing below → no right pad
    map remaining None → " "  # something below → left pad
    join into an output row
join output rows with "\n"
```

Why this is correct:

- `zip_longest` walks by column index `0 .. max(len(row))-1`.
- A `None` means that input row was shorter than this column.
- Trailing `None`s = missing cells with no content further down the column = **do not pad right** → pop them.
- Interior `None`s = missing cells with content further down = **pad left** → `" "`.
- Real `' '` characters are not `None`, so they survive, including at the end of an output row.

### Worked traces

`""`

- `split` → `[""]`
- `zip_longest(*[""])` is `zip_longest("")` → no columns
- `"\n".join([])` → `""`

`"ABC\nDE"`

- columns: `('A','D')`, `('B','E')`, `('C', None)`
- drop trailing None on the last → `"AD"`, `"BE"`, `"C"`

`"AB\nDEF"`

- columns: `('A','D')`, `('B','E')`, `(None, 'F')`
- last has interior None → `"AD"`, `"BE"`, `" F"`

`"A\n"` (row `"A"` then empty row)

- columns: `('A', None)` → pop trailing None → `"A"`

`"\nA"` (empty row then `"A"`)

- columns: `(None, 'A')` → `" A"`

`"A \nB"` (A, space, newline, B)

- columns: `('A','B')`, `(' ', None)` → `"AB"`, `" "`
- the space is real input; it is kept as its own output row

`"A\nB "` (A, newline, B, space)

- columns: `('A','B')`, `(None, ' ')` → `"AB"`, `"  "`
- first space is left-pad; second is the original trailing space

### Reference shape (implement this, not a different API)

```python
from itertools import zip_longest

def transpose(text):
    rows = text.split("\n")
    out = []
    for col in zip_longest(*rows, fillvalue=None):
        cells = list(col)
        while cells and cells[-1] is None:
            cells.pop()
        out.append("".join(" " if c is None else c for c in cells))
    return "\n".join(out)
```

A compact equivalent of the trailing-None strip: walk `col` from the right until a non-`None` (or empty), then join the prefix. Do not use `str.rstrip`.

## Alternative (no itertools)

Pad each input row to `max(len(rows[j]) for j >= i)` — i.e. max length of this row and all rows below — using `str.ljust`. Lengths become non-increasing down the matrix. Then emit column `c` as `rows[r][c]` for every `r` with `c < len(padded[r])`.

Same results. Prefer `zip_longest` unless you want to avoid the import.

Do **not** `ljust` every row to the global max width and then `rstrip` the output: that deletes original trailing spaces.

## Edge cases the implementation must handle

| Case | Input (repr) | Output (repr) | Why |
|---|---|---|---|
| Empty | `""` | `""` | Public test |
| Single char | `"A"` | `"A"` | 1×1 |
| Single row | `"ABC"` | `"A\nB\nC"` | Row → column |
| Single column | `"A\nB\nC"` | `"ABC"` | Column → row |
| Rectangle | `"ABC\n123"` | `"A1\nB2\nC3"` | README square analogue |
| First row longer | `"ABC\nDE"` | `"AD\nBE\nC"` | No right pad |
| First row shorter | `"AB\nDEF"` | `"AD\nBE\n F"` | Left pad |
| Trailing newline | `"A\n"` | `"A"` | Empty last row, no right pad |
| Leading newline | `"\nA"` | `" A"` | Empty first row, left pad |
| Empty middle row | `"A\n\nB"` | `"A B"` | Interior pad |
| Input trailing space | `"A \nB"` | `"AB\n "` | Preserve real space |
| Pad + real space | `"A\nB "` | `"AB\n  "` | Both spaces kept |
| Only spaces | `"  "` | `" \n "` | Two space-rows |
| Two empty rows | `"\n"` | `""` | 2×0 matrix → no columns |
| Mixed jagged | `"11\n2\n333"` | `"123\n1 3\n  3"` | Independent columns |

Also:

- Interior spaces in words stay put (`"A B"` as a single row → `"A\n \nB"`).
- Non-ASCII: index by character, not byte (`"äB\nC"` is width 2, not 3).
- No `\r\n` handling. Tests use `\n`.
- Do not add a trailing newline on output.

## Complexity

Let `R` = number of rows, `C` = max row length, `N` = `len(text)`.

Time `O(R*C)` = `O(N)`. Space `O(R*C)` for the output. Fine for this problem; no need to micro-optimize.

## Pitfalls

1. **`rstrip` / `strip` on output rows** — fails character preservation.
2. **`fillvalue=' '`** without a sentinel — cannot drop right-pad without also dropping real spaces.
3. **`splitlines()`** — wrong empty-row and line-break behavior.
4. **Padding every row to global max** — extra right-pad spaces on short bottom rows.
5. **Forgetting empty input** — `max(len(r) for r in rows)` on `[""]` is 0; `zip_longest` on a single empty string yields no columns; both must return `""`, not an error.
6. **Joining with `""` instead of `"\n"`** — would glue output rows together.

## Verification

After implementing, run:

```text
python -m unittest public_test.py
```

That only covers `""`. Mentally (or with a throwaway snippet in the workspace, not a committed test file) check the README examples and the table above, especially:

- `"ABC\nDE"` → `"AD\nBE\nC"`
- `"AB\nDEF"` → `"AD\nBE\n F"`
- `"A\nB "` → `"AB\n  "` (spaces preserved)

Invariants:

- `transpose("") == ""`
- Non-newline characters in the input all appear in the output, in column-major order, with spaces possibly inserted (never deleted).
- Number of output rows equals `max(map(len, rows), default=0)`.
- Number of output columns (length of first output row, if any) equals the number of input rows that are long enough for column 0; later output rows are prefix-aligned and may be shorter.

## Out of scope

- In-place mutation, streaming, or a 2D-list API
- `\r\n` / `splitlines`
- Type checking beyond accepting `str`
- Extra helpers exported from `transpose.py`
