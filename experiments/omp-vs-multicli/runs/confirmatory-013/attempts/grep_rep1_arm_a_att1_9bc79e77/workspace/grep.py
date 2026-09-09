def grep(pattern, flags, files):
    flagset = set(flags.split())
    ignore_case = "-i" in flagset
    invert = "-v" in flagset
    exact = "-x" in flagset
    names_only = "-l" in flagset
    number_lines = "-n" in flagset

    needle = pattern.lower() if ignore_case else pattern
    multiple_files = len(files) > 1
    matches = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.rstrip("\n")
                haystack = line.lower() if ignore_case else line
                matched = haystack == needle if exact else needle in haystack

                if invert:
                    matched = not matched
                if not matched:
                    continue

                if names_only:
                    matches.append(filename)
                    break

                parts = []
                if multiple_files:
                    parts.append(filename)
                if number_lines:
                    parts.append(str(line_number))
                parts.append(line)
                matches.append(":".join(parts))

    return "".join(match + "\n" for match in matches)
