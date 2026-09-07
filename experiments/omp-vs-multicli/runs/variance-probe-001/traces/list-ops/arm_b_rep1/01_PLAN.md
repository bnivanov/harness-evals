# List Ops Implementation Guide

This document is the complete architecture and implementation plan for `list_ops.py`. Implement only that module. Do not change tests.

Source of truth in this workspace:

- `README.md` — required operations and informal semantics
- `list_ops.py` — function names and signatures
- `public_test.py` — currently only `append([], []) == []`

The public suite is a stub. Hidden tests will cover every exported function, empty/non-empty inputs, order-sensitive folds, and nested lists. Implement the full API below, not just the one public case.

---

## 1. Goal

Reimplement a small functional list toolkit in pure Python, using only primitive iteration and list construction. Do **not** call the Python builtins / methods that already provide these operations.

Export exactly these eight callables (names must match the stub and the test imports):

| Function | Stub signature | Returns |
|---|---|---|
| `append` | `append(list1, list2)` | new list |
| `concat` | `concat(lists)` | new list |
| `filter` | `filter(function, list)` | new list |
| `length` | `length(list)` | `int` |
| `map` | `map(function, list)` | new list |
| `foldl` | `foldl(function, list, initial)` | accumulator |
| `foldr` | `foldr(function, list, initial)` | accumulator |
| `reverse` | `reverse(list)` | new list |

Keep those public names. Internally, rename the parameter `list` to `lst` (or similar) so it does not shadow the builtin type. Callers use positional arguments, so parameter names are not part of the contract.

---

## 2. Hard constraints

### 2.1 Forbidden (do not use)

These either *are* the operations being implemented or make the exercise trivial:

- `len()`
- builtin `map()`, `filter()`, `sum()`, `any()`, `all()`, `min()`, `max()`, `sorted()`, `reversed()`
- `functools.reduce` and anything in `itertools`
- `list.extend`, `list.insert`, `list.pop`, `list.remove`, `list.reverse`, `list.clear`, `list.copy`, `list.index`, `list.count`
- Concatenating two whole lists in one shot: `list1 + list2`, `[*list1, *list2]`, `list1 += list2`
- Slice reverse / copy-as-substitute: `lst[::-1]`, `lst[:]`, `lst[i:j]` used to copy or reverse a whole list
- In-place mutation of any caller-supplied list

List comprehensions that are just `map`/`filter` in disguise (`[f(x) for x in lst]`, `[x for x in lst if p(x)]`) should not be used. Write explicit loops so each operation’s algorithm is obvious.

### 2.2 Allowed primitives

- `for item in lst:` left-to-right iteration
- Creating a fresh `result = []`
- **Local constructor only:** `result.append(item)` on a list *you* allocated in this function, never on an input
- Indexing `lst[i]` and `range(...)` if a right-to-left walk is needed
- Integer arithmetic for the counter in `length`
- Calling the other functions defined in this module
- Empty-list test via `for` (zero iterations) or `length(lst) == 0`. Prefer “loop zero times” over a special case when the general algorithm already handles empty input.

### 2.3 Functional style

Every operation that returns a list must return a **new** list. Inputs are treated as immutable. Nested list *elements* are not copied; they are reused by reference (shallow). That is required for reverse/concat of nested lists: inner lists keep identity and order.

---

## 3. Data structures

Use Python lists as the only sequence type.

- Inputs are ordinary `list` objects. Elements may be any Python value: ints, empty lists, nested lists, etc.
- Results that are sequences are new `list` objects.
- No custom linked-list class, no `collections.deque`, no tuples as the public result type.
- Accumulators in `foldl` / `foldr` have whatever type `initial` and `function` produce. Do not coerce them.

There is no extra module-level state. All functions are pure.

---

## 4. Semantic specification

Treat items as opaque. Never inspect an element’s type except by passing it to the caller-provided function.

### 4.1 `append(list1, list2)`

Return a new list containing every item of `list1` (in order) followed by every item of `list2` (in order). One level only: if an element is itself a list, it is one item, not flattened.

```
append([], [])           -> []
append([], [1, 2, 3])    -> [1, 2, 3]
append([1, 2, 3], [])    -> [1, 2, 3]
append([1, 2], [2, 3])   -> [1, 2, 2, 3]
```

Identities:

