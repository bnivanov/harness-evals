# Implementation Guide: `list_ops.py`

## 1. Goal

Implement eight basic list operations in `list_ops.py` in the functional-programming style described by `README.md`:

| README name | Python function | Meaning |
|---|---|---|
| append | `append` | Concatenate two lists (second after first) |
| concatenate | `concat` | Flatten a list of lists by one level |
| filter | `filter` | Keep items for which a predicate is true |
| length | `length` | Count items |
| map | `map` | Transform each item with a function |
| foldl | `foldl` | Left fold / reduce |
| foldr | `foldr` | Right fold / reduce |
| reverse | `reverse` | Reverse item order (shallow) |

The public test file currently contains only `test_append_empty_lists`. That is a smoke test, not the full contract. Hidden tests are expected to cover every operation, empty and non-empty inputs, nested lists, and direction-sensitive folds. Implement **all eight functions** completely.

Keep the function names and positional parameters exactly as in the stub. Do not add extra required arguments. Do not rename parameters (the stub uses `list` as a parameter name; that is intentional).

---

## 2. Constraints (from README and the stub)

1. **Do not use Python’s existing list-processing functions** to implement these operations. Forbidden as the implementation of the corresponding operation (and as helpers for them):
   - `len()`
   - builtin `map()` / `filter()`
   - `functools.reduce` / `itertools` helpers
   - `reversed()`, `list.reverse()`, slicing `[::-1]`
   - `list.extend()`, `list.insert()` as a substitute for `append`/`concat`
   - `sum()` as a substitute for `length` or folds
   - unpacking tricks such as `[*a, *b]` as the sole body of `append`/`concat`
2. **Do not mutate caller-owned lists.** Every operation that returns a list must return a **new** list. The inputs must be bit-for-bit unchanged after the call (identity of nested objects may be shared; do not copy nested lists unless an operation’s spec requires it).
3. **Shallow operations.** Nested lists are ordinary elements. `length`, `reverse`, `map`, `filter`, and `append` do **not** recurse into nested lists. `concat` flattens **exactly one** level.
4. **Fold argument order is significant.** Both `foldl` and `foldr` call `function(accumulator, element)` — accumulator first, current element second. They differ only in traversal direction.
5. Match the stub style: no need for type hints, classes, or extra modules. A single module of eight functions is the whole design.

Allowed, and recommended:

- `for item in sequence:` iteration
- Indexing (`seq[i]`) if you compute indices yourself
- Building a fresh result list and using **that result’s** `.append(...)` method (this is constructing output, not using a forbidden list-op)
- Calling the **other functions in this module** (e.g. `concat` may call `append`; `foldr` may call `reverse`)
- Boolean tests on the predicate result (`if function(item):`)
- Recursion is allowed but not required; hidden tests use small lists, but iteration is simpler and avoids stack limits

---

## 3. Public API (exact signatures)

```python
def append(list1, list2):
    ...

def concat(lists):
    ...

def filter(function, list):
    ...

def length(list):
    ...

def map(function, list):
    ...

def foldl(function, list, initial):
    ...

def foldr(function, list, initial):
    ...

def reverse(list):
    ...
```

`filter` and `map` shadow Python builtins inside this module. That is required: tests import them as `filter as list_ops_filter` and `map as list_ops_map`. Do not rename them.

Return types:

- `append`, `concat`, `filter`, `map`, `reverse` → a new `list`
- `length` → `int` (`0` for empty)
- `foldl`, `foldr` → the same type as the fold’s accumulator (number, list, string, etc.)

---

## 4. Data structures

No custom types. Use Python lists as the sequence representation.

| Structure | Role |
|---|---|
| Input `list` / `list1` / `list2` / `lists` | Read-only. Never call mutating methods on these. |
| Fresh `result = []` | Output builder for list-returning operations. |
| Scalar `count` (`int`) | Running length. |
| Scalar `acc` (any) | Fold accumulator; starts as `initial`. |

