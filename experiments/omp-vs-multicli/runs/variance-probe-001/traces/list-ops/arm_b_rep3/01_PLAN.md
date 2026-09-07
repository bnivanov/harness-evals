# list_ops.py Implementation Guide

## 1. Goal

Implement eight list operations in `list_ops.py` from first principles.

The README requires reimplementing common functional-list operations **without using existing functions** that already do the same work. The public tests only cover `append([], [])`, but the stub and README define a full API. Implement every function completely; do not stop at the single public case.

Keep the eight top-level names and signatures exactly as in the stub. Do not add a class, extra public helpers that change the module API, or type annotations unless they stay compatible with the existing signatures.

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

Parameter name `list` shadows the builtin constructor. Never call `list(...)`. Use `[]` to allocate.

---

## 2. Constraints

### 2.1 Forbidden (do not use)

These already implement the operations being asked for, or hide the algorithm:

| Forbidden | Why |
|---|---|
| `len()` | this is `length` |
| builtin `map()`, `filter()` | these are `map` / `filter` |
| `functools.reduce`, `itertools` (`chain`, `islice`, …) | these are `foldl` / `concat` |
| `reversed()`, `list.reverse()`, slice `[::-1]` | these are `reverse` |
| `list.extend()`, `list.insert()`, `list.pop()` | hide append/concat/reverse |
| `+` or `+=` between two whole lists as the body of `append` / `concat` | hides concatenation |
| `sum(...)` used to count, `enumerate`, `zip` | hide length / pairing |
| in-place mutation of **caller-owned** lists | functional API; tests compare return values and may reuse inputs |

`for item in some_list` is iteration, not a list operation. That is allowed.

### 2.2 Allowed primitives

- `for` / `while`, `if`, arithmetic, comparisons
- integer indexing (`seq[i]`) and non-reversing slices if needed
- `range(...)` (not as a substitute for walking a list when a `for item in list` loop will do)
- allocating `result = []` and appending **one element we already hold**: `result.append(item)`
- calling the other functions in this module

Treat `result.append(item)` as the **only** list-construction primitive. It is not the same operation as `append(list1, list2)`. Using it on a list you allocated is required for O(n) builds.

Do not use `result = result + [item]` or `result = [item] + result` in a loop. Those copy the whole result each time and are quadratic.

### 2.3 Mutation rule

Every function that returns a list must allocate a **new** list.

- Never call `.append`, `.extend`, or item assignment on `list1`, `list2`, `lists`, or the input `list`.
- Nested inner lists may be reused **by reference**. `concat` and `reverse` are one-level operations: they rearrange / flatten one layer of lists, they do not copy inner containers.
- Returning the same object as an input (identity aliasing) is not required and is discouraged. `append(xs, [])` should still return a new list whose contents equal `xs`.

---

## 3. Data structures

No custom types. Use Python lists and scalars.

| Role | Structure | Notes |
|---|---|---|
| Inputs | `list` of items, or `list` of `list`s (`concat`) | Tests use real `list` objects. Iterate with `for x in seq`. Indexing is valid. |
| Output lists | newly allocated `list` | Same element objects as the input, except `map`, which stores call results. |
| Accumulators (`foldl` / `foldr`) | whatever `initial` is | May be `int`, `float`, `list`, or another type. Do not assume a numeric accumulator. |
| Counters (`length`) | `int` starting at `0` | |
| Predicates / transforms | callables | `function(item)` for `filter`/`map`; `function(acc, el)` for both folds. |

Do not convert inputs with `list()`, tuples, deques, or generators. Walk the given sequence directly.

---

## 4. Shared calling convention

### 4.1 Empty list

The empty list is a valid input for every function.

| Function | Empty behavior |
|---|---|
| `append([], [])` | `[]` |
| `append([], ys)` | shallow copy of `ys` |
| `append(xs, [])` | shallow copy of `xs` |
| `concat([])` | `[]` |
| `concat([[], [], ...])` | `[]` |
| `filter(p, [])` | `[]` |
| `length([])` | `0` |
| `map(f, [])` | `[]` |
| `foldl(f, [], init)` | `init` (function never called) |
| `foldr(f, [], init)` | `init` (function never called) |
| `reverse([])` | `[]` |

### 4.2 Order

`append`, `concat`, `filter`, `map`, and `reverse` are order-preserving in the natural sense:

- `append` / `concat`: all items of the first sequence, then the next, and so on.
- `filter` / `map`: original relative order.
- `reverse`: exact reversal of the top-level sequence only.

### 4.3 One-level structure

Nested lists are **items**, not implicit trees.

- `concat` flattens **exactly one** level: a list of lists → one list. Inner lists stay intact.
- `reverse` reverses the top-level sequence only. It must not flatten.
- `append` concatenates two top-level lists; it does not walk nested structure.

