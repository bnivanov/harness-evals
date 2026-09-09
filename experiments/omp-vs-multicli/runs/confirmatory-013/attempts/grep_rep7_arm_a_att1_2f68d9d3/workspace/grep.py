def _parse_flags(flags):
    options = set(flags.split()) if isinstance(flags, str) else set(flags)
    return (
        "-n" in options,
        "-l" in options,
        "-i" in options,
        "-v" in options,
        "-x" in options,
    )


def _matches(text, pattern, exact, invert):
    if exact:
        matched = text == pattern
    else:
        matched = pattern in text

    return not matched if invert else matched


def _format_line(filename, lineno, raw_line, multiple_files, number):
    line = raw_line if raw_line.endswith("\n") else raw_line + "\n"
    prefix = ""

    if multiple_files:
        prefix += f"{filename}:"
    if number:
        prefix += f"{lineno}:"

    return prefix + line


def grep(pattern, flags, files):
    number, list_files, insensitive, invert, exact = _parse_flags(flags)
    file_list = list(files)
    multiple_files = len(file_list) > 1

    if insensitive:
        pattern = pattern.casefold()

    output = []

    for filename in file_list:
        with open(filename) as file:
            for lineno, raw_line in enumerate(file, start=1):
                text = raw_line.rstrip("\r\n")
                if insensitive:
                    text = text.casefold()

                if not _matches(text, pattern, exact, invert):
                    continue

                if list_files:
                    output.append(filename + "\n")
                    break

                output.append(
                    _format_line(
                        filename,
                        lineno,
                        raw_line,
                        multiple_files,
                        number,
                    )
                )

    return "".join(output)