Elements are opaque. They may be ints, strings, booleans, `None`, or nested lists. Never assume a homogeneous element type except where a given call’s `function` imposes one.

Identity vs copy:

- When placing an element into a result, store the **same object reference** (no deep copy).
- Example: `reverse([[1, 2], [3]])` must yield `[[3], [1, 2]]` — the inner lists are the original inner lists, in reversed outer order, not flattened and not cloned.

---

## 5. Algorithms

Implement in this order so later functions can reuse earlier ones if you choose.

### 5.1 `length(list)` — O(n) time, O(1) extra space

Count by iteration. Do not call `len()`.

```
count ← 0
for each item in list:
    count ← count + 1
return count
```

Empty list → `0`. Nested lists count as **one** element each: `length([[1, 2], [3]]) == 2`.

### 5.2 `append(list1, list2)` — O(|list1| + |list2|) time and space

Build a new list containing every element of `list1` in order, then every element of `list2` in order.

```
result ← []
for each item in list1:
    result.append(item)
for each item in list2:
    result.append(item)
return result
```

Do **not** write `list1.extend(list2)` or `list1 += list2` (mutates `list1`). Do not write `return list1 + list2` as the implementation — that uses the builtin list concatenate the exercise asks you to reimplement (it also happens to be non-mutating, but it violates the “no existing functions” rule).

Duplicates are kept: `append([1, 2], [2, 3, 4, 5])` → `[1, 2, 2, 3, 4, 5]`.

### 5.3 `concat(lists)` — O(total number of elements) time

`lists` is a list of lists. Flatten **one** level: concatenate the inner lists from left to right.

```
result ← []
for each inner in lists:
    result ← append(result, inner)
return result
```

Equivalently, nested loops: for each inner list, for each item, `result.append(item)`.

**Not a deep flatten.** Inner elements that happen to be lists stay lists:

```
concat([[[1], [2]], [[3]], [[]], [[4, 5, 6]]])
    == [[1], [2], [3], [], [4, 5, 6]]
```

`concat([])` → `[]`. `concat([[], [], []])` → `[]`. `concat([[1, 2], [3], [], [4, 5, 6]])` → `[1, 2, 3, 4, 5, 6]`.

### 5.4 `reverse(list)` — O(n) time, O(n) space

New list, original items, reversed order. Shallow: do not reverse or flatten nested lists.

Iterative options (pick one):

**A. Walk from the end using `length` (O(n), no builtin `reversed`):**

```
n ← length(list)
result ← []
i ← n - 1
while i >= 0:
    result.append(list[i])
    i ← i - 1
return result
```

**B. Head-prepend via `append` (clear, O(n²) because each prepend copies; fine for this exercise’s sizes):**

```
result ← []
for each item in list:
    result ← append([item], result)
return result
```

**C. Fold (see §6) after `foldl` exists.**

Do not use `list.reverse()`, `reversed(list)`, or `list[::-1]`.

`reverse([])` → `[]`.  
`reverse([1, 3, 5, 7])` → `[7, 5, 3, 1]`.  
`reverse([[1, 2], [3], [], [4, 5, 6]])` → `[[4, 5, 6], [], [3], [1, 2]]`.

### 5.5 `filter(function, list)` — O(n) time

Predicate `function` is a callable of one argument. Keep items for which the predicate is true, in original order.

```
result ← []
for each item in list:
    if function(item):
        result.append(item)
return result
```

Use ordinary boolean context (`if function(item):`). Tests pass predicates that return real booleans (e.g. `lambda x: x % 2 == 1`). Do not wrap the predicate in builtin `filter()`.

`filter(pred, [])` → `[]`.  
If nothing matches, return `[]` (not `None`).  
If everything matches, return a **new** list with the same items in the same order.

### 5.6 `map(function, list)` — O(n) time

Apply `function` to every item; collect results in order. Output length always equals input length.

```
result ← []
for each item in list:
    result.append(function(item))
return result
```

`map(f, [])` → `[]`.  
`map(lambda x: x + 1, [1, 3, 5, 7])` → `[2, 4, 6, 8]`.  
Do not use builtin `map()`.

