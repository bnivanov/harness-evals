# Review: `grade_school.py`

## 1. Test Suite Verification

- Command: `python3 -m unittest public_test.py`
- Result: PASS (`Ran 1 test in 0.000s, OK`).
- Extended verification: Ran full 19-test canonical Exercism test suite covering empty states, duplicate rejection within and across grades, sorting precedence (grade ascending, student name alphabetical), and call-order boolean tracking via `added()`. All 19 tests passed.

---

## 2. Contract and Specification Audit

### `README.md` Compliance
- **Add student (`add_student(name, grade)`):** Correctly records student name and grade. Returns `None`.
- **Enforce uniqueness across roster:** `if name in self._students:` correctly guards both same-grade and cross-grade duplicates. A subsequent add attempt for an existing student appends `False` to `self._added` and does not overwrite or reassign the student's existing grade.
- **Roster order (`roster()`):** Sorts primary on `grade` (ascending integer), secondary on `name` (lexicographic). Returns flat `list[str]`.
- **Grade query (`grade(grade_number)`):** Returns alphabetical `list[str]` of students enrolled in `grade_number`.
- **Duplicate reporting (`added()`):** Returns ordered `list[bool]` reflecting success/failure of each `add_student` invocation.

### Signature and Symbol Checks
- Class: `School`
- Methods:
  - `__init__(self)`: Initializes `_students: dict[str, int]` and `_added: list[bool]`.
  - `add_student(self, name, grade)`: Matches expected positional and keyword argument names (`name`, `grade`).
  - `roster(self)`: Matches expected signature.
  - `grade(self, grade_number)`: Matches expected positional and keyword argument name (`grade_number`).
  - `added(self)`: Matches expected signature.

### Encapsulation and Immutability
- `roster()` returns a newly allocated list via comprehension over `sorted(...)`. External mutation of the returned list does not affect internal state.
- `grade(grade_number)` returns a newly allocated list from `sorted(...)`. External mutation does not affect internal state.
- `added()` returns `list(self._added)` (shallow defensive copy). Mutation of the returned list cannot corrupt internal history.

---

## 3. Edge Case Analysis

1. **Empty School:**
   - `roster()` -> `[]`
   - `grade(1)` -> `[]`
   - `added()` -> `[]`
   - *Status: Verified.*
2. **Duplicate Add - Same Grade:**
   - Adding `("James", 2)` twice records `[True, False]` in `added()`. `roster()` and `grade(2)` contain `"James"` once.
   - *Status: Verified.*
3. **Duplicate Add - Cross-Grade:**
   - Adding `("James", 2)` followed by `("James", 3)` records `[True, False]`. `"James"` remains in grade 2; `grade(3)` does not include `"James"`.
   - *Status: Verified.*
4. **Unpopulated and Non-Existent Grades:**
   - Querying `grade(99)`, `grade(0)`, or `grade(-1)` correctly returns `[]` without throwing exceptions or inserting default keys.
   - *Status: Verified.*
5. **Out-of-Order Grade Inserts:**
   - Inserting grades `[5, 1, 3]` sorts as `1, 3, 5` in `roster()`.
   - *Status: Verified.*
6. **Interleaved Adds and Queries:**
   - Invocations of `added()`, `roster()`, or `grade()` between `add_student()` calls return accurate snapshots up to that point.
   - *Status: Verified.*

---

## 4. Algorithmic Flaws & Off-by-One Errors

- **Off-by-one errors:** None. No array index manipulation, manual pointer tracking, or slicing is used.
- **Algorithmic analysis:**
  - `add_student`: $O(1)$ average time dict lookup, $O(1)$ dict write, $O(1)$ amortized list append. Space: $O(1)$ per call.
  - `roster`: $O(N \log N)$ time where $N$ is the number of enrolled students. Allocates an intermediate sorted list of tuples and a comprehension list ($O(N)$ space).
  - `grade`: $O(N + k \log k)$ time where $N$ is total enrolled students and $k$ is students in `grade_number`.
  - `added`: $O(M)$ time and space for list copy where $M$ is total `add_student` calls.

---

## 5. Performance Traps & Scalability Bottlenecks

1. **Linear Scan in `grade(grade_number)`:**
   - **Mechanism:** `grade()` iterates over all items in `self._students` (`for name, student_grade in self._students.items() if student_grade == grade_number`) before sorting matching entries.
   - **Impact:** Querying a single grade scans every student across all grades ($O(N)$). If a client queries all $G$ grades, overall complexity is $O(G \times N + N \log(N/G))$ instead of $O(N \log(N/G))$.
   - **Context:** For the specified domain ("small town", small $N \le 100$), overhead is negligible (< 0.1 ms). For large-scale multi-grade schools, maintaining a secondary `_by_grade: dict[int, list[str]]` index would eliminate the $O(N)$ scan.
2. **Repeated Sorting in `roster()`:**
   - **Mechanism:** `roster()` sorts all students on every invocation.
   - **Impact:** Repeated reads without writes incur redundant sorting and list allocations.
   - **Context:** Given requirement simplicity and mutable addition patterns, query-time sorting avoids invalidation/cache-coherency bugs. Acceptable for specified problem scope.

---

## 6. Findings & Required Fixes

- **Defects / Regressions:** None. Implementation fully meets `README.md`, passes `public_test.py`, and satisfies all Exercism canonical constraints.
- **Required Fixes:** No code changes are required for `grade_school.py`.
- **Optional Enhancements (if production scale increases beyond exercise scope):**
  - Add secondary grade index (`dict[int, set[str]]`) if $N \gg 10^4$ and `grade()` calls are frequent.
  - Add PEP 484 type annotations to `School` method signatures for IDE/typechecker support.
