# list_ops.py — Implementation Guide

## Goal

Implement eight list operations in `list_ops.py` matching the stub signatures. Functional-style primitives: no Python builtins / methods that already perform the operation being implemented. Return new lists; never mutate inputs.

Public tests only cover `append([], [])`. The rest of the contract comes from `README.md` plus the Python-track conventions implied by the stub (`foldl` / `foldr` both take `function(acc, el)`). Held-out tests will exercise empties, non-empties, nested lists, and direction-dependent folds.

## Constraints (must follow)

Do **not** use:

- `len()`
- list concatenation: `+`, `+=`, `[*a, *b]`
- `list.extend`, `list.insert`, `list.pop`, `list.reverse`, `list.copy`
- `reversed()`, slicing reverse `[::-1]`, `sorted(..., reverse=True)`
- builtins `map`, `filter`, `sum`, `reduce` / `functools.reduce`
- `copy.copy` / `copy.deepcopy` / `list(...)` as a whole-list clone

Allowed:

- `for` loops and `range` over an index you already counted
- indexing / iteration (`for item in xs`)
- `list.append` **only** to grow a **new** result list you allocated
- calling the other functions in this module (composition is encouraged)

Do **not** mutate `list1`, `list2`, `lists`, or `list`. Always allocate a fresh result (except folds, which return the accumulator).

Keep the stub’s parameter names, including `list` (it shadows the builtin — do not call `list()`).

No type annotations required; match the stub.

---

## Signatures

```python
def append(list1, list2): ...
def concat(lists): ...
def filter(function, list): ...
def length(list): ...
def map(function, list): ...
def foldl(function, list, initial): ...
def foldr(function, list, initial): ...
def reverse(list): ...
```

Elements are untyped: ints, nested lists, mixed values. Nested structure is **not** flattened except by `concat`, and `concat` flattens **exactly one** level.

---

## Algorithms

Implement `foldl` first; several other ops are one-liners on top of it. `foldr` needs right-to-left traversal — implement it independently (do not create a reverse↔foldr cycle).

### 1. `foldl(function, list, initial)`

Left fold: `function(acc, el)` for each element, left to right.

```
acc ← initial
for el in list:
    acc ← function(acc, el)
return acc
```

Empty list → `initial` unchanged.

Direction-dependent example (held-out):

- `foldl(lambda acc, el: el / acc, [1, 2, 3, 4], 24)`
- steps: `1/24` → `2/(1/24)=48` → `3/48` → `4/(3/48)=64`

Do **not** assume `acc` and `el` share a type (accumulator may be `int` while elements are something else, or vice versa).

### 2. `foldr(function, list, initial)`

Right fold, **same call convention** as foldl: `function(acc, el)`.

Process elements from the last index toward the first. Do not use `reversed()` / `[::-1]`.

```
acc ← initial
i ← length(list) - 1          # use our length(), not len()
while i >= 0:
    acc ← function(acc, list[i])
    i ← i - 1
return acc
```

Alternative without `length`: walk once into a new list via `append` on a fresh list, then index that — still no builtin reverse. Simplest: index the original list with a countdown.

Empty list → `initial`.

Direction-dependent example:

- `foldr(lambda acc, el: el / acc, [1, 2, 3, 4], 24)`
- from the right: `4/24` → `3/(4/24)=18` → `2/18` → `1/(2/18)=9`

`foldr` is **not** `foldl` on a reversed list unless the function is associative; with `el / acc` they differ (`64` vs `9`). Implement real right-to-left application.

### 3. `length(list)`

Count by iteration. Nested lists count as **one** item each (do not recurse).

```
n ← 0
for _ in list:
    n ← n + 1
return n
```

`[]` → `0`. `[[1, 2], [3], [[4]]]` → `3`.

Do not use `len()`.

### 4. `append(list1, list2)`

New list: every item of `list1`, then every item of `list2`. One-level; nested items stay nested.

```
result ← []
for x in list1:
    result.append(x)
for x in list2:
    result.append(x)
return result
```

Cases:

- `append([], [])` → `[]`
- `append([], [1, 2, 3, 4])` → `[1, 2, 3, 4]`
- `append([1, 2, 3, 4], [])` → `[1, 2, 3, 4]`
- `append([1, 2], [2, 3, 4, 5])` → `[1, 2, 2, 3, 4, 5]` (duplicates kept)

Do not mutate `list1`. Do not use `+` / `extend`.

### 5. `concat(lists)`

`lists` is a list of lists. Flatten **one** level into a single list.