### 5.7 `foldl(function, list, initial)` — O(n) time

Left fold. Callable signature: `function(accumulator, element) -> new_accumulator`.

```
foldl(f, [x1, x2, x3], init)  ==  f(f(f(init, x1), x2), x3)
```

Algorithm:

```
acc ← initial
for each item in list:
    acc ← function(acc, item)
return acc
```

Empty list: return `initial` unchanged (even if `initial` is `[]` or another container). Do not wrap it, do not copy it unless `function` does.

Worked numeric example (direction-dependent):

```
function = (acc, el) -> el / acc     # Python: lambda acc, el: el / acc
list     = [1, 2, 3, 4]
initial  = 24

acc = 24
acc = 1 / 24          # 0.04166...
acc = 2 / (1/24)      # 48
acc = 3 / 48          # 0.0625
acc = 4 / 0.0625      # 64
→ 64   (Python 3 `/` yields float 64.0; 64.0 == 64, so either is fine)
```

Direction-independent example: `foldl(lambda acc, el: el + acc, [1, 2, 3, 4], 5)` → `15`.

Empty-list example: `foldl(lambda acc, el: el * acc, [], 2)` → `2`.

### 5.8 `foldr(function, list, initial)` — O(n) time

Right fold. **Same callable signature as foldl:** `function(accumulator, element)`. The only difference is that elements are consumed from right to left:

```
foldr(f, [x1, x2, x3], init)  ==  f(f(f(init, x3), x2), x1)
```

This is **not** the Haskell/ML convention `f(element, accumulator)`. If you call `function(item, acc)` you will fail the direction-dependent tests.

Equivalent formulations (all correct):

**A. Reverse then left-fold (recommended):**

```
return foldl(function, reverse(list), initial)
```

This is valid because both folds share `function(acc, el)`. Using `reverse` here is implementing `foldr` in terms of **this module’s** `reverse` + `foldl`, not in terms of Python’s `reversed`.

**B. Index walk from the end:**

```
acc ← initial
i ← length(list) - 1
while i >= 0:
    acc ← function(acc, list[i])
    i ← i - 1
return acc
```

**C. Recursion (correct, but unnecessary):**

```
if list is empty: return initial
return function(foldr(function, list[1:], initial), list[0])
```

(`list[1:]` copies the tail; fine for small n.)

Worked numeric example with the **same** function as foldl:

```
function = (acc, el) -> el / acc
list     = [1, 2, 3, 4]
initial  = 24

acc = 24
acc = 4 / 24          # 1/6
acc = 3 / (1/6)       # 18
acc = 2 / 18          # 1/9
acc = 1 / (1/9)       # 9
→ 9
```

`foldl` on that input is `64`; `foldr` is `9`. A single shared loop that always walks left-to-right will fail one of these tests.

Empty list: `foldr` also returns `initial` unchanged.

String/list-building intuition (if hidden tests use a non-commutative operator):

```
foldl(lambda acc, el: acc + el, ["a", "b", "c"], "")  →  "abc"
foldr(lambda acc, el: acc + el, ["a", "b", "c"], "")  →  "cba"

foldl(lambda acc, el: acc + [el], [1, 2, 3], [])      →  [1, 2, 3]
foldr(lambda acc, el: acc + [el], [1, 2, 3], [])      →  [3, 2, 1]
```

---

## 6. Optional: implement several operations via folds

Not required. If you prefer a single primitive:

| Operation | Definition in terms of `foldl` |
|---|---|
| `length(xs)` | `foldl(lambda acc, _: acc + 1, xs, 0)` |
| `map(f, xs)` | `foldl(lambda acc, el: append(acc, [f(el)]), xs, [])` |
| `filter(p, xs)` | `foldl(lambda acc, el: append(acc, [el]) if p(el) else acc, xs, [])` |
| `reverse(xs)` | `foldl(lambda acc, el: append([el], acc), xs, [])` |
| `append(a, b)` | `foldl(lambda acc, el: acc + [el]  /* via result.append */, b, copy_of_a)` — still copy `a` first without mutation |
| `concat(xss)` | `foldl(append, xss, [])` |

