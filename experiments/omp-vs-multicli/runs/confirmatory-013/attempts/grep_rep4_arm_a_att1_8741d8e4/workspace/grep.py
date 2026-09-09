def _without_line_ending(line):
    if line.endswith("\n"):
        line = line[:-1]
    if line.endswith("\r"):
        line = line[:-1]
    return line


def grep(pattern, flags, files):
    flag_set = set(flags.split() if isinstance(flags, str) else flags)
    numbered = "-n" in flag_set
    list_files = "-l" in flag_set
    ignore_case = "-i" in flag_set
    invert = "-v" in flag_set
    whole_line = "-x" in flag_set

    needle = pattern.lower() if ignore_case else pattern
    multiple_files = len(files) > 1
    matches = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = _without_line_ending(raw_line)
                haystack = line.lower() if ignore_case else line
                matched = (
                    haystack == needle
                    if whole_line
                    else needle in haystack
                )
                if invert:
                    matched = not matched
                if not matched:
                    continue

                if list_files:
                    matches.append(filename)
                    break

                fields = []
                if multiple_files:
                    fields.append(filename)
                if numbered:
                    fields.append(str(line_number))
                fields.append(line)
                matches.append(":".join(fields))

    return "".join(match + "\n" for match in matches)
