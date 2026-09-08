# Code Review: `grade_school.py`

## Verdict: PASS

The implementation of `School` in `grade_school.py` fully complies with the specification in `README.md`, passes `public_test.py`, and correctly handles all required canonical edge cases, invariants, and performance expectations without defects.

---

## 1. Test Verification

- **Command executed**: `python3 -m unittest public_test.py`
- **Result**:
  ```text
  .
  ----------------------------------------------------------------------
  Ran 1 test in 0.000s

  OK
  ```
- **Extended Test Suite Execution**:
  Tested all canonical behaviors, including:
  - Empty roster query: `roster() == []`
  - Empty grade query: `grade(1) == []`
  - Single student addition and status tracking: `added() == [True]`
  - Multiple students in the same grade (alphabetical order)
  - Duplicate additions within the same grade (`False` recorded in `added()`, student retained once)
  - Duplicate additions across different grades (`False` recorded in `added()`, original grade preserved, student not enrolled in new grade)
  - Multi-grade roster sorting (ascending by grade number, ascending by student name within each grade)
  - Non-existent grade query returns `[]`
  - Defensive copying / mutation isolation of lists returned by `roster()`, `grade()`, and `added()`
  All extended verification tests passed with 0 errors.

---

## 2. Specification & Interface Conformance

Inspected against `README.md` and `public_test.py`:

| Method | Specification Requirement | Conformance in `grade_school.py` | Status |
|---|---|---|---|
| `__init__(self)` | Initialize an empty school state. | Initializes `self._students = {}` and `self._added = []`. | Pass |
| `add_student(self, name, grade)` | Add student if not already enrolled; track success/failure. Accepts keyword args (`name=...`, `grade=...`). | Checks `if name in self._students: self._added.append(False); return`. Otherwise sets `self._students[name] = grade` and appends `True`. | Pass |
| `roster(self)` | Return all enrolled students ordered by grade ascending, then by name alphabetically. | Extracts names from `sorted(self._students.items(), key=lambda item: (item[1], item[0]))`. | Pass |
| `grade(self, grade_number)` | Return students in the specified grade sorted alphabetically. | Extracts names filtered by `student_grade == grade_number` and sorted via `sorted(...)`. | Pass |
| `added(self)` | Return boolean sequence tracking each add attempt in chronological order. | Returns `list(self._added)` (independent list copy). | Pass |

---

## 3. Edge Case Audit

1. **Empty School Queries**:
   - `roster()` returns `[]` because `self._students` is empty.
   - `grade(grade_number)` returns `[]` because the filtered generator yields nothing.
   - `added()` returns `[]` because no add calls have occurred.
2. **Duplicate Student (Same Grade)**:
   - Evaluates `name in self._students` in $O(1)$.
   - Appends `False` to `self._added` and returns without modifying `self._students`.
3. **Duplicate Student (Different Grade)**:
   - Because `_students` is keyed by student name (`dict[name, grade]`), the membership check triggers regardless of the new grade argument.
   - Student's previous grade mapping is unchanged; `False` is appended to `self._added`.
4. **Querying Unpopulated / Non-Existent Grades**:
   - Returns `[]` cleanly without raising exceptions or creating empty buckets in state.
5. **Caller Mutation Defense**:
   - `roster()` builds and returns a brand-new list.
   - `grade()` uses `sorted()`, which returns a brand-new list.
   - `added()` returns `list(self._added)`, a copy of the internal history list.
   - Caller mutations cannot corrupt internal state.

---

## 4. Algorithmic Flaws & Off-By-One Errors Audit

- **Algorithmic Flaws**: None.
  - The choice of storing state as `_students: dict[name, grade]` guarantees global name uniqueness across all grades without needing secondary indices or synchronized data structures.
- **Off-By-One Errors**: None.
  - No manual indexing, range slicing, or offset arithmetic is used.
  - Grade sorting relies on Python's built-in tuple comparison `(grade, name)`, which naturally orders numerically by grade and lexicographically by name.

---

## 5. Performance Traps & Complexity Analysis

- **`add_student(name, grade)`**:
  - Time: $O(1)$ average for dictionary membership check and insertion; $O(1)$ amortized for list append.
  - Space: $O(1)$ per call.
- **`roster()`**:
  - Time: $O(N \log N)$ where $N$ is total enrolled students.
  - Space: $O(N)$ for the returned list.
- **`grade(grade_number)`**:
  - Time: $O(N + K \log K)$ where $N$ is total enrolled students and $K$ is the number of students in the requested grade.
  - Space: $O(K)$ for the returned list.
- **`added()`**:
  - Time: $O(M)$ where $M$ is the number of `add_student` calls.
  - Space: $O(M)$ for the copy.
- **Performance Trap Considerations**:
  - For typical school roster problem sizes, sorting at query time avoids synchronization hazards (such as stale cached lists or dual-maintenance race conditions).
  - No quadratic iterations or redundant deep-copying of nested structures.

---

## 6. Findings & Required Fixes

- **Defects Found**: None.
- **Required Fixes**: None.
- **Conclusion**: The codebase is production-ready, clean, idiomatic, and satisfies all requirements.
