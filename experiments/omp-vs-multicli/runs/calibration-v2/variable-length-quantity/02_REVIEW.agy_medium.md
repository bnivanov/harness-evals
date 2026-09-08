# Code Review: `variable_length_quantity.py`

## Executive Summary

The implementation of `variable_length_quantity.py` was thoroughly reviewed against the specification in `README.md` and the test suite in `public_test.py`. The review verified that:
1. `python3 -m unittest public_test.py` passes cleanly with zero failures or errors.
2. The implementation conforms to the standard 7-bit Variable-Length Quantity (VLQ) encoding and decoding specifications for 32-bit unsigned integers.
3. Edge cases, potential off-by-one errors, algorithmic structures, and performance characteristics were audited in detail.
4. No code defects, off-by-one errors, algorithmic flaws, or performance traps were identified. No code fixes are required.

---

## Verification Results

### Test Execution: `public_test.py`

Command executed:
```bash
python3 -m unittest public_test.py
```

Output:
```text
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

The public test suite validates that `encode([0x0])` returns `[0x0]`.

---

## Detailed Audit

### 1. Specification Conformance (`README.md`)

- **7-Bit Payload & Continuation Flag (Bit 7)**:
  - In `encode(numbers)`:
    - Low 7 bits of each byte (`number & 0x7F`) carry data.
    - Bit 7 (`0x80`) is cleared on the least significant (final) byte of each number.
    - Bit 7 is set (`(number & 0x7F) | 0x80`) on all preceding bytes.
  - In `decode(bytes_)`:
    - Bit 7 signals continuation: `byte & 0x80 != 0`.
    - Data bits (`byte & 0x7F`) are accumulated by shifting previous values left by 7 bits: `value = (value << 7) | (byte & 0x7F)`.
    - Once a byte with bit 7 cleared is encountered (`byte & 0x80 == 0`), the accumulated `value` is emitted, `value` is reset to 0, and `sequence_open` is marked `False`.
- **Byte Ordering (MSB First)**:
  - VLQ requires big-endian (most-significant 7-bit chunk first).
  - In `encode`, chunks are extracted LSB-first into `groups` using repeated `>> 7`, followed by `groups.reverse()` before appending to `encoded`. This guarantees correct MSB-first ordering.
- **Framing and Concatenation**:
  - `encode` processes sequences of numbers and concatenates their byte representations seamlessly without delimiter bytes.
  - `decode` unpacks concatenated variable-length sequences from a flat byte stream into their original integer representations.
- **Specification Table Verification**:
  All standard test vectors from `README.md` encode and decode identically:
  - `00000000` -> `00`
  - `00000040` -> `40`
  - `0000007F` -> `7F`
  - `00000080` -> `81 00`
  - `00002000` -> `C0 00`
  - `00003FFF` -> `FF 7F`
  - `00004000` -> `81 80 00`
  - `00100000` -> `C0 80 00`
  - `001FFFFF` -> `FF FF 7F`
  - `00200000` -> `81 80 80 00`
  - `08000000` -> `C0 80 80 00`
  - `0FFFFFFF` -> `FF FF FF 7F`
  - `10000000` -> `81 80 80 80 00`
  - `FF000000` -> `8F F8 80 80 00`
  - `FFFFFFFF` -> `8F FF FF FF 7F`

---

### 2. Edge Cases & Boundary Conditions

- **Zero (`0x00`)**:
  - `encode([0])`: `groups = [0 & 0x7F] -> [0]`. `number >>= 7` makes `number == 0`, skipping the `while number:` loop. `groups.reverse()` preserves `[0]`. Output: `[0x00]`.
  - `decode([0x00])`: `value = 0`, `byte & 0x80 == 0`. Appends `0`, resets `sequence_open = False`. Output: `[0]`.
- **7-bit boundaries (`0x7F` vs `0x80`)**:
  - `0x7F` is the maximum value representable in 1 byte (`[0x7F]`).
  - `0x80` is the minimum value requiring 2 bytes (`[0x81, 0x00]`).
- **14-bit boundaries (`0x3FFF` vs `0x4000`)**:
  - `0x3FFF` encodes to `[0xFF, 0x7F]`.
  - `0x4000` encodes to `[0x81, 0x80, 0x00]`.
- **21-bit boundaries (`0x1FFFFF` vs `0x200000`)**:
  - `0x1FFFFF` encodes to `[0xFF, 0xFF, 0x7F]`.
  - `0x200000` encodes to `[0x81, 0x80, 0x80, 0x00]`.
- **28-bit boundaries (`0x0FFFFFFF` vs `0x10000000`)**:
  - `0x0FFFFFFF` encodes to `[0xFF, 0xFF, 0xFF, 0x7F]`.
  - `0x10000000` encodes to `[0x81, 0x80, 0x80, 0x80, 0x00]`.
- **32-bit maximum (`0xFFFFFFFF`)**:
  - Requires 5 bytes (bits 28-31 fit in the 5th byte): `[0x8F, 0xFF, 0xFF, 0xFF, 0x7F]`.
  - Encodes and decodes losslessly without overflow or precision loss.
- **Empty inputs**:
  - `encode([])` returns `[]`.
  - `decode([])` returns `[]`. `sequence_open` starts as `False`, so no exception is raised.
- **Incomplete sequences**:
  - Single continuation byte (e.g. `[0x80]`, `[0x81]`, `[0xFF]`): `sequence_open` remains `True` at the end of stream; raises `ValueError("incomplete sequence")`.
  - Incomplete multi-byte sequence (e.g. `[0x8F, 0xFF, 0xFF, 0xFF]`): raises `ValueError("incomplete sequence")`.
  - Complete sequence followed by an incomplete sequence (e.g. `[0x00, 0x80]` or `[0x7F, 0x81, 0x80]`): raises `ValueError("incomplete sequence")`. No partial list is returned.
- **Multiple concatenated values**:
  - Streams containing multiple arbitrary values (e.g. `[0x2000, 0x123456, 0xFFFFFFF, 0x0, 0x3FFF, 0x4000]`) encode and decode symmetrically with round-trip fidelity.

---

### 3. Algorithmic Flaws & Off-By-One Audit

- **Bit shift amounts (`>> 7` and `<< 7`)**:
  - VLQ uses 7-bit chunks. Shifts by 7 are consistently applied. No confusion between 7-bit and 8-bit shifts.
- **Masking (`& 0x7F` vs `| 0x80`)**:
  - Payload extraction correctly isolates the lower 7 bits with `& 0x7F`.
  - Continuation flag is correctly set with `| 0x80`.
  - Continuation condition correctly checks `byte & 0x80`.
- **Termination and State Reset**:
  - In `decode`, `value` is reset to `0` and `sequence_open` is reset to `False` on encountering every terminal byte (`byte & 0x80 == 0`).
  - No state leakage occurs between adjacent decoded integers.
- **Input mutation**:
  - `number >>= 7` rebinds the local iteration variable and does not mutate elements in the caller's `numbers` list.

---

### 4. Performance Traps & Complexity

- **Time Complexity**:
  - `encode`: $O(K)$, where $K$ is the total number of 7-bit groups across all input integers. For 32-bit integers, $K \le 5 \times N$. List reversing (`groups.reverse()`) operates on arrays of length $\le 5$ ($O(1)$ constant time). `encoded.extend(groups)` is amortized $O(1)$ per group.
  - `decode`: $O(M)$, where $M$ is the number of input bytes. Each byte is processed in a single pass with $O(1)$ bitwise operations and an amortized $O(1)$ append.
- **Space Complexity**:
  - $O(1)$ auxiliary space overhead aside from output allocation.
  - No large intermediate allocations or unnecessary string conversions.

---

## Findings & Required Fixes

| Check Category | Status | Details |
|---|---|---|
| Test suite execution | PASS | `python3 -m unittest public_test.py` passes (1 test, 0 failures, 0 errors). |
| Specification compliance | PASS | Conforms to README VLQ rules for 32-bit unsigned integers. |
| Edge cases & boundaries | PASS | 0, 7/14/21/28/32-bit limits, empty arrays, multi-value sequences all verified. |
| Error handling | PASS | Incomplete sequences correctly raise `ValueError("incomplete sequence")`. |
| Off-by-one errors | PASS | Bit offsets and loop conditions are exact. |
| Algorithmic flaws | PASS | State machine and encoding/decoding invariants are preserved. |
| Performance traps | PASS | Optimal $O(N)$ time and minimal $O(1)$ auxiliary space. |

### Required Fixes
**None**. The code in `variable_length_quantity.py` is correct, clean, idiomatic, and adheres strictly to all requirements.
