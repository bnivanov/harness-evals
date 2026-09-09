def _parse_flags(flags):
    if isinstance(flags, str):
        return set(flags.split())
    return set(flags)


def _matches(line, pattern, insensitive, exact):
    if insensitive:
        line = line.lower()

    if exact:
        return line == pattern
    return pattern in line


def grep(pattern, flags, files):
    flagset = _parse_flags(flags)
    insensitive = "-i" in flagset
    exact = "-x" in flagset
    inverted = "-v" in flagset
    line_numbers = "-n" in flagset
    filenames_only = "-l" in flagset
    multiple_files = len(files) > 1
    if insensitive:
        pattern = pattern.lower()
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.rstrip("\r\n")
                matches = _matches(line, pattern, insensitive, exact)
                if inverted:
                    matches = not matches
                if not matches:
                    continue

                if filenames_only:
                    output.append(filename + "\n")
                    break

                fields = []
                if multiple_files:
                    fields.append(filename)
                if line_numbers:
                    fields.append(str(line_number))
                fields.append(line)
                output.append(":".join(fields) + "\n")

    return "".join(output)