Concrete structural cases the implementation must satisfy:

```
concat([[1, 2], [3], [], [4, 5, 6]]) == [1, 2, 3, 4, 5, 6]
concat([[[1], [2]], [[3]], [[]], [[4, 5, 6]]]) == [[1], [2], [3], [], [4, 5, 6]]
reverse([[1, 2], [3], [], [4, 5, 6]]) == [[4, 5, 6], [], [3], [1, 2]]
append([1, 2], [2, 3, 4, 5]) == [1, 2, 2, 3, 4, 5]   # duplicates kept
```

### 4.4 Predicates are booleans, not truthiness of items

`filter(function, list)` keeps `item` iff `function(item)` is true. Do not write `if item`. A predicate such as `lambda x: x % 2 == 1` must be the only membership test.

### 4.5 No extra error handling

Do not raise on empty lists, empty inner lists, or mixed element types. Assume:

- `append` receives two lists
- `concat` receives a list whose elements are lists
- `filter` / `map` / folds receive a callable
- sequences support iteration and (if you index) `seq[i]`

Malformed input is out of scope.

---

## 5. Fold argument order (critical)

README note: *the ordering in which arguments are passed to the fold functions is significant.*

Both folds take the **same** binary callable shape used in the Python tests:

```text
function(accumulator, element) -> new_accumulator
```

They differ only in **traversal direction**.

### 5.1 `foldl` — left to right

```text
foldl(f, [a, b, c], init)  ==  f(f(f(init, a), b), c)
```

Algorithm:

```
acc = initial
for el in list:          # first item first
    acc = function(acc, el)
return acc
```

Worked example (direction-dependent, matches typical tests):

```text
f = (acc, el) -> el / acc
foldl(f, [1, 2, 3, 4], 24)

24, 1 -> 1/24
1/24, 2 -> 48
48, 3 -> 1/16
1/16, 4 -> 64
```

Worked example (direction-independent):

```text
f = (acc, el) -> el + acc
foldl(f, [1, 2, 3, 4], 5) == 15
```

Empty: return `initial` unchanged; never call `function`.

### 5.2 `foldr` — right to left, **same** `function(acc, el)`

```text
foldr(f, [a, b, c], init)  ==  f(f(f(init, c), b), a)
```

This is **not** Haskell `foldr`, which would call `f(element, acc)`. Calling `function(el, acc)` will fail direction-dependent tests.

Worked example:

```text
f = (acc, el) -> el / acc
foldr(f, [1, 2, 3, 4], 24)

24, 4 -> 4/24 = 1/6
1/6, 3 -> 18
18, 2 -> 1/9
1/9, 1 -> 9
```

Empty: return `initial` unchanged.

### 5.3 How to traverse right-to-left without forbidden reverse builtins

Preferred implementation of `foldr`: reuse this module’s `reverse` and `foldl`:

```text
foldr(function, list, initial) == foldl(function, reverse(list), initial)
```

That identity holds **because** both folds use `function(acc, el)`.

If implementing `foldr` independently:

```
acc = initial
i = length(list) - 1
while i >= 0:
    acc = function(acc, list[i])
    i -= 1
return acc
```

Use this module’s `length`, not `len()`.

Do **not** implement `reverse` in terms of `foldr` if `foldr` already uses `reverse` (cycle). See dependency order in §7.

---

## 6. Function-by-function algorithms

Each algorithm is O(n) time and O(n) extra space for the result (O(1) extra besides the output for `length` and the folds when the accumulator is a scalar).

### 6.1 `length(list) -> int`

```
count = 0
for _ in list:
    count += 1
return count
```

- `[]` → `0`
- `[1, 2, 3, 4]` → `4`
- Nested values count as **one** item each: `length([[1, 2], 3]) == 2`

Do not use `len`.

### 6.2 `append(list1, list2) -> list`

Shallow concatenation of two lists into a new list.

```
result = []
for item in list1:
    result.append(item)
for item in list2:
    result.append(item)
return result
```

Cases:

| list1 | list2 | result |
|---|---|---|
| `[]` | `[]` | `[]` |
| `[]` | `[1, 2, 3, 4]` | `[1, 2, 3, 4]` |
| `[1, 2, 3, 4]` | `[]` | `[1, 2, 3, 4]` |
| `[1, 2]` | `[2, 3, 4, 5]` | `[1, 2, 2, 3, 4, 5]` |

Duplicates are retained. Do not deduplicate. Do not mutate `list1`.

### 6.3 `concat(lists) -> list`

One-level flatten: `concat([A, B, C]) == append(append(A, B), C)` conceptually, but **do not** implement it by repeatedly calling `append` on a growing result. That copies the prefix every time and is O(n²).

```
result = []
for inner in lists:
    for item in inner:
        result.append(item)
return result
```

Cases:

