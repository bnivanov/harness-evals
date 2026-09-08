# Implementation Guide: `grade_school.py`

## Problem

Maintain a school roster of unique student names, each in exactly one grade.

Callers must be able to:

1. Attempt to add a student to a grade (`add_student`).
2. List every enrolled student, ordered by grade then name (`roster`).
3. List students in one grade, ordered by name (`grade`).
4. Inspect, in call order, whether each add attempt succeeded (`added`).

Source of truth for the public surface is the stub in `grade_school.py`. Behavior is specified by `README.md` and the Exercism grade-school Python tests generated from `canonical-data.json` (2023-07-19). The checked-in `public_test.py` only covers the empty-roster case; the implementation must still satisfy the full contract below.

## Public API

```python
class School:
    def __init__(self) -> None: ...
    def add_student(self, name: str, grade: int) -> None: ...
    def roster(self) -> list[str]: ...
    def grade(self, grade_number: int) -> list[str]: ...
    def added(self) -> list[bool]: ...
```

Parameter names are load-bearing. Tests call `add_student(name=..., grade=...)`. Do not rename them.

No method returns a status from `add_student`. Success/failure is recorded internally and read later via `added()`.

## Data structures

Keep two private fields. Nothing else is required.

| Field | Type | Role |
|---|---|---|
| `_students` | `dict[str, int]` | Maps enrolled name → grade. Dict membership is the uniqueness check. Insertion order is irrelevant; queries sort. |
| `_added` | `list[bool]` | One entry per `add_student` call, in call order. `True` = enrolled, `False` = rejected. |

Rejected names are **not** stored in `_students`. A failed add leaves the roster unchanged.

Do not use `defaultdict`, nested grade→list maps, or a separate `set` of names. A name→grade dict already:

- answers “is this student already enrolled?” in O(1)
- preserves the original grade on a later conflicting add
- is enough to rebuild both `roster()` and `grade()` with a sort

Keep lists returned to callers independent of internals. Build a new list on every query. Returning a live internal list is unnecessary and invites mutation bugs.

## Invariants

1. Every name in `_students` appears at most once. Names are compared exactly (case-sensitive, no strip/normalize).
2. A name that is already a key in `_students` is never reassigned, even if the new `grade` differs.
3. `len(_added)` equals the number of `add_student` calls on this instance.
4. `len(_students)` equals the number of `True` values in `_added`.
5. `roster()` is the concatenation of `grade(g)` for every occupied grade `g` in ascending numeric order.
6. `grade(n)` contains exactly the names whose mapped grade is `n`, sorted lexicographically.
7. An unknown or empty grade yields `[]`, not `None`.
8. A brand-new `School` has `_students == {}` and `_added == []`.

## Algorithms

### `__init__`

```python
self._students = {}
self._added = []
```

No other setup.

### `add_student(name, grade)`

```
if name in self._students:
    append False to _added
    return
store name → grade in _students
append True to _added
```

Do not raise. Do not return a bool. Do not move the student. Do not record the rejected grade anywhere.

`name in self._students` covers both “same grade twice” and “same student, different grade”. Those are the same uniqueness rule.

### `roster()`

```
return [name for name, _grade in sorted(
    self._students.items(),
    key=lambda item: (item[1], item[0]),
)]
```

Sort key is `(grade, name)`:

- numeric grade ascending (`1` before `2` before `5`)
- within a grade, Python’s default string order (ASCII/Unicode code point; tests use Title Case ASCII names)

Empty school → `[]`.

### `grade(grade_number)`

```
return sorted(
    name for name, g in self._students.items() if g == grade_number
)
```

Empty result when:

- no students exist at all
- students exist, but none in `grade_number`

Do not create a placeholder entry for empty grades.

### `added()`

```
return list(self._added)
```

A shallow copy is enough (elements are bools). Tests only `assertEqual` against a list of bools, but copying avoids accidental coupling.

`added()` after zero adds returns `[]`. There is no public-test for that, but it follows from invariant 3.

## Edge cases (must handle)

