from dataclasses import dataclass


@dataclass(frozen=True)
class Flags:
    line_number: bool
    filename_only: bool
    ignore_case: bool
    invert: bool
    exact_line: bool


def parse_flags(flags):
    """Return the supported options found in a string or iterable of flags."""
    values = flags.split() if isinstance(flags, str) else flags
    tokens = set()
    supported = {"-n", "-l", "-i", "-v", "-x"}
    supported_short = {flag[1:] for flag in supported}

    for value in values:
        if value in supported:
            tokens.add(value)
            continue

        cluster = value[1:]
        if (
            value.startswith("-")
            and not value.startswith("--")
            and cluster
            and set(cluster) <= supported_short
        ):
            tokens.update(
                f"-{flag}" for flag in value[1:] if f"-{flag}" in supported
            )

    return Flags(
        line_number="-n" in tokens,
        filename_only="-l" in tokens,
        ignore_case="-i" in tokens,
        invert="-v" in tokens,
        exact_line="-x" in tokens,
    )


def normalize_line(line):
    """Remove line terminators for matching while preserving other whitespace."""
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def line_matches(pattern, text, flags):
    """Apply positive matching options, then invert the result if requested."""
    if flags.ignore_case:
        text = text.casefold()

    if flags.exact_line:
        matched = text == pattern
    else:
        matched = pattern in text

    return not matched if flags.invert else matched


def format_line(filename, line_number, raw, flags, include_filename):
    """Format a selected line, retaining its original body and terminator."""
    prefix = ""
    if include_filename:
        prefix += f"{filename}:"
    if flags.line_number:
        prefix += f"{line_number}:"

    if raw.endswith("\n"):
        return prefix + raw
    return prefix + raw + "\n"


def search_file(filename, pattern, flags, include_filename):
    """Yield output records for one file, stopping early for ``-l``."""
    effective_pattern = pattern.casefold() if flags.ignore_case else pattern
    with open(filename) as file_handle:
        for line_number, raw in enumerate(file_handle, start=1):
            text = normalize_line(raw)
            if not line_matches(effective_pattern, text, flags):
                continue

            if flags.filename_only:
                yield f"{filename}\n"
                return

            yield format_line(filename, line_number, raw, flags, include_filename)


def grep(pattern, flags, files):
    parsed_flags = parse_flags(flags)
    include_filename = len(files) > 1

    return "".join(
        record
        for filename in files
        for record in search_file(filename, pattern, parsed_flags, include_filename)
    )
