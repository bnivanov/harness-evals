def _parse_flags(flags):
    tokens = flags.split()
    short_flags = set()
    known_flags = {"n", "l", "i", "v", "x"}

    for token in tokens:
        if token.startswith("-") and not token.startswith("--"):
            candidate = token[1:]
            if set(candidate).issubset(known_flags):
                short_flags.update(candidate)

    return {
        "line_numbers": "n" in short_flags,
        "filenames_only": "l" in short_flags,
        "ignore_case": "i" in short_flags,
        "invert": "v" in short_flags,
        "entire_line": "x" in short_flags,
    }


def _line_body(raw_line):
    if raw_line.endswith("\r\n"):
        return raw_line[:-2]
    if raw_line.endswith("\n"):
        return raw_line[:-1]
    return raw_line


def _line_matches(body, pattern, flags):
    if flags["ignore_case"]:
        body = body.lower()

    if flags["entire_line"]:
        matched = body == pattern
    else:
        matched = pattern in body

    return not matched if flags["invert"] else matched


def grep(pattern, flags, files):
    parsed_flags = _parse_flags(flags)
    multiple_files = len(files) > 1
    search_pattern = pattern.lower() if parsed_flags["ignore_case"] else pattern
    results = []

    for filename in files:
        with open(filename) as file_handle:
            for line_number, raw_line in enumerate(file_handle, start=1):
                body = _line_body(raw_line)
                if not _line_matches(body, search_pattern, parsed_flags):
                    continue

                if parsed_flags["filenames_only"]:
                    results.append(filename + "\n")
                    break

                prefix = []
                if multiple_files:
                    prefix.append(filename)
                if parsed_flags["line_numbers"]:
                    prefix.append(str(line_number))

                if prefix:
                    results.append(":".join(prefix) + ":" + body + "\n")
                else:
                    results.append(body + "\n")

    return "".join(results)
