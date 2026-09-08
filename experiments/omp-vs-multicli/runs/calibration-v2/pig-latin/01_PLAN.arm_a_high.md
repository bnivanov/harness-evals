# Pig Latin — Implementation Guide

## Goal

Implement `translate(text)` in `pig_latin.py` so English text becomes Pig Latin per the four README rules. Public test: `translate("apple") == "appleay"`. Hidden tests will cover remaining rules, consonant clusters, `qu`/`y` specials, and multi-word phrases.

Do not change tests. Keep the public function name `translate`.

## Contract

```python
def translate(text):
    """Translate English `text` to Pig Latin. Return a string."""
```

- Input: a string of one or more lowercase English words, space-separated.
- Output: the same words, each transformed, joined by a single space.
- Alphabet: `a`–`z` only in expected inputs. No punctuation, mixed case, or hyphens in the spec.
- Vowels: `a e i o u`. Consonants: the other 21 letters. `y` is a consonant at the start of a word and a vowel after one or more consonants.

## Architecture

Two functions, no classes, no I/O, no extra modules required.

| Symbol | Role |
|---|---|
| `translate(text)` | Public. Split on whitespace, map each word, join with `" "`. |
| `_translate_word(word)` | Private. Apply Rule 1–4 to one word and append `"ay"`. |

Optional tiny helpers (keep them local if used):

- `_VOWELS = frozenset("aeiou")` — membership test, not a string scan.
- `_starts_with_vowel_sound(word)` — Rule 1 predicate.

Do not import `re` unless the cluster scan is clearly cleaner as one regex. A linear index walk is the boring default: O(n) per word, no allocation beyond the result string, no regex engine.

## Algorithm (per word)

Apply rules in this order. First match wins.

### Rule 1 — vowel sound

If the word begins with a vowel, **or** begins with `"xr"`, **or** begins with `"yt"`:

```
word + "ay"
```

Examples: `"apple"` → `"appleay"`; `"xray"` → `"xrayay"`; `"yttria"` → `"yttriaay"`; `"equal"` → `"equalay"` (leading vowel beats an interior `"qu"`).

`"y"` alone is **not** Rule 1 (`y` is not a vowel; `"yt"` is the only `y…` prefix that is). `"xenon"` is **not** Rule 1 (`x` without following `r`).

### Otherwise — find the split index `i`

`i` is the length of the leading cluster that moves to the end. Scan `word` from index `0`:

1. If the current char is a vowel (`a e i o u`), **stop**. Do not include it.
2. If the current char is `y` **and** the index is `> 0`, **stop**. `y` is a vowel here (Rule 4). Do not include it.
3. If the current char is `q` **and** the next char is `u`, include both (`i += 2`) and **stop**. That is Rule 3: consonants (already consumed) + `"qu"` are the whole moved piece. Do not consume letters after `"qu"`.
4. Otherwise the char is a consonant. Include it (`i += 1`) and continue.

Then:

```
word[i:] + word[:i] + "ay"
```

This one scan covers Rules 2, 3, and 4:

| Rule | Cluster | Example |
|---|---|---|
| 2 | one or more consonants, stop at first vowel | `"pig"` `i=1` → `"igpay"`; `"chair"` `i=2` → `"airchay"`; `"thrush"` `i=3` → `"ushthray"` |
| 3 | consonants* + `"qu"` | `"quick"` `i=2` → `"ickquay"`; `"square"` `i=3` → `"aresquay"` |
| 4 | consonants+ then `y` as vowel | `"my"` `i=1` → `"ymay"`; `"rhythm"` `i=2` → `"ythmrhay"` |

Rule 2 also covers a leading `y` that is **not** `"yt"`: `"yellow"` → `y` at index 0 is a consonant, `e` stops → `"ellowyay"`.

If the scan runs off the end (`i == len(word)`), the whole word is consonants: `"" + word + "ay"`. That is fine (`"y"` → `"yay"`). Do not special-case it.

## Phrase handling

```python
return " ".join(_translate_word(w) for w in text.split())
```

- `str.split()` with no args: splits on any whitespace, drops extra spaces, yields no empty tokens.
- Empty `text`: `"".split()` is `[]` → `""`. Harmless.
- Preserve word order. Do not mutate in place.

Do not use `split(" ")` (would keep empty tokens on double spaces). Canonical cases use single spaces; `split()` is still the right API.

## Data structures

- `text` / `word`: `str`. Words are short; slicing is the result, not a buffer.
- `_VOWELS`: `frozenset` of five chars. Constant, module-level.
- Split index: `int`. No list of consonants to copy.
- No dicts, no sets of words, no recursion.

Do not allocate a character list unless you also join it; two slices + `"ay"` is enough.