- `append([], xs) == xs` (equal contents; still a new list)
- `append(xs, []) == xs`
- `append(xs, ys)` does not modify `xs` or `ys`

### 4.2 `concat(lists)`

`lists` is a list of lists. Flatten **exactly one** level: concatenate the inner lists from left to right.

```
concat([])                               -> []
concat([[], [], []])                     -> []
concat([[1, 2], [3], [], [4, 5, 6]])     -> [1, 2, 3, 4, 5, 6]
concat([[[1], [2]], [[3]], [[]], [[4, 5, 6]]])
    -> [[1], [2], [3], [], [4, 5, 6]]
```

The last example is the important nested case: inner lists stay lists. `concat` is not a deep flatten.

`concat` is the fold of `append` over the outer list, starting from `[]`.

### 4.3 `filter(function, lst)`

Return a new list of those items for which `function(item)` is truthy, original order preserved.

README wording is “predicate(item) is True”. Callers pass real predicates that return booleans (`x % 2 == 1`). Use `if function(item):` (Python truthiness). Do not special-case `is True` unless a predicate actually returns a non-bool; tests use bools.

```
filter(lambda x: True, [])              -> []
filter(lambda x: x % 2 == 1, [1,2,3,5]) -> [1, 3, 5]
```

Do not call `function` on items you then discard except as the predicate. Do not mutate items.

### 4.4 `length(lst)`

Return the number of **top-level** items. Nested lists count as one item each.

```
length([])              -> 0
length([1, 2, 3, 4])    -> 4
length([[], [], []])    -> 3
```

This is a counter loop, not `len()`.

### 4.5 `map(function, lst)`

Return a new list ` [function(item) for each item] ` in the same order. Empty in, empty out. One pass, no flattening.

```
map(lambda x: x + 1, [])           -> []
map(lambda x: x + 1, [1, 3, 5, 7]) -> [2, 4, 6, 8]
```

### 4.6 `foldl(function, lst, initial)` — left fold

Argument order of `function` is **`(accumulator, element)`** for both folds. This is the Python-track convention and is **not** Haskell `foldr`’s `(element, accumulator)`.

Left fold applies the function from the head toward the tail:

```
foldl(f, [a, b, c], z) == f(f(f(z, a), b), c)
```

Empty list: return `initial` unchanged (never call `function`).

Direction-independent example (addition is commutative):

```
foldl(lambda acc, el: el + acc, [1, 2, 3, 4], 5) -> 15
```

Direction-dependent example. The tests use a lambda that *names* parameters `(acc, el)` but computes `el / acc` (float division):

```
foldl(lambda acc, el: el / acc, [1, 2, 3, 4], 24) -> 64
```

Worked steps (`acc` starts at 24):

1. `el=1` → `1 / 24`
2. `el=2` → `2 / (1/24) = 48`
3. `el=3` → `3 / 48 = 0.0625`
4. `el=4` → `4 / 0.0625 = 64`

If you reverse the argument order inside `function(...)` this value will be wrong.

### 4.7 `foldr(function, lst, initial)` — right fold

Same `function(acc, el)` convention. Reduce from the **tail** toward the **head**:

```
foldr(f, [a, b, c], z) == f(f(f(z, c), b), a)
```

Empty list: return `initial`.

Direction-independent:

```
foldr(lambda acc, el: el + acc, [1, 2, 3, 4], 5) -> 15
```

Direction-dependent (same lambda as above):

```
foldr(lambda acc, el: el / acc, [1, 2, 3, 4], 24) -> 9
```

Worked steps (`acc` starts at 24, elements from the right):

1. `el=4` → `4 / 24 = 1/6`
2. `el=3` → `3 / (1/6) = 18`
3. `el=2` → `2 / 18 = 1/9`
4. `el=1` → `1 / (1/9) = 9`

Algebraic relationship you should rely on:

```
foldr(f, lst, z) == foldl(f, reverse(lst), z)
```

That identity holds **only because** both folds pass `(acc, el)` in the same order. Do not “swap arguments” when reusing `foldl`.

### 4.8 `reverse(lst)`

New list, top-level order reversed. Nested lists are not reversed inside.

```
reverse([])                         -> []
reverse([1, 2, 3, 4])               -> [4, 3, 2, 1]
reverse([[1, 2], [3], [], [4, 5, 6]])
    -> [[4, 5, 6], [], [3], [1, 2]]
```

