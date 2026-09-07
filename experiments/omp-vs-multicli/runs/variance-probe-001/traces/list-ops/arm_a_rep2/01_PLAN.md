# list_ops.py — Implementation Guide

## Goal

Implement the eight list operations declared in `list_ops.py` using explicit iteration only. Do not call Python’s list algorithms (`len`, `sum`, `map`, `filter`, `reversed`, `sorted`, `functools.reduce`, `itertools`, list concatenation via `+`/`+=` of whole lists, `list.extend`, slicing reverse `[::-1]`, unpacking `[*a, *b]`). Building a *new* result list with the primitive `list.append` (one element at a time) is allowed. Never mutate caller-owned lists.

Public tests only assert `append([], []) == []`. Held-out tests will cover the rest of the README operations. Names and signatures must match the stub and `public_test.py` imports exactly (`concat`, not `concatenate`; `filter`/`map` keep those names).

## API (freeze; do not rename or reorder)

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

Parameter name `list` shadows the builtin; keep it to match the stub. Values are homogeneous or mixed Python objects (ints, strings, nested lists). Callables are ordinary 1- or 2-arg functions.

## Constraints

- **No existing list algorithms.** Count by walking; fold by walking; reverse by walking. `list.append` on a freshly allocated result is the only permitted list mutator.
- **Non-destructive.** Every function returns a new list (or a scalar for `length` / folds). Inputs are read-only.
- **One-level only.** `concat` flattens exactly one level. `reverse` / `map` / `filter` / `length` do not recurse into nested lists.
- **Empty lists are first-class.** Empty input never special-cases into a different type; empty → empty list or the fold `initial`.
- **Reuse internally.** Implement `concat` via `append`, and `filter`/`map`/`reverse` via a single “push onto new list” loop. `foldr` may walk a reversed copy or index from the end; both are valid if they match the fold contract below.

## Data structures

- **Inputs / outputs:** Python `list`. No custom nodes.
- **Accumulators:**
  - Result lists: `out = []` then `out.append(item)`.
  - `length`: integer counter starting at `0`.
  - `foldl` / `foldr`: accumulator starts as `initial` (any type: int, float, str, list, …) and is replaced each step by `function(acc, item)`.
- **No extra buffers** except where `foldr` needs right-to-left order (a reversed snapshot, or an index `i` from `length(list)-1` down to `0`). Prefer indexing from the end if `length` is already available, to avoid an extra allocation; a `reverse` then left-fold is also correct.

## Algorithms

### `append(list1, list2)`

Walk `list1` then `list2`, pushing each element onto a new list.

```
out ← []
for x in list1: out.append(x)
for x in list2: out.append(x)
return out
```

- `append([], [])` → `[]`
- `append([], xs)` → shallow copy of `xs`
- `append(xs, [])` → shallow copy of `xs`
- `append([1, 2], [2, 3, 4, 5])` → `[1, 2, 2, 3, 4, 5]` (order preserved; duplicates kept)
- Nested elements are copied by reference, not cloned: `append([[1]], [[2]])` → `[[1], [2]]`

### `concat(lists)`

`lists` is a list of lists. Fold `append` across them, starting from `[]`.

```
out ← []
for inner in lists:
    out ← append(out, inner)
return out
```

- `concat([])` → `[]`
- `concat([[], [], []])` → `[]`
- `concat([[1, 2], [3], [], [4, 5, 6]])` → `[1, 2, 3, 4, 5, 6]`
- **Not deep flatten:** `concat([[[1], [2]], [[3]]])` → `[[1], [2], [3]]`
- Each `inner` may be empty; skip is automatic because `append(out, [])` is a no-op copy of `out`.

### `filter(function, list)`

Keep items for which `function(item)` is truthy. Preserve order. Do not use builtin `filter`.

```
out ← []
for x in list:
    if function(x):
        out.append(x)
return out
```

- `filter(pred, [])` → `[]`
- `filter(lambda x: x % 2 == 1, [1, 2, 3, 5])` → `[1, 3, 5]`
- Predicate false for every item → `[]`
- Do not coerce the predicate result beyond Python truthiness (`if function(x)`).

### `length(list)`

```
n ← 0
for _ in list:
    n ← n + 1
return n
```

- `length([])` → `0`
- Nested list counts as **one** item: `length([[1, 2], [3]])` → `2`
- Do not use `len()`.

### `map(function, list)`

```
out ← []
for x in list:
    out.append(function(x))
return out
```

- `map(f, [])` → `[]`
- `map(lambda x: x + 1, [1, 3, 5, 7])` → `[2, 4, 6, 8]`
- Length of output equals length of input. Do not use builtin `map`.

### `foldl(function, list, initial)` — left fold

Argument order of `function` is **`(accumulator, element)`**, not Haskell’s `(element, accumulator)` for `foldr`. Apply left-to-right:

