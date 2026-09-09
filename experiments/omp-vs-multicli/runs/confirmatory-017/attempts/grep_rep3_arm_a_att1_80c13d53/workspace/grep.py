def _parse_flags(flags):
    tokens = flags.split() if isinstance(flags, str) else flags
    return {flag for flag in tokens if flag in {"-i", "-l", "-n", "-v", "-x"}}


def _matches(text, pattern, case_insensitive, whole_line, invert):
    if case_insensitive:
        text = text.casefold()

    if whole_line:
        matched = text == pattern
    else:
        matched = pattern in text

    return not matched if invert else matched


def _format_line(filename, lineno, text, show_file, show_lineno):
    prefix = ""
    if show_file:
        prefix += f"{filename}:"
    if show_lineno:
        prefix += f"{lineno}:"
    return f"{prefix}{text}\n"


def grep(pattern, flags, files):
    flag_set = _parse_flags(flags)
    case_insensitive = "-i" in flag_set
    files_only = "-l" in flag_set
    line_numbers = "-n" in flag_set
    invert = "-v" in flag_set
    whole_line = "-x" in flag_set
    search_pattern = pattern.casefold() if case_insensitive else pattern
    show_file = len(files) > 1
    output = []

    for filename in files:
        matched_file = False

        with open(filename) as file_handle:
            for lineno, raw_line in enumerate(file_handle, start=1):
                line = raw_line.removesuffix("\n").removesuffix("\r")
                if not _matches(
                    line,
                    search_pattern,
                    case_insensitive,
                    whole_line,
                    invert,
                ):
                    continue

                matched_file = True
                if files_only:
                    break

                output.append(
                    _format_line(
                        filename,
                        lineno,
                        line,
                        show_file,
                        line_numbers,
                    )
                )

        if files_only and matched_file:
            output.append(f"{filename}\n")

    return "".join(output)