- `concat([])` → `[]`
- `concat([[1, 2], [3], [], [4, 5, 6]])` → `[1, 2, 3, 4, 5, 6]`
- empty inner lists contribute nothing
- `concat([[[1], [2]], [[3]], [[]], [[4, 5, 6]]])` → `[[1], [2], [3], [], [4, 5, 6]]`

`concat` of a list of nested lists only unwraps the outer layer. `[[1], [2]]` becomes items `[1]` and `[2]`, not `1` and `2`.

If you want reuse: an inner helper that extends `result` by one inner list using a single-element loop is fine. Calling `append(result, inner)` and replacing `result` is correct but quadratic; avoid it.

### 6.4 `filter(function, list) -> list`

```
result = []
for item in list:
    if function(item):
        result.append(item)
return result
```

Cases:

- `filter(is_odd, [])` → `[]`
- `filter(is_odd, [1, 2, 3, 5])` → `[1, 3, 5]`
- predicate never true → `[]`
- predicate always true → new list with the same items in the same order

Keep original objects, do not copy inner values.

### 6.5 `map(function, list) -> list`

```
result = []
for item in list:
    result.append(function(item))
return result
```

- Output length always equals input length (use `length` mentally; do not call builtin `len` to assert this).
- `map(lambda x: x + 1, [])` → `[]`
- `map(lambda x: x + 1, [1, 3, 5, 7])` → `[2, 4, 6, 8]`
- Preserve order. Apply `function` once per item, left to right.

### 6.6 `foldl(function, list, initial)`

See §5.1. Single left-to-right pass. No special case except empty → `initial`.

Further checks:

- Non-associative / non-commutative `function` must see items from the **left**.
- `initial` may be `[]` or another collection. Example: `foldl(lambda acc, el: acc + [el], [1, 2, 3], [])` builds `[1, 2, 3]` if you were allowed to use `+`; the point is the accumulator can be a list. Do not coerce `initial` to a number.

### 6.7 `foldr(function, list, initial)`

See §5.2. Same callable convention as `foldl`, opposite direction.

Further checks:

- `foldr(lambda acc, el: el / acc, [1, 2, 3, 4], 24)` is `9`, not `64`.
- Empty → `initial`.
- If implemented as `foldl(function, reverse(list), initial)`, that is correct and preferred.

### 6.8 `reverse(list) -> list`

Top-level reverse, new list, no flattening.

O(n) index walk using this module’s `length`:

```
result = []
i = length(list) - 1
while i >= 0:
    result.append(list[i])
    i -= 1
return result
```

Cases:

- `reverse([])` → `[]`
- `reverse([1, 3, 5, 7])` → `[7, 5, 3, 1]`
- `reverse([[1, 2], [3], [], [4, 5, 6]])` → `[[4, 5, 6], [], [3], [1, 2]]`

Do not use `[::-1]`, `reversed()`, or in-place `.reverse()` on the input.

A two-pass version is also fine: copy with `append` into a new list, then swap indices `0..n-1` on **that copy only**. Do not swap on the caller’s list.

---

## 7. Module architecture and dependency order

Implement in this order so each function only depends on already-correct pieces:

```text
length          (iteration + counter)
append          (two iteration passes)
concat          (nested iteration; may call append per item but not per inner list on a growing copy)
reverse         (length + backward index, or copy + swap on the copy)
filter, map     (independent; iteration + predicate/transform)
foldl           (independent left fold)
foldr           (foldl + reverse, or independent backward index using length)
```

Suggested internal reuse (optional, not required):

| Function | May reuse |
|---|---|
| `concat` | conceptually `append`, but implement with nested loops for linear time |
| `foldr` | `reverse` then `foldl` |
| `reverse` | `length` |

Do not build a helper class. A single private helper such as `_push_all(dest, src)` that loops and `dest.append`s each item is acceptable if it stays unused as a public API. Prefer inlining; the file is small.

No imports are required. Do not import `functools`, `itertools`, `operator`, or `copy`.

---

## 8. Edge-case matrix

Implementer should mentally (or with throwaway checks) cover all of these. Do not add a test file; this is the spec.

### 8.1 Emptiness

- Both empty, left empty, right empty for `append`
- Empty outer list for `concat`
- Outer list of only empty inners for `concat`
- Empty input for `filter`, `map`, `length`, `reverse`, both folds

### 8.2 Structure

- Duplicate values in `append` (multiset concatenation, not set union)
- Single-element lists
- `concat` one-level vs two-level nesting (must not deep-flatten)
- `reverse` of a list of lists (must not flatten)
- `length` of a list of lists (count outer items only)

### 8.3 Higher-order functions

