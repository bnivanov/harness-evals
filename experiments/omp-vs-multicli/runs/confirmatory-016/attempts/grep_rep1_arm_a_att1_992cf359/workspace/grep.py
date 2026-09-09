def _line_body(raw_line):
    if raw_line.endswith("\r\n"):
        return raw_line[:-2]
    if raw_line.endswith(("\n", "\r")):
        return raw_line[:-1]
    return raw_line


def _matches(body, pattern, ignore_case, whole_line, invert):
    if ignore_case:
        body = body.lower()

    if whole_line:
        matched = body == pattern
    else:
        matched = pattern in body

    return not matched if invert else matched


def _format_line(filename, line_number, body, multiple_files, with_numbers):
    prefix = []
    if multiple_files:
        prefix.append(filename)
    if with_numbers:
        prefix.append(str(line_number))

    if prefix:
        return ":".join(prefix) + ":" + body + "\n"
    return body + "\n"


def grep(pattern, flags, files):
    active_flags = set(flags.split() if isinstance(flags, str) else flags)
    ignore_case = "-i" in active_flags
    invert = "-v" in active_flags
    whole_line = "-x" in active_flags
    list_files = "-l" in active_flags
    with_numbers = "-n" in active_flags
    multiple_files = len(files) > 1
    target_pattern = pattern.lower() if ignore_case else pattern
    result = []

    for filename in files:
        with open(filename) as input_file:
            if list_files:
                for raw_line in input_file:
                    body = _line_body(raw_line)
                    if _matches(body, target_pattern, ignore_case, whole_line, invert):
                        result.append(filename + "\n")
                        break
                continue

            for line_number, raw_line in enumerate(input_file, start=1):
                body = _line_body(raw_line)
                if _matches(body, target_pattern, ignore_case, whole_line, invert):
                    result.append(
                        _format_line(
                            filename,
                            line_number,
                            body,
                            multiple_files,
                            with_numbers,
                        )
                    )

    return "".join(result)
