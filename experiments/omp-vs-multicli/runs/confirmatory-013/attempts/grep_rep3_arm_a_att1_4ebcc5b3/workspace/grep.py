def _parse_flags(flags):
    tokens = set(flags.split())
    return (
        "-n" in tokens,
        "-l" in tokens,
        "-i" in tokens,
        "-v" in tokens,
        "-x" in tokens,
    )


def _matches(text, pattern, ignore_case, whole_line):
    if ignore_case:
        text = text.lower()

    if whole_line:
        return text == pattern
    return pattern in text


def grep(pattern, flags, files):
    number_lines, list_files, ignore_case, invert, whole_line = _parse_flags(flags)
    if ignore_case:
        pattern = pattern.lower()

    multiple_files = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                if raw_line.endswith("\r\n"):
                    text = raw_line[:-2]
                elif raw_line.endswith("\n"):
                    text = raw_line[:-1]
                else:
                    text = raw_line

                matched = _matches(text, pattern, ignore_case, whole_line)
                if matched == invert:
                    continue

                if list_files:
                    output.append(filename + "\n")
                    break

                prefix = ""
                if multiple_files:
                    prefix += filename + ":"
                if number_lines:
                    prefix += str(line_number) + ":"
                output.append(prefix + text + "\n")

    return "".join(output)