`foldr` should still be a distinct right-to-left traversal as in §5.8.

Loop-based implementations (§5) are easier to get right and are the recommended default.

---

## 7. Dependency graph (if reusing module functions)

```
length  (no deps)
append  (no deps)
concat  → append
reverse → length  (if indexing from the end)
        → append  (if prepending)
filter  (no deps, or → append)
map     (no deps, or → append)
foldl   (no deps)
foldr   → reverse + foldl
        or → length
```

Avoid cycles: if `reverse` is defined via `foldl`, then `foldr` may still use that `reverse`. Do not define `foldl` via `foldr` and `foldr` via `foldl`.

---

## 8. Edge-case catalog

Handle every row. Hidden tests are expected to include these.

### Empty inputs

| Call | Result |
|---|---|
| `append([], [])` | `[]` |
| `append([], [1, 2, 3, 4])` | `[1, 2, 3, 4]` |
| `append([1, 2, 3, 4], [])` | `[1, 2, 3, 4]` |
| `concat([])` | `[]` |
| `concat([[], []])` | `[]` |
| `filter(p, [])` | `[]` |
| `length([])` | `0` |
| `map(f, [])` | `[]` |
| `foldl(f, [], init)` | `init` (including when `init` is `[]`) |
| `foldr(f, [], init)` | `init` (including when `init` is `[]`) |
| `reverse([])` | `[]` |

The “empty list remains empty even when you add an initial” fold cases exist specifically so that `foldl(f, [], [])` and `foldr(f, [], [])` return `[]`, not `[None]` or `[[]]`. Return the accumulator as-is; do not iterate, do not call `f`.

### Non-empty / mixed

| Call | Result |
|---|---|
| `append([1, 2], [2, 3, 4, 5])` | `[1, 2, 2, 3, 4, 5]` (keep duplicates) |
| `concat([[1, 2], [3], [], [4, 5, 6]])` | `[1, 2, 3, 4, 5, 6]` |
| `filter(lambda x: x % 2 == 1, [1, 2, 3, 4, 5])` | `[1, 3, 5]` |
| `length([1, 2, 3, 4])` | `4` |
| `map(lambda x: x + 1, [1, 3, 5, 7])` | `[2, 4, 6, 8]` |
| `foldl(lambda acc, el: el + acc, [1, 2, 3, 4], 5)` | `15` |
| `foldl(lambda acc, el: el / acc, [1, 2, 3, 4], 24)` | `64` |
| `foldr(lambda acc, el: el + acc, [1, 2, 3, 4], 5)` | `15` |
| `foldr(lambda acc, el: el / acc, [1, 2, 3, 4], 24)` | `9` |
| `reverse([1, 3, 5, 7])` | `[7, 5, 3, 1]` |

### Nested lists (shallow)

| Call | Result |
|---|---|
| `concat([[[1], [2]], [[3]], [[]], [[4, 5, 6]]])` | `[[1], [2], [3], [], [4, 5, 6]]` |
| `length([[1, 2], [3]])` | `2` (not 3) |
| `reverse([[1, 2], [3], [], [4, 5, 6]])` | `[[4, 5, 6], [], [3], [1, 2]]` |

### Mutation / identity

After any call, the original list objects must compare equal to their pre-call values. Build new lists; never `pop`, `clear`, `reverse` in place, `extend`, or assign into input slots.

Sharing inner references is required for nested-list tests: reversing `[[1, 2], [3]]` must not invent new inner lists with different contents.

### Fold callable contract

- Always invoke `function(acc, item)` — two positional arguments, accumulator first.
- Do not call `function` at all when the list is empty.
- `/` is true division (Python 3). Direction-dependent tests compare with `==`, so `64.0 == 64` succeeds. Do not use `//`.
- Accumulators may be ints, floats, strings, or lists. Do not special-case types.

### Filter / map callables

