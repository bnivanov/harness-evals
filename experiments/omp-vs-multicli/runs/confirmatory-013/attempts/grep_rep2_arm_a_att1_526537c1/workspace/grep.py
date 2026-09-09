def _parse_flags(flags):
    if not flags:
        return set()

    tokens = flags.split() if isinstance(flags, str) else flags
    recognized = {"n", "l", "i", "v", "x"}
    options = set()

    for token in tokens:
        if token.startswith("-"):
            token = token[1:]
        options.update(character for character in token if character in recognized)

    return options


def _is_match(line, pattern, options, normalized_pattern=None):
    if "i" in options:
        line = line.lower()
        pattern = (
            pattern.lower()
            if normalized_pattern is None
            else normalized_pattern
        )

    if "x" in options:
        return line == pattern
    return pattern in line


def grep(pattern, flags, files):
    options = _parse_flags(flags)
    normalized_pattern = pattern.lower() if "i" in options else pattern
    include_filenames = len(files) > 1
    results = []

    for filename in files:
        with open(filename) as file:
            for line_number, line in enumerate(file, start=1):
                if line.endswith("\n"):
                    line = line[:-1]
                if line.endswith("\r"):
                    line = line[:-1]

                matches = _is_match(
                    line, pattern, options, normalized_pattern
                )
                if "v" in options:
                    matches = not matches
                if not matches:
                    continue

                if "l" in options:
                    results.append(str(filename))
                    break

                fields = []
                if include_filenames:
                    fields.append(str(filename))
                if "n" in options:
                    fields.append(str(line_number))
                fields.append(line)
                results.append(":".join(fields))

    return "".join(result + "\n" for result in results)


