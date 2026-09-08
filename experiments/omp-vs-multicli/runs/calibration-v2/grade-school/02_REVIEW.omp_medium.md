# Code Review: `grade_school.py`

## Verdict: PASS

The implementation in `grade_school.py` satisfies all requirements from `README.md`, passes `public_test.py`, and conforms to the complete canonical Exercism specification.

---

## 1. Test Verification

- Command: `python3 -m unittest public_test.py`
- Result: 1/1 tests passing (0.000s, OK).
- Extended canonical behavior audit: 19/19 scenarios passed, covering:
  - Empty roster initialization.
  - Adding single and multiple students to single and multiple grades.
  - Rejecting duplicate additions within the same grade (`added()` logs `False`).
  - Rejecting cross-grade duplicate additions (`added()` logs `False`, student retains initial grade).
  - Multi-grade roster sorting: grade ascending, student name ascending.
  - Single-grade queries: alphabetical sorting within the queried grade.
  - Querying non-existent grades returning empty lists.

---

## 2. API and Interface Conformance

- Class: `School`
- Methods:
  - `__init__(self)`: Initializes internal storage `_students` (`dict[str, int]`) and `_added` (`list[bool]`).
  - `add_student(self, name, grade)`: Signature and parameter names match keyword argument calls (`name=...`, `grade=...`). Returns `None`.
  - `roster(self)`: Returns `list[str]` sorted by grade ascending, then name ascending.
  - `grade(self, grade_number)`: Returns `list[str]` of names in `grade_number` sorted alphabetically.
  - `added(self)`: Returns `list[bool]` tracking success/failure history in call order.

---

## 3. Edge Case & Invariant Audit

| Edge Case | Implementation Handling | Status |
|---|---|---|
| Empty school roster | `roster()` returns `[]` via sorted empty dict items. | Pass |
| Empty school grade query | `grade(n)` returns `[]` via filtered empty dict. | Pass |
| Query for unpopulated grade | Filter condition `student_grade == grade_number` matches 0 items; returns `[]`. | Pass |
| Duplicate name, same grade | `name in self._students` guard triggers: appends `False` to `_added`, returns early without state mutation. | Pass |
| Duplicate name, different grade | Same guard triggers: appends `False`, does not overwrite existing grade. | Pass |
| Callers mutating returned lists | `roster()` creates a new list via comprehension; `grade()` creates a new list via `sorted()`; `added()` returns a shallow copy `list(self._added)`. Internal state is protected. | Pass |
| Sorting tie-breakers | Sort key `(item[1], item[0])` compares `(grade, name)` pairs, correctly establishing numeric grade order then lexicographic name order. | Pass |

---

## 4. Algorithmic Complexity & Performance

- `add_student`: $O(1)$ average time dictionary lookup and insertion; $O(1)$ amortized append to `_added`.
- `roster`: $O(N \log N)$ where $N$ is total enrolled students.
- `grade`: $O(N + K \log K)$ where $N$ is total enrolled students and $K$ is the number of students in the requested grade.
- Space: $O(N)$ for unique student mappings and $O(M)$ for add call history ($M \ge N$).
- Trap analysis: Storing `_students` as a single `dict[str, int]` prevents student-duplication bugs across grades, avoiding complex synchronization between multiple grade-bucket lists.

---

## 5. Findings & Required Fixes

- No syntax errors, off-by-one errors, or algorithmic flaws found.
- No blocking defects.
- Required fixes: None.