```
acc ← initial
for x in list:
    acc ← function(acc, x)
return acc
```

Identities and cases:

- Empty list: return `initial` unchanged (`foldl(f, [], init) is init`).
- Sum: `foldl(lambda acc, el: acc + el, [1, 2, 3, 4], 5)` → `15`
- Direction-dependent (must not be implemented as a right fold):

  `function(acc, el) = el / acc`, list `[1, 2, 3, 4]`, initial `24`:

  ```
  1/24 → 2/(1/24)=48 → 3/48=1/16 → 4/(1/16)=64
  ```

  Expected: `64`.
- Accumulator type follows `initial` and `function` (e.g. start `""` and add chars; start `[]` and append).

### `foldr(function, list, initial)` — right fold

Same `function(acc, el)` convention as `foldl`, but reduce **from the right**.

```
acc ← initial
for x in reverse(list):          # or index from end
    acc ← function(acc, x)
return acc
```

Equivalent recurrence: `foldr(f, [x, *xs], init) = f(foldr(f, xs, init), x)`.

- Empty list: return `initial`.
- Sum (associative): same numeric result as `foldl` for `+`.
- Direction-dependent:

  `function(acc, el) = el / acc`, list `[1, 2, 3, 4]`, initial `24`:

  ```
  4/24=1/6 → 3/(1/6)=18 → 2/18=1/9 → 1/(1/9)=9
  ```

  Expected: `9`.
- **Do not** swap arguments to mimic Haskell `foldr` (`f(el, acc)`). Tests pass `(acc, el)`.

If implementing via reverse: `foldr(f, xs, init) == foldl(f, reverse(xs), init)` under this argument convention.

### `reverse(list)`

```
out ← []
for x in list:
    # prepend without slice tricks: build by walking and inserting at 0,
    # or walk with an index from the end.
```

Preferred (O(n), no `insert(0)` quadratic):

```
n ← length(list)
out ← []
i ← n - 1
while i >= 0:
    out.append(list[i])
    i ← i - 1
return out
```

Alternative: push onto `out` in forward order then… no, that would need a second reverse. Forward walk with `insert(0)` is correct but O(n²); avoid.

- `reverse([])` → `[]`
- `reverse([1, 3, 5, 7])` → `[7, 5, 3, 1]`
- **Top-level only:** `reverse([[1, 2], [3, 4]])` → `[[3, 4], [1, 2]]`, not `[[4, 3], [2, 1]]`

## Edge-case matrix

| Case | Expected |
|---|---|
| Both args empty (`append`) | `[]` |
| Left empty / right empty (`append`) | Shallow copy of the non-empty side |
| `concat` of no lists | `[]` |
| `concat` of empty inners mixed with non-empty | Empty inners contribute nothing |
| Nested lists in `concat` | One-level flatten only |
| Empty `filter` / `map` / `reverse` | `[]` |
| `filter` keeps none / keeps all | `[]` / shallow copy in original order |
| Empty `length` | `0` |
| `length` of nested | Outer count only |
| Empty folds | `initial` (any type), function never called |
| `foldl` vs `foldr` on non-associative `/` | `64` vs `9` with the numbers above |
| Reverse nested | Reverse outer order only |
| Shared nested objects | Identity of inner objects preserved (shallow) |
| Do not mutate inputs | After any call, original lists compare equal to pre-call copies |

## Implementation notes

1. **Order of implementation (dependencies):** `append` → `length` → `concat` / `filter` / `map` → `reverse` → `foldl` → `foldr`. `foldr` can call `reverse`; `concat` can call `append`.
2. **Shallow copies:** `append([], xs)` and `filter`/`map`/`reverse` on non-empty inputs must not return the *same object* as an input (`is` identity). Always allocate `out = []`.
3. **No `list += other_list`.** That is `extend`. Push elements one at a time.
4. **Division tests** may yield `float`. Do not `int()`-cast fold results.
5. **Do not import** `functools`, `itertools`, or anything else. File stays function definitions only.
6. **Stubs:** replace every `pass` with a real body. No `NotImplementedError`, no extra public helpers required. A private `_copy` is optional; prefer using `append([], xs)` if a copy is needed.

## Verification (for the implementer; planner does not run tests)

- `python -m unittest public_test.py` — `test_append_empty_lists`.
- Mentally / locally check the edge-case matrix, especially fold direction and one-level `concat`/`reverse`.
- Confirm no use of forbidden builtins (`len`, `map`, `filter`, `reversed`, `sum`, `extend`, `+` of lists, `[::-1]`).

## Out of scope

- Type hints, classes, iterators-as-inputs, deep copy, concurrency, error raising on non-list inputs (tests pass lists and callables).
- Editing `list_ops.py` or any test file in the planning step.
