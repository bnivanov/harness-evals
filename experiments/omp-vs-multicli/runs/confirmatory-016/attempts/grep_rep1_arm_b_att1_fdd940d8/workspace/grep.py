from dataclasses import dataclass
from typing import Iterable, Union


@dataclass(frozen=True)
class _Flags:
    line_numbers: bool
    filenames_only: bool
    ignore_case: bool
    invert: bool
    entire_line: bool


def _parse_flags(flags: Union[str, Iterable[str]]) -> _Flags:
    """Parse string or iterable grep flags into a fixed set of booleans."""
    tokens = set(flags.split() if isinstance(flags, str) else flags)
    short_options = frozenset("nlivx")
    for token in tuple(tokens):
        if (
            len(token) > 2
            and token.startswith("-")
            and not token.startswith("--")
            and set(token[1:]).issubset(short_options)
        ):
            tokens.update(f"-{option}" for option in token[1:])

    return _Flags(
        line_numbers="-n" in tokens,
        filenames_only="-l" in tokens,
        ignore_case="-i" in tokens,
        invert="-v" in tokens,
        entire_line="-x" in tokens,
    )


def _strip_terminator(raw: str) -> str:
    """Remove one line-feed and the carriage return preceding it, if present."""
    if raw.endswith("\n"):
        raw = raw[:-1]
    if raw.endswith("\r"):
        raw = raw[:-1]
    return raw


def _line_selected(line: str, needle: str, flags: _Flags) -> bool:
    """Return whether a logical line is selected by the matching flags."""
    haystack = line.lower() if flags.ignore_case else line

    if flags.entire_line:
        selected = haystack == needle
    else:
        selected = needle in haystack

    return not selected if flags.invert else selected


def grep(pattern, flags, files):
    """Return matching lines, or matching file names, for the supplied files."""
    parsed_flags = _parse_flags(flags)
    needle = pattern.lower() if parsed_flags.ignore_case else pattern
    show_filename = len(files) > 1
    records = []

    for filename in files:
        filename_prefix = f"{filename}:" if show_filename else ""
        with open(filename, encoding="utf-8") as file_handle:
            for line_number, raw in enumerate(file_handle, start=1):
                line = _strip_terminator(raw)
                if not _line_selected(line, needle, parsed_flags):
                    continue

                if parsed_flags.filenames_only:
                    records.append(filename + "\n")
                    break

                number_prefix = f"{line_number}:" if parsed_flags.line_numbers else ""
                records.append(f"{filename_prefix}{number_prefix}{line}\n")

    return "".join(records)