## Edge cases (must handle)

| Case | Expected behavior |
|---|---|
| Leading vowel `a e i o u` | Rule 1, append `"ay"` only |
| `"xr…"` / `"yt…"` | Rule 1 even though `x`/`y` are consonants |
| `"x…"` not `"xr"` (e.g. `"xenon"`) | Rule 2, move `x` |
| `"y…"` not `"yt"` (e.g. `"yellow"`) | Rule 2, move leading `y` |
| Single consonant + vowel | Rule 2 |
| Consonant cluster (`ch`, `th`, `thr`, `sch`, …) | Rule 2, move the whole cluster up to the first vowel |
| `"qu…"` | Rule 3, move `"qu"` |
| Consonants + `"qu"` (e.g. `"square"`) | Rule 3, move prefix + `"qu"` |
| Vowel then `"qu"` (e.g. `"equal"`) | Rule 1, do **not** move `"qu"` |
| `"q"` not followed by `"u"` | Treat `q` as a normal consonant (Rule 2) |
| Consonants then `"y"` (`"my"`, `"rhythm"`) | Rule 4, keep `"y"` at the front |
| `"y"` as the only letter | Rule 2, `"yay"` |
| `"qu"` as the whole word | Rule 3, `"quay"` |
| Multi-word phrase | Translate each word independently; join with one space |
| Word with no vowels after a cluster | Move the cluster (possibly the whole word), then `"ay"` |

Out of spec (do not add code for these unless a test forces it): uppercase, punctuation, empty tokens, non-ASCII, hyphens. Inputs are lowercase `[a-z]+` words.

## Rule interactions (do not get these wrong)

1. **Order:** Rule 1 before the cluster scan. `"yttria"` must not be treated as Rule 4 (`y` + rest).
2. **`y` position:** index 0 → consonant; index > 0 in a consonant run → vowel, split **before** it.
3. **`qu` is atomic:** when `q` is followed by `u`, consume both and stop. Do not treat that `u` as a Rule 1 vowel. Do not keep scanning after `"qu"`.
4. **Interior `"qu"`:** only a *leading* consonants*+`qu` cluster moves. `"equal"` stays `"equalay"`.
5. **`"xr"` / `"yt"` are prefixes, not letters:** `"xray"` is Rule 1, not “move `x`”.

## Suggested implementation sketch

```python
_VOWELS = frozenset("aeiou")

def translate(text):
    return " ".join(_translate_word(word) for word in text.split())

def _translate_word(word):
    if _rule1(word):
        return word + "ay"
    i = _cluster_len(word)
    return word[i:] + word[:i] + "ay"

def _rule1(word):
    return word[0] in _VOWELS or word.startswith(("xr", "yt"))

def _cluster_len(word):
    i = 0
    n = len(word)
    while i < n:
        ch = word[i]
        if ch in _VOWELS:
            break
        if ch == "y" and i > 0:
            break
        if ch == "q" and i + 1 < n and word[i + 1] == "u":
            i += 2
            break
        i += 1
    return i
```

`_rule1` assumes `word` is non-empty. `translate` only feeds tokens from `split()`, so empty words do not appear. Do not add a guard unless you keep a path that can pass `""`.

Invariants:

- `_cluster_len` returns `0..len(word)`.
- Rule 1 never calls `_cluster_len`.
- Result always ends with `"ay"`.
- `len(result) == len(word) + 2` for a single word.

## What not to do

- Do not edit `public_test.py` or add test files.
- Do not download Exercism canonical data or look at other solutions.
- Do not handle capitalization or punctuation “while you’re at it”.
- Do not use a chain of overlapping regexes that re-scan the word four times unless it is the entire implementation and still first-match-wins in the order above.
- Do not treat `y` as always a vowel or always a consonant.
- Do not move `"qu"` when it is not at the front of the remaining word after a consonant prefix (i.e. not after Rule 1 already matched).

## Verification (implementer)

After coding `pig_latin.py` only:

1. Targeted: `python -m unittest public_test.py` — `test_word_beginning_with_a` must pass.
2. Smoke the README examples in a one-off interpreter session (not a checked-in test file):

   - Rule 1: `apple` → `appleay`, `xray` → `xrayay`, `yttria` → `yttriaay`
   - Rule 2: `pig` → `igpay`, `chair` → `airchay`, `thrush` → `ushthray`
   - Rule 3: `quick` → `ickquay`, `square` → `aresquay`
   - Rule 4: `my` → `ymay`, `rhythm` → `ythmrhay`
   - Phrase: two or more of the above joined by spaces, each word transformed independently

3. Do not add a permanent test file. Do not touch the stub’s caller surface beyond filling in `translate` and helpers in `pig_latin.py`.