---

## 5. Architecture

Single module, eight public functions, no classes.

Recommended internal layering:

```
length, reverse, append, map, filter, foldl   ← independent primitives
concat  ← loop of append (or equivalent nested loop)
foldr   ← foldl(function, reverse(lst), initial)
           OR an index walk from length(lst)-1 down to 0
```

Composition is preferred over duplicating loops, as long as you do not introduce mutation or forbidden builtins.

Do **not** implement `length` via `foldl` that adds 1 if that feels cute but obscures the counter; a direct count is clearer. Either is correct if it avoids `len()`.

---

## 6. Algorithms

All of these are one or two linear passes. Use them as written.

### 6.1 `length`

```
count ← 0
for each item in lst:
    count ← count + 1
return count
```

### 6.2 `append`

```
result ← []
for each item in list1:
    result.append(item)      # local result only
for each item in list2:
    result.append(item)
return result
```

Do not `list1.append(...)`. Do not `return list1 + list2`.

### 6.3 `concat`

```
result ← []
for each inner in lists:
    result ← append(result, inner)
return result
```

Equivalent nested form (also fine, one allocation):

```
result ← []
for each inner in lists:
    for each item in inner:
        result.append(item)
return result
```

The nested form is O(total items). Repeated `append(result, inner)` that copies `result` each time is O(n²) if `append` copies; if `append` builds a new list by walking both arguments it is still O(n²) across the outer loop. Prefer the single `result` nested loop so hidden tests with larger concatenations stay cheap.

### 6.4 `filter`

```
result ← []
for each item in lst:
    if function(item):
        result.append(item)
return result
```

### 6.5 `map`

```
result ← []
for each item in lst:
    result.append(function(item))
return result
```

### 6.6 `reverse`

Build by inserting at the front of a new list **without** `insert(0, ...)` (that is O(n²) and a forbidden-ish method). Two O(n) options:

**A. Append then walk backwards with indices**

```
n ← length(lst)
result ← []
i ← n - 1
while i >= 0:
    result.append(lst[i])
    i ← i - 1
return result
```

**B. Fold / prepend using a second list**

Walk left to right, appending each item onto a *new* list that starts with the current item and then copies the previous result. That is O(n²). Do not do this.

Use **A**.

Do not use `lst[::-1]` or `reversed(lst)`.

### 6.7 `foldl`

```
acc ← initial
for each item in lst:
    acc ← function(acc, item)
return acc
```

Call is `function(acc, item)` — accumulator first.

### 6.8 `foldr`

**Preferred:** reuse `reverse` + `foldl`:

```
return foldl(function, reverse(lst), initial)
```

**Alternative:** index from the right:

```
acc ← initial
i ← length(lst) - 1
while i >= 0:
    acc ← function(acc, lst[i])
    i ← i - 1
return acc
```

**Do not** recurse on `lst[1:]` (slicing is forbidden as a list-copy stand-in, and it is O(n²)).

**Do not** write `function(item, acc)`. That is the Haskell argument order and will fail the division tests.

---

## 7. Suggested implementation order

1. `length` — no dependencies; easiest empty-list case (`0`).
2. `append` — two loops; satisfies the one public test immediately.
3. `reverse` — needs `length` if using index walk.
4. `foldl` — one loop.
5. `foldr` — `foldl` + `reverse`.
6. `map`, `filter` — same loop shape as `append`’s first half.
7. `concat` — nested loop or repeated `append` on a shared result list.

After each function, mentally run the examples in §4.

---

## 8. Edge cases and invariants

| Case | Expected |
|---|---|
| Empty list for `map` / `filter` / `reverse` / `append` / `concat` | `[]` (new list) |
| `append` with either side empty | the other side’s items, in order |
| `concat([])` | `[]` |
| `concat` of empty inner lists | `[]` |
| `length([])` | `0` |
| `foldl` / `foldr` on `[]` | `initial` (including `0`, `2`, `[]`, etc.) |
| Nested lists in `length` | count outer items only |
| Nested lists in `reverse` | reverse outer order only |
| Nested lists in `concat` | flatten exactly one level |
| Duplicate values | preserved (`append([1,2],[2,3])` → `[1,2,2,3]`) |
| Predicate never true | `[]` |
| Predicate always true | shallow copy of items, new list |
| Fold function that is not commutative | order as in §4.6–4.7 |
| `/` in fold tests | true division; do not use `//` |
| Caller lists after any call | identical contents and identity of inner objects |

