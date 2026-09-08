# Code Review: `variable_length_quantity.py`

## Executive Summary

The implementation of `variable_length_quantity.py` has been audited against `README.md`, `public_test.py`, and the canonical VLQ specifications. The implementation correctly implements 7-bit variable-length quantity encoding and decoding for unsigned 32-bit integers, properly sets and clears continuation bits, correctly handles boundary cases (including zero, 7/14/21/28-bit boundaries, and 32-bit maximums), handles arbitrary multi-value concatenations, and accurately detects incomplete sequences raising `ValueError("incomplete sequence")`.

Public tests pass cleanly. No code defects, off-by-one errors, or performance bottlenecks were detected. No fixes are required.

---

## Verification Results

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

---

## Detailed Audit

### 1. Specification Conformance (`README.md`)

- **7-bit grouping and continuation bit (Bit 7)**:
  - In `encode`, bits 0–6 contain payload data. Bit 7 is set (`| 0x80`) on all leading bytes and cleared on the final byte of each number.
  - In `decode`, bit 7 signals continuation (`byte & 0x80`). Payload bits (`byte & 0x7F`) are shifted left by 7 and accumulated into `value`.
- **Endianness (MSB first)**:
  - `encode` extracts 7-bit chunks LSB-first into `groups`, then reverses `groups` prior to extending the output. This produces most-significant-byte-first ordering as required.
- **Concatenation and Framing**:
  - `encode` accepts a list of integers and concatenates the resulting byte sequences without separators.
  - `decode` processes the continuous byte stream, emitting each decoded integer upon encountering a byte with bit 7 clear (`byte & 0x80 == 0`).
- **README Test Vectors**:
  All table entries from `README.md` were evaluated and match exact outputs:
  - `0x00000000` -> `[0x00]`
  - `0x00000040` -> `[0x40]`
  - `0x0000007F` -> `[0x7F]`
  - `0x00000080` -> `[0x81, 0x00]`
  - `0x00002000` -> `[0xC0, 0x00]`
  - `0x00003FFF` -> `[0xFF, 0x7F]`
  - `0x00004000` -> `[0x81, 0x80, 0x00]`
  - `0x00100000` -> `[0xC0, 0x80, 0x00]`
  - `0x001FFFFF` -> `[0xFF, 0xFF, 0x7F]`
  - `0x00200000` -> `[0x81, 0x80, 0x80, 0x00]`
  - `0x08000000` -> `[0xC0, 0x80, 0x80, 0x00]`
  - `0x0FFFFFFF` -> `[0xFF, 0xFF, 0xFF, 0x7F]`
  - `0x10000000` -> `[0x81, 0x80, 0x80, 0x80, 0x00]`
  - `0xFF000000` -> `[0x8F, 0xF8, 0x80, 0x80, 0x00]`
  - `0xFFFFFFFF` -> `[0x8F, 0xFF, 0xFF, 0xFF, 0x7F]`

### 2. Edge Case & Boundary Analysis

- **Zero (`0x00`)**:
  - `encode([0])`: `groups = [0 & 0x7F]` initializes `groups` with `[0]`. `number >>= 7` evaluates to `0`, terminating the `while number:` loop immediately. Output is `[0x00]`.
  - `decode([0])`: `value` set to `0`, `byte & 0x80 == 0` is false, appends `0`, resets `sequence_open = False`. Output is `[0]`.
- **Single-byte upper boundary (`0x7F`)**:
  - `encode([0x7F])` yields `[0x7F]`. Loop exits immediately.
- **Two-byte lower boundary (`0x80`)**:
  - `encode([0x80])` extracts `0x00`, then `0x01 | 0x80 = 0x81`. Reversed: `[0x81, 0x00]`.
- **Max 32-bit unsigned (`0xFFFFFFFF`)**:
  - Requires 5 bytes (bits 28-31 fit in the 5th byte: `0x0F | 0x80 = 0x8F`). Encodes to `[0x8F, 0xFF, 0xFF, 0xFF, 0x7F]`. Decodes back to `0xFFFFFFFF`.
- **Empty input**:
  - `encode([])` returns `[]`.
  - `decode([])` returns `[]` without triggering `ValueError`.
- **Incomplete sequences**:
  - Single byte with bit 7 set (e.g., `[0x80]`, `[0x81]`, `[0xFF]`): sets `sequence_open = True`, loop finishes, raises `ValueError("incomplete sequence")`.
  - Incomplete trailing sequence after complete sequence (e.g., `[0x00, 0x80]` or `[0x7F, 0x81, 0x80]`): properly raises `ValueError("incomplete sequence")` and drops partial state.
- **Byte values with 0 payload under continuation** (e.g. `0x80` followed by `0x00` = `0` encoded with leading zero byte, or valid zero payloads in larger numbers):
  - Properly accumulated via `(value << 7) | (byte & 0x7F)`.

### 3. Algorithmic Complexity & Performance

- **Time Complexity**:
  - `encode`: $O(K)$ where $K$ is the number of 7-bit groups across all numbers (at most $5 \times N$ for 32-bit numbers). Each number requires at most 5 iterations and an in-place list reverse of size $\le 5$.
  - `decode`: $O(M)$ where $M$ is the number of input bytes. Single linear pass with constant-time bitwise operations.
- **Space Complexity**:
  - $O(1)$ auxiliary space excluding the output lists.

### 4. Findings & Fixes Required

- **Defects Found**: None.
- **Off-by-one Errors**: None.
- **Algorithmic Flaws**: None.
- **Required Fixes**: None. The implementation is complete and correct.