| Case | Expected |
|---|---|
| No students | `roster() == []`, `grade(any) == []` |
| Single student | `roster()` is that one name; `added() == [True]` |
| Several students, same grade | All accepted; `roster()` and `grade(n)` are alphabetical |
| Several students, different grades | `roster()` ordered by grade then name |
| Duplicate add, same grade | Second call appends `False`; roster unchanged; original grade kept |
| Duplicate add, different grade | Same as above: `False`, student stays in first grade, not copied into the new grade |
| Duplicate among other successful adds | `added()` is mixed `[True, True, False, True]` in call order |
| Query a grade that was never used | `[]` |
| Query a grade after a rejected add that targeted it | Still `[]` if no successful add landed there |
| Names that sort before/after each other (`Alex`, `Peter`, `Zoe`) | Alphabetical inside the grade |
| Grades not inserted in numeric order (`3` then `2` then `1`) | `roster()` still `["Anna", "Peter", "Jim"]` style |
| `added()` inspected after some adds, then more adds | Later `added()` includes the full history |

Names are unique tokens. Do not treat `"Jim"` and `"jim"` as the same student; tests never collide on case, and the spec does not ask for case-folding.

Grades are integers. Tests use positive ints (`1`, `2`, `3`, `5`, `7`). Do not special-case zero or negatives; if they appear, treat them as ordinary sort keys.

## Worked examples (from the spec / canonical tests)

**Empty**

```
School()
roster() -> []
grade(1) -> []
```

**Add one**

```
add_student(name="Aimee", grade=2)
added()  -> [True]
roster() -> ["Aimee"]
```

**Same-grade duplicates**

```
add_student("Blair", 2)   # True
add_student("James", 2)   # True
add_student("James", 2)   # False — already enrolled
add_student("Paul", 2)    # True
added()     -> [True, True, False, True]
roster()    -> ["Blair", "James", "Paul"]
grade(2)    -> ["Blair", "James", "Paul"]
```

**Cross-grade duplicate (must not move)**

```
add_student("Blair", 2)   # True
add_student("James", 2)   # True
add_student("James", 3)   # False — already in grade 2
add_student("Paul", 3)    # True
added()     -> [True, True, False, True]
roster()    -> ["Blair", "James", "Paul"]
grade(2)    -> ["Blair", "James"]
grade(3)    -> ["Paul"]
```

**Sort by grade then name**

```
Peter/2, Anna/1, Barb/1, Zoe/2, Alex/2, Jim/3, Charlie/1
roster() -> ["Anna", "Barb", "Charlie", "Alex", "Peter", "Zoe", "Jim"]
```

**Sort within a grade**

```
Franklin/5, Bradley/5, Jeff/1
grade(5) -> ["Bradley", "Franklin"]
grade(1) -> ["Jeff"]
```

## Implementation notes

- File: `grade_school.py` only. Keep the existing `School` class; fill in the four methods and `__init__`.
- No extra public methods, properties, or module-level helpers.
- No I/O, no exceptions for normal duplicate adds, no logging.
- Sorting is done at query time. The roster is tiny; do not maintain a pre-sorted cache.
- `sorted` on strings is sufficient; do not use `locale` or case-insensitive keys.
- Prefer the name→grade dict over a grade→names map so a rejected cross-grade add cannot accidentally append the name to a second list.
- Do not mutate lists returned by previous `roster()` / `grade()` / `added()` calls when later adds happen. Fresh lists on each call satisfy this.

## Verification (for the implementer)

1. Empty school: `roster() == []`.
2. One add: `added() == [True]`, `roster() == [that name]`.
3. Three distinct same-grade names: `added()` all `True`; `roster()` alphabetical.
4. Repeat name, same grade: corresponding `added()` entry `False`; name appears once.
5. Repeat name, other grade: `False`; name stays in first grade; other grade’s `grade()` does not include them.
6. Mixed grades inserted out of order: `roster()` is grade-major, name-minor.
7. `grade(n)` empty when unused; sorted when populated.
8. `added()` length always matches the number of `add_student` calls.

Do not edit tests. Do not add files other than the implementation when coding this plan.
