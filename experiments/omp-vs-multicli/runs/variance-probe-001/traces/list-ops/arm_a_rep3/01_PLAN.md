# list_ops.py — Implementation Guide

Exercism-style **list operations** in Python. Implement the eight functions in the stub. Do **not** use the builtin equivalents (`len`, `map`, `filter`, `reversed`, `reversed()`, `reduce`, `sum`, `list.copy`, slicing reverse `[::-1]`, or list methods `append` / `extend` / `insert` / `pop` / `reverse`). Build results with `for` iteration and the `+` operator (or by calling our own `append`). Do **not** mutate caller-owned inputs.

Public tests only cover `append([], [])`. Hidden tests follow the 2023-07-19 Exercism `list-ops` canonical data (same generator as `public_test.py`). Plan for the full suite below.

---

## 1. Signatures (keep the stub exactly)

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

- Parameter name `list` shadows the builtin; that is intentional. Do not rename.
- Module-level `filter` / `map` also shadow builtins; tests import them as `list_ops_filter` / `list_ops_map`.
- No type hints required. No extra helpers need to be public.

---

## 2. Architecture

Two layers.

**Layer A — primitives** (only `for` + list `+`):

| Function | Role |
|---|---|
| `append` | Concatenate two lists into a **new** list |
| `length` | Count elements by walking |
| `foldl`  | Left fold: `function(acc, el)` for each element L→R |