- `filter`’s predicate and `map`’s transformer take **one** argument (the element).
- Preserve order. Do not sort or unique.
- `filter` that rejects every element returns `[]`.

### Single-element lists

`append([1], [2])` → `[1, 2]`.  
`reverse([1])` → `[1]` (new list).  
`foldl(f, [x], init)` → `f(init, x)`.  
`foldr(f, [x], init)` → `f(init, x)` (same as foldl when n = 1).

---

## 9. What not to do

- Do not leave any stub as `pass` (hidden tests import and call all eight).
- Do not raise on empty inputs; empty is a normal case.
- Do not flatten recursively in `concat` or `reverse`.
- Do not implement `foldr` by calling `function(item, acc)` (swapped arguments).
- Do not use `len`, builtin `map`/`filter`, `reversed`, `[::-1]`, `reduce`, or in-place `list.reverse` / `list.extend`.
- Do not mutate parameters.
- Do not change signatures or add a class-based API.

---

## 10. Suggested file body (reference structure, not a paste-in solution)

One function after another, matching the stub order. Each body is a short loop as in §5. Typical length: ~60–90 lines.

```
append:  two for-loops into a new list
concat:  for-loop over inners, reuse append
filter:  for-loop + if predicate
length:  for-loop + counter
map:     for-loop applying function
foldl:   acc = initial; for-loop updating acc
foldr:   foldl(function, reverse(list), initial)   # or index walk
reverse: index walk from the end, or prepend loop
```

No helper types, no imports. If you add a private helper (e.g. `_copy(xs)`), keep it internal and non-mutating.

---

## 11. Verification the implementer should perform

1. Public: `python -m unittest public_test.py` — `test_append_empty_lists` must pass.
2. Local smoke checks (not to be committed as test-file edits). Manually exercise the tables in §8, especially:
   - `append` empty/left-empty/right-empty/both-nonempty
   - `concat` of nested lists (one-level flatten)
   - `foldl` vs `foldr` with `lambda acc, el: el / acc` on `[1, 2, 3, 4]` starting at `24` → `64` vs `9`
   - `reverse` of a list of lists
   - Identity: save `list1[:]`, call `append(list1, list2)`, assert `list1` unchanged
3. Confirm no forbidden builtins (`len`, `map(`, `filter(`, `reversed`, `reduce`, `[::-1]`, `.extend`, `.reverse(`).

---

## 12. Complexity summary

| Function | Time | Extra space | Notes |
|---|---|---|---|
| `length` | O(n) | O(1) | |
| `append` | O(n+m) | O(n+m) | New list |
| `concat` | O(N) | O(N) | N = total elements |
| `filter` / `map` | O(n) | O(n) | |
| `reverse` | O(n) | O(n) | O(n²) acceptable if prepending |
| `foldl` / `foldr` | O(n) × cost of `function` | O(1) + whatever `function` allocates; `foldr` via `reverse` uses O(n) temp | |

Input sizes in this exercise are tiny; correctness and non-mutation matter more than micro-optimizations.

---

## 13. Implementation checklist

- [ ] `append` returns a new list; empty/empty, empty/nonempty, nonempty/empty, nonempty/nonempty all work; duplicates preserved
- [ ] `concat` one-level flatten; empty outer list; empty inner lists; nested lists remain nested
- [ ] `filter` keeps order; empty in → empty out; predicate not wrapped in builtin `filter`
- [ ] `length` counts top-level items only; empty → 0; no `len()`
- [ ] `map` preserves length and order; empty in → empty out; no builtin `map`
- [ ] `foldl` is left-to-right, `function(acc, el)`; empty returns `initial`
- [ ] `foldr` is right-to-left, **same** `function(acc, el)`; empty returns `initial`; direction-dependent `/` case yields 9 not 64
- [ ] `reverse` is shallow; list-of-lists is not flattened; no `[::-1]` / `reversed`
- [ ] No input mutation
- [ ] Signatures unchanged; module importable as `from list_ops import append, concat, foldl, foldr, length, reverse, filter, map`