```
result ← []
for inner in lists:
    result ← append(result, inner)    # or inline the same two-loop copy
return result
```

Cases:

- `concat([])` → `[]`
- `concat([[1, 2], [3], [], [4, 5, 6]])` → `[1, 2, 3, 4, 5, 6]`
- `concat([[[1], [2]], [[3]], [[]], [[4, 5, 6]]])` → `[[1], [2], [3], [], [4, 5, 6]]`
  — inner lists are appended as sequences of items, so a nested list value is preserved as an element

Empty inner lists contribute nothing. Do not recurse into nested structure.

### 6. `filter(function, list)`

Keep items for which `function(item)` is truthy. Preserve order.

```
result ← []
for item in list:
    if function(item):
        result.append(item)
return result
```

- `filter(pred, [])` → `[]`
- `filter(lambda x: x % 2 == 1, [1, 2, 3, 4, 5])` → `[1, 3, 5]`

Predicate result is what matters, not the item’s own truthiness (`0` / `None` / `[]` stay if the predicate says so).

Do not use builtin `filter`.

### 7. `map(function, list)`

Apply `function` to every item; preserve order and length.

```
result ← []
for item in list:
    result.append(function(item))
return result
```

- `map(f, [])` → `[]`
- `map(lambda x: x + 1, [1, 3, 5, 7])` → `[2, 4, 6, 8]`

Do not flatten; if an item is a list, `function` receives that list as one value.

Do not use builtin `map`.

### 8. `reverse(list)`

New list, original items in reverse order. Do **not** reverse or flatten nested lists.

```
result ← []
i ← length(list) - 1
while i >= 0:
    result.append(list[i])
    i ← i - 1
return result
```

Or: `foldl(lambda acc, el: append([el], acc), list, [])` — that prepends via our `append`, no builtin reverse.

Cases:

- `reverse([])` → `[]`
- `reverse([1, 3, 5, 7])` → `[7, 5, 3, 1]`
- `reverse([[1, 2], [3], [], [4, 5, 6]])` → `[[4, 5, 6], [], [3], [1, 2]]`

---

## Optional composition (all valid)

If you prefer a single primitive loop in `foldl` / `foldr`:

| op | via |
|---|---|
| `length` | `foldl(lambda acc, _: acc + 1, list, 0)` |
| `map` | `foldl(lambda acc, el: append(acc, [function(el)]), list, [])` |
| `filter` | `foldl(lambda acc, el: append(acc, [el]) if function(el) else acc, list, [])` |
| `reverse` | `foldl(lambda acc, el: append([el], acc), list, [])` |
| `concat` | `foldl(append, lists, [])` |
| `append` | still a loop, or `concat([list1, list2])` — then `concat` must not call `append` (avoid a cycle) |

Pick **one** direction of dependency. Recommended (no cycles, simple):

1. `foldl` — primitive left loop
2. `length` — count loop (or foldl)
3. `foldr` — countdown index using `length`
4. `append` — two copy loops
5. `concat` — fold/loop of `append`
6. `filter`, `map`, `reverse` — loops or foldl + `append`

---

## Edge cases (held-out tests will hit these)

| Area | Behavior |
|---|---|
| Empty inputs | Every op on `[]` is identity-like: `append`/`concat`/`filter`/`map`/`reverse` → `[]`; `length` → `0`; folds → `initial` |
| Do not mutate | After `append(a, b)`, `a` and `b` unchanged |
| Nested structure | `length` / `reverse` / `map` / `filter` treat a nested list as one element |
| `concat` depth | Exactly one flatten; list-of-list-of-lists stays list-of-lists |
| Fold argument order | Always `function(accumulator, element)`, both folds |
| Fold direction | Non-associative ops (`/`) must yield foldl=64 and foldr=9 on `[1,2,3,4]` with init `24` and `lambda acc, el: el / acc` |
| Mixed types | Acc type may differ from element type; just call `function` |
| Duplicates | `append` / `concat` keep every occurrence |
| Filter predicate | Use truthiness of `function(item)`, not `item` |

---

## Verification (implementer)

```text
python -m unittest public_test.py
```

That file only asserts `append([], []) == []`. After implementing all eight, the same command must still pass. Do not add tests in this repo; do not touch `list_ops.py` in the planning phase.

---

## Out of scope

- Type hints, docstrings, extra helpers beyond the eight functions
- In-place variants
- Deep flatten, `reduce` with no initial value
- Editing `public_test.py` or any file other than `list_ops.py` at implementation time