**Layer B — derived** (compose Layer A; no extra iteration if you don't want it):

| Function | Derivation |
|---|---|
| `concat`  | `foldl(append, lists, [])` |
| `reverse` | `foldl(lambda acc, el: append([el], acc), list, [])` |
| `map`     | `foldl(lambda acc, el: append(acc, [function(el)]), list, [])` |
| `filter`  | `foldl` that appends `el` only when `function(el)` is true |
| `foldr`   | `foldl(function, reverse(list), initial)` |

Direct `for`-loop implementations of Layer B are equally valid and often clearer. Either style is fine; do not mix a third convention.

**Invariant:** every function that returns a list returns a **newly allocated** list. Empty input → empty (or `initial` for folds). Nested lists are **not** flattened except by `concat`, which is **one level only**.

---

## 3. Algorithms

### 3.1 `append(list1, list2) -> list`

Spec: all items of `list2` after all items of `list1`. Duplicates preserved. Neither input mutated.

```text
result ← []
for item in list1: result ← result + [item]
for item in list2: result ← result + [item]
return result
```

`return list1 + list2` is also correct (operator, new list, no mutation). Prefer that one-liner if the rest of the file still avoids forbidden builtins/methods.

Cases:

- `[], []` → `[]`
- `[], [1,2,3,4]` → `[1,2,3,4]`
- `[1,2,3,4], []` → `[1,2,3,4]`
- `[1,2], [2,3,4,5]` → `[1,2,2,3,4,5]`  (the shared `2` is kept twice)

### 3.2 `concat(lists) -> list`

Spec: `lists` is a list of lists. Flatten **exactly one** level.

```text
result ← []
for inner in lists:
    result ← append(result, inner)
return result
```

Cases:

- `[]` → `[]`
- `[[1,2],[3],[],[4,5,6]]` → `[1,2,3,4,5,6]`
- `[[[1],[2]],[[3]],[[]],[[4,5,6]]]` → `[[1],[2],[3],[],[4,5,6]]`  
  (inner lists stay lists; `[[]]` contributes one empty list, not nothing)

Empty inner lists contribute nothing: `[[], [1], []]` → `[1]`.

### 3.3 `filter(function, list) -> list`

Spec: keep items for which `function(item)` is true, **original order**.

```text
result ← []
for item in list:
    if function(item):
        result ← append(result, [item])
return result
```

Use the actual truth value of `function(item)` (`if function(item):`), not a comparison to `True`. Canonical predicate is `lambda x: x % 2 == 1`.

Cases:

- `pred, []` → `[]`
- odds of `[1,2,3,5]` → `[1,3,5]`
- predicate never true → `[]`
- predicate always true → shallow copy of input (new list)

### 3.4 `length(list) -> int`

```text
n ← 0
for _ in list:
    n ← n + 1
return n
```

**Forbidden:** `len(list)`.

Cases: `[]` → `0`; `[1,2,3,4]` → `4`. Nested structure does not matter; count top-level items only (`[[1,2], [3]]` would be `2` if it appeared).

### 3.5 `map(function, list) -> list`

Spec: one output per input, same order, `function(item)` per element.

```text
result ← []
for item in list:
    result ← append(result, [function(item)])
return result
```

Cases:

- `f, []` → `[]`
- `lambda x: x + 1` on `[1,3,5,7]` → `[2,4,6,8]`

### 3.6 `foldl(function, list, initial)`

Left fold. **Call `function(accumulator, element)`** — accumulator is the **first** argument.

```text
acc ← initial
for item in list:
    acc ← function(acc, item)
return acc
```

Empty list → `initial` (function never called).

Canonical checks (Python 3 true division):

| function | list | initial | result | reduction |
|---|---|---|---|---|
| `lambda acc, el: el * acc` | `[]` | `2` | `2` | identity |
| `lambda acc, el: el + acc` | `[1,2,3,4]` | `5` | `15` | commutative |
| `lambda acc, el: el / acc` | `[1,2,3,4]` | `24` | `64` | `1/24` → `2/(1/24)=48` → `3/48` → `4/(3/48)=64` |

`assertEqual(64, 64.0)` is true; returning a float from `/` is fine.

### 3.7 `foldr(function, list, initial)`

Right fold. **Same calling convention as foldl: `function(accumulator, element)`.** Difference is only traversal direction (R→L).

```text
return foldl(function, reverse(list), initial)
```

Equivalent loop:

```text
acc ← initial
for item in reverse(list):
    acc ← function(acc, item)
return acc
```

Do **not** call `function(element, accumulator)`. Hidden tests pass `lambda acc, el: ...`.

Canonical checks:

| function | list | initial | result | reduction |
|---|---|---|---|---|
| `lambda acc, el: el * acc` | `[]` | `2` | `2` | identity |
| `lambda acc, el: el + acc` | `[1,2,3,4]` | `5` | `15` | commutative (same as foldl) |
| `lambda acc, el: el / acc` | `[1,2,3,4]` | `24` | `9` | `4/24` → `3/(4/24)=18` → `2/18` → `1/(2/18)=9` |

If foldl and foldr were swapped, the direction-dependent `/` tests fail (`64` vs `9`).

Recursive formulation (if not using `reverse`): foldr on `[x0, x1, …, xn]` is  
`f(f(…f(f(initial, xn), xn-1)…, x1), x0)` with `f = function`. Recursion plus `list[1:]` is worse (slicing + depth); prefer reverse-then-foldl.

### 3.8 `reverse(list) -> list`

Top-level reverse only. Nested lists are **not** flattened or recursively reversed.

```text
result ← []
for item in list:
    result ← append([item], result)   # prepend
return result
```

Cases:

- `[]` → `[]`
- `[1,3,5,7]` → `[7,5,3,1]`
- `[[1,2],[3],[],[4,5,6]]` → `[[4,5,6],[],[3],[1,2]]`  
  inner lists identical objects-by-value, not reversed internally

---

## 4. Data structures

- Inputs and outputs are Python `list` objects. No custom nodes, no `collections`, no iterators as return values.
- Accumulators in folds are whatever `initial` / `function` produce (`int` or `float` in tests).
- Elements may be ints or lists (nested). Treat elements as opaque: never iterate an element unless the function is `concat` and the element **is** one of the inner lists being concatenated.
- Use a fresh `[]` per call. Never alias an input list as the return value (`return list1` is wrong even when `list2` is empty, if mutation of the returned list should not affect the caller — returning `list1 + list2` is safe because `+` copies).

---

## 5. Edge-case and constraint checklist

1. **Empty everywhere** — first element of every function's tests.
2. **One-sided empty `append`** — both `append([], xs)` and `append(xs, [])`.
3. **`concat` is shallow** — list-of-list-of-lists stays one level of nesting.
4. **`reverse` is shallow** — same.
5. **Stability / duplicates** — `append` and `concat` keep repeated values and order.
6. **No input mutation** — if tests keep a reference to the original, it must be unchanged. Never `list1 += list2`, never `.append` on an argument.
7. **No builtin list ops** — especially `len()`, `map()`, `filter()`, `reversed()`, `.reverse()`, `[::-1]`, `functools.reduce`. A source-level scan in hidden tests is possible.
8. **Fold argument order** — always `function(acc, el)`, both folds.
9. **Fold direction** — foldl walks the original list; foldr walks the reversed list.
10. **`/` in Python 3** — results may be `float`; do not int-cast.
11. **Filter truthiness** — `if function(item):` (canonical preds return real `bool`).
12. **Single-element lists** — folds call `function` once; reverse/map/filter are identity-shaped.
13. **`concat([])` vs `concat([[]])`** — `[]` vs `[]` (empty inner list adds no items). `concat([[[]]])` → `[[]]`.
14. **Do not deep-copy** — mapped/filtered/reversed inner list values can be the same objects; only the outer spine is new.
15. **Shadowing** — inside `filter`/`map`/`length`/`reverse`/`foldl`/`foldr`, do not call builtin `list()`, `map()`, `filter()`, or `len()`; you don't need them.

---

## 6. Suggested file body (reference — implementer writes `list_ops.py`)

Straight-loop form (clear, no helpers). Derived form (section 2) is equally acceptable.

```python
def append(list1, list2):
    result = []
    for item in list1:
        result = result + [item]
    for item in list2:
        result = result + [item]
    return result


def concat(lists):
    result = []
    for inner in lists:
        result = append(result, inner)
    return result


def filter(function, list):
    result = []
    for item in list:
        if function(item):
            result = append(result, [item])
    return result


def length(list):
    n = 0
    for _ in list:
        n = n + 1
    return n


def map(function, list):
    result = []
    for item in list:
        result = append(result, [function(item)])
    return result


def foldl(function, list, initial):
    acc = initial
    for item in list:
        acc = function(acc, item)
    return acc


def foldr(function, list, initial):
    return foldl(function, reverse(list), initial)


def reverse(list):
    result = []
    for item in list:
        result = append([item], result)
    return result
```

`foldr` depends on `reverse`; define `reverse` anywhere in the module (all defs are at import time). Do not introduce a cycle (`reverse` must not call `foldr`).

---

## 7. Verification (for the implementer, not this planning step)

- `python -m unittest public_test` → `test_append_empty_lists` passes.
- Mentally replay the canonical rows in §3, especially foldl `64` vs foldr `9` and the two shallow nested-list cases.
- Grep own source for `len(`, `.append(`, `.extend(`, `reversed(`, `[::-1]`, builtin `map(` / `filter(` — should be clean (our own `def map` / `def filter` are the definitions, not calls).

No tests or `list_ops.py` are modified by this plan.