- `filter` keeps none / some / all
- `filter` must call the predicate; item truthiness is irrelevant
- `map` of identity preserves values and order
- `map` / `filter` on empty never call `function`
- folds on empty never call `function`
- fold `function` that is not commutative (`el / acc`, `el - acc`)
- fold `function` that is commutative (`el + acc`, `el * acc`) — `foldl` and `foldr` agree
- accumulator type distinct from element type (numeric init with numeric els; list init)

### 8.4 Direction checks (must not swap foldl/foldr)

Use `f = (acc, el) -> el / acc` on `[1, 2, 3, 4]` with init `24`:

| Call | Result |
|---|---|
| `foldl` | `64` |
| `foldr` | `9` |

If these two results are swapped, argument order or traversal is wrong.
If both are `1` (`acc / el` instead of `el / acc`), the callable is being given `(el, acc)` or the operator is reversed.

### 8.5 Identity / algebraic properties

These are correctness checks, not required runtime assertions:

- `append(xs, [])` equals `xs` by content
- `append([], xs)` equals `xs` by content
- `concat([xs])` equals `xs` by content
- `concat([xs, ys])` equals `append(xs, ys)`
- `reverse(reverse(xs))` equals `xs` by content
- `length(append(xs, ys)) == length(xs) + length(ys)`
- `length(map(f, xs)) == length(xs)`
- `length(filter(p, xs)) <= length(xs)`
- `foldl(f, [], i) == foldr(f, [], i) == i`

### 8.6 Non-mutation

After `append(a, b)`, `concat([a, b])`, `reverse(a)`, `filter(...)`, `map(...)`:

- `a` and `b` still have their original top-level contents and identity
- inner list objects that appear in the output of `concat` / `reverse` may be the same objects as in the input (shallow)

---

## 9. Complexity and pitfalls

| Pitfall | Failure mode | Avoid by |
|---|---|---|
| `result = result + inner` inside `concat` | O(n²), may still pass small tests | nested `append` of single items onto one `result` |
| `result = [item] + result` as reverse | O(n²) | backward index + `result.append` |
| `len()`, `[::-1]`, builtin `map`/`filter` | violates README | explicit loops |
| Mutating `list1` in `append` | later reuse of the input is wrong | always allocate `result = []` |
| `foldr` calling `function(el, acc)` | direction-dependent tests fail | always `function(acc, el)` |
| Deep-flattening in `concat` | nested-list case fails | only iterate one inner level |
| Flattening in `reverse` | list-of-lists case fails | move inner lists as whole items |
| `if item` in `filter` | wrong keep/drop | `if function(item)` |
| Using `list(...)` | name shadow, TypeError | `[]` literal |
| `foldl`/`foldr` assuming numeric `initial` | breaks list accumulators | assign `acc = initial` with no conversion |

Target complexity:

- `length`, `foldl`: O(n) time, O(1) extra
- `foldr` via `reverse`+`foldl`: O(n) time, O(n) extra for the reversed copy
- `append`, `concat`, `filter`, `map`, `reverse`: O(n) time, O(n) space for the new list

---

## 10. Implementation sketch (reference, not drop-in)

This is the intended control flow. Write real Python in `list_ops.py` following it. Do not import anything. Do not use forbidden builtins.

```text
append(list1, list2):
    result ← []
    for item in list1: result.append(item)
    for item in list2: result.append(item)
    return result

concat(lists):
    result ← []
    for inner in lists:
        for item in inner:
            result.append(item)
    return result

filter(function, list):
    result ← []
    for item in list:
        if function(item): result.append(item)
    return result

length(list):
    n ← 0
    for _ in list: n ← n + 1
    return n

map(function, list):
    result ← []
    for item in list: result.append(function(item))
    return result

foldl(function, list, initial):
    acc ← initial
    for el in list: acc ← function(acc, el)
    return acc

reverse(list):
    result ← []
    i ← length(list) - 1
    while i >= 0:
        result.append(list[i])
        i ← i - 1
    return result

foldr(function, list, initial):
    return foldl(function, reverse(list), initial)
```

Keep `filter` and `map` named `filter` and `map` in this module. Callers import them as aliases; that is their concern.

---

## 11. What not to do

- Do not edit tests.
- Do not implement only `append` because it is the only public case.
- Do not add exception-raising wrappers, type checks, or docstrings that restate the obvious.
- Do not deep-copy elements (`copy.deepcopy` is unnecessary and can break identity expectations for nested lists).
- Do not return iterators, tuples, or numpy arrays; return built-in `list` (or `int` for `length`, or the accumulator type for folds).

---

## 12. Verification notes for the implementer

`public_test.py` currently checks only `append([], []) == []`. Passing it is necessary and far from sufficient.

After implementing, a correct module will also satisfy the cases in §4.3, §6, and §8.4. Those are the documented README operations plus the standard empty / direction / nesting distinctions this API is defined by.

No file other than `list_ops.py` should be changed when implementing.
