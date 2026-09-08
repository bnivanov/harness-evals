# Plan: Variable Length Quantity (`variable_length_quantity.py`)

## Problem

Implement MIDI-style VLQ encode/decode for 32-bit unsigned integers.

Public API (already stubbed):

```python
def encode(numbers): ...
def decode(bytes_): ...
```

Both take and return `list[int]`. Bytes are integer values in `0..255`, not `bytes` objects.

Restriction from README: values fit in a 32-bit unsigned integer (`0 .. 0xFFFFFFFF`). Do not add extra range validation unless a test demands it. Python `int` is unbounded; just treat inputs as non-negative integers.

## Encoding rules

Each integer becomes one or more bytes:

- Payload is the low 7 bits of each byte (`value & 0x7F`).
- Bit 7 is the continuation flag:
  - `1` (`| 0x80`) on every byte except the last of that integer.
  - `0` on the last byte.
- Groups are emitted **most-significant 7-bit group first**.
- Do **not** emit leading zero groups. Exception: integer `0` encodes as the single byte `0x00`.
- `encode` concatenates the encodings of every integer in `numbers` in order. There is no length prefix or separator; the continuation bit is the only framing.

Worked examples from the README (and the 32-bit extremes implied by the same packing):

| number       | 7-bit groups (MSB first)     | VLQ bytes              |
|--------------|------------------------------|------------------------|
| `0x00000000` | `00`                         | `00`                   |
| `0x00000040` | `40`                         | `40`                   |
| `0x0000007F` | `7F`                         | `7F`                   |
| `0x00000080` | `01 00`                      | `81 00`                |
| `0x00002000` | `40 00`                      | `C0 00`                |
| `0x00003FFF` | `7F 7F`                      | `FF 7F`                |
| `0x00004000` | `01 00 00`                   | `81 80 00`             |
| `0x00100000` | `40 00 00`                   | `C0 80 00`             |
| `0x001FFFFF` | `7F 7F 7F`                   | `FF FF 7F`             |
| `0x00200000` | `01 00 00 00`                | `81 80 80 00`          |
| `0x08000000` | `40 00 00 00`                | `C0 80 80 00`          |
| `0x0FFFFFFF` | `7F 7F 7F 7F`                | `FF FF FF 7F`          |
| `0x10000000` | `01 00 00 00 00`             | `81 80 80 80 00`       |
| `0xFF000000` | `0F 78 00 00 00`             | `8F F8 80 80 00`       |
| `0xFFFFFFFF` | `0F 7F 7F 7F 7F`             | `8F FF FF FF 7F`       |

A 32-bit value needs at most 5 bytes (`ceil(32/7) = 5`). The high group of `0xFFFFFFFF` is 4 bits (`0x0F`), not 7.

## Decoding rules

Walk the byte stream left to right, accumulating one integer at a time:

- `n = (n << 7) | (b & 0x7F)`
- If `b & 0x80 == 0`, that integer is complete: append `n`, reset `n` to `0`.
- If the stream ends while the last integer is still open (last consumed byte had bit 7 set, or the stream is a lone continuation byte), raise `ValueError("incomplete sequence")`.
- Do not return a partial list on error. Either the whole stream decodes or the call raises.
- Complete integers that precede an incomplete tail still do not get returned; raise instead.
- An empty input list decodes to `[]` (no incomplete sequence).
- Multiple concatenated VLQs in one list decode to multiple integers.

`0x80` alone is incomplete (continuation set, no terminator), even though the payload bits are zero.

## Algorithms

### `encode_one(n) -> list[int]`

LSB-first collect, then reverse. Handles `0` without a special case:

```
out = [n & 0x7F]
n >>= 7
while n:
    out.append((n & 0x7F) | 0x80)
    n >>= 7
out.reverse()
return out
```

Invariant: after reverse, every byte except the last has bit 7 set; the last does not.

Do not use a “keep looping until n is 0, then drop leading zeros” path that would emit `[0x80, 0x00]` for small values, or that would emit `[]` for `0`.

### `encode(numbers) -> list[int]`

```
result = []
for n in numbers:
    result.extend(encode_one(n))
return result
```

Empty `numbers` → `[]`.

### `decode(bytes_) -> list[int]`

```
numbers = []
n = 0
open_seq = False
for b in bytes_:
    n = (n << 7) | (b & 0x7F)
    if b & 0x80:
        open_seq = True
    else:
        numbers.append(n)
        n = 0
        open_seq = False
if open_seq:
    raise ValueError("incomplete sequence")
return numbers
```

`open_seq` is true iff the last consumed byte had the continuation bit. Equivalent: a flag set on every byte and cleared only on a terminator.

Do not mask `n` to 32 bits on the way. Held-out tests are expected to stay within the 32-bit contract; extra overflow checks are out of scope unless a test requires them.

## Data structures

- Inputs/outputs: plain `list[int]`.
- Per-integer encode buffer: small `list` of at most 5 ints, reversed in place.
- Decode accumulator: a single Python `int` plus a boolean “sequence open” flag.
- No classes, no `bytearray` requirement, no imports.

Keep `encode_one` as a nested function or a module-private helper. Either is fine; nested keeps the module surface equal to the stub.

## Edge cases

| Case | Behavior |
|------|----------|
| `encode([])` | `[]` |
| `encode([0])` | `[0]` |
| `encode([n])` for `n in 1..127` | `[n]` |
| `encode([0x80])` | `[0x81, 0x00]` — not `[0x80]` |
| `encode([0xFFFFFFFF])` | `[0x8F, 0xFF, 0xFF, 0xFF, 0x7F]` |
| `encode([a, b, ...])` | concat of each VLQ, no extra bytes |
| `decode([])` | `[]` |
| `decode([0])` | `[0]` |
| `decode` of any README row | inverse of encode |
| `decode` of concatenated VLQs | list of the original integers |
| `decode([0xFF])` | `ValueError("incomplete sequence")` |
| `decode([0x80])` | same error (zero payload, still open) |
| `decode([0x81])` | same error |
| `decode([complete..., 0xFF])` | same error, no partial result |
| terminator `0x00` after continuation | valid; contributes 0 to the low 7 bits |
| values with unused high groups | never encoded (no leading `0x80` padding) |

Encode and decode are inverses for every list of integers in `0 .. 0xFFFFFFFF`.

## Error contract

- Only decode raises.
- Exception type: `ValueError`.
- Message: `"incomplete sequence"` exactly. Exercism-style tests assert `err.exception.args[0]`.
- Do not raise on empty input.
- Do not raise on encode.

## What not to do

- Do not change the function names or add required extra parameters.
- Do not import third-party packages.
- Do not read/write files, use sockets, or inspect tests beyond this plan.
- Do not emit a continuation byte for single-byte values `0..127`.
- Do not treat input as `bytes`/`bytearray`; index and return lists of ints.
- Do not silently drop a trailing incomplete sequence.
- Do not special-case the README table as a lookup; implement the general 7-bit packing.

## File to edit

Only `variable_length_quantity.py`. Replace the two `pass` bodies. No tests, no extra modules.

## Verification (for the implementer)

1. `encode([0]) == [0]` (the public test).
2. Mentally or via a short local scratch script (not a test file in-repo): every README row, `0xFFFFFFFF`, multi-value concat, and the incomplete-sequence raises.
3. Round-trip: `decode(encode(ns)) == ns` for a handful of values including `0`, `127`, `128`, `0x2000`, `0xFFFFFFFF`, and a mixed list.