Invariants:

1. No public function mutates its list arguments.
2. List-returning functions return a list object that is not one of the inputs (`append([], x)` may still allocate a new `[]` or a new copy of `x`; always allocate a new list so identity is not shared with an input).
3. Order of kept items is stable (`filter`, `map`, `append`, `concat`).
4. `length(append(a, b)) == length(a) + length(b)`.
5. `length(map(f, a)) == length(a)`.
6. `reverse(reverse(a))` equals `a` at the top level.
7. `foldl(f, [], z) == foldr(f, [], z) == z`.

---

## 9. Complexity targets

Let `n` be the number of top-level items touched.

| Function | Time | Extra space |
|---|---|---|
| `length` | O(n) | O(1) |
| `append` | O(\|list1\| + \|list2\|) | O(\|list1\| + \|list2\|) for the copy |
| `concat` | O(total inner items) | O(total inner items) |
| `filter` / `map` / `reverse` | O(n) | O(n) |
| `foldl` | O(n) | O(1) besides what `function` allocates |
| `foldr` via reverse | O(n) | O(n) for the reversed copy |

Avoid O(n²) concatenation in `concat` and O(n²) prepend in `reverse`.

---

## 10. Testing strategy (implementer)

Do not edit `public_test.py`. Run it as a smoke check:

```
python -m unittest public_test.py
```

It only asserts `append([], []) == []`. Before considering the module done, self-check with a throwaway scratch session (not a committed test file) covering:

- `append` empty/left/right/both non-empty
- `concat` empty, empty inners, mixed, one-level nested lists
- `filter` empty and odd-number predicate
- `length` empty, flat, list of empty lists
- `map` increment
- `foldl` / `foldr` empty; `el + acc` with init `5`; `el / acc` with `[1,2,3,4]` and init `24` expecting `64` and `9`
- `reverse` empty, flat, nested

Then delete any scratch driver. Ship only `list_ops.py` changes.

---

## 11. Pitfalls (read before coding)

1. **Fold argument order.** `function(acc, el)`, not `function(el, acc)`. Confirm with the `/` traces in §4.6–4.7.
2. **`foldr` ≠ Haskell `foldr`.** Because the binary function takes acc first, right fold is “`foldl` on the reversed list”, not “swap the lambda’s arguments”.
3. **`concat` is not `sum(lists, [])` and not deep flatten.**
4. **`length([[],[],[]])` is 3, not 0.**
5. **Do not use `len`, `+` on two lists, `[::-1]`, builtin `map`/`filter`.** Hidden checks and the exercise rules both forbid them.
6. **Do not mutate inputs** then return them. Even `list1.extend(list2); return list1` fails both mutation and “new list” requirements.
7. **Shadowing.** The stub parameter name `list` hides the builtin; rename locally.
8. **Integer vs float.** Leave `/` results as floats. Do not `int(...)`.
9. **`filter` vs builtin.** The tests import `filter as list_ops_filter` because the name collides. Your function must still be defined as `filter`.
10. **Empty fold.** Returning `None` or `[]` instead of `initial` will fail.

---

## 12. File-level sketch (for the implementer)

`list_ops.py` should look like: module docstring optional; eight functions; no extra public names; no imports (none are needed). Each body is a short loop as in §6. No comments that narrate the exercise. A one-line comment on `foldr` noting `(acc, el)` and “right-to-left = foldl on reversed list” is acceptable because that constraint is non-obvious.

Do not add `__all__` unless you want it; tests import names directly.

---

## 13. Mapping from README names to code names

README says `concatenate`; the stub and tests say `concat`. Implement `concat`.

README says “a series of lists”; the stub takes one argument `lists` (a list of lists), not `*lists`. Do not use varargs.

---

## 14. Done criteria

- All eight functions implemented per §4 and §6.
- No forbidden APIs from §2.1.
- Inputs never mutated.
- `python -m unittest public_test.py` passes.
- Manual checks in §10 pass, especially foldl=64, foldr=9, concat nested one-level, reverse nested outer-only, length of `[[],[],[]]` is 3.
