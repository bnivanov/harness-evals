def grep(pattern, flags, files):
    flagset = set(flags.split())
    ignore_case = "-i" in flagset
    invert = "-v" in flagset
    exact_line = "-x" in flagset
    names_only = "-l" in flagset
    number_lines = "-n" in flagset
    multiple_files = len(files) > 1

    needle = pattern.lower() if ignore_case else pattern
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.rstrip("\n")
                haystack = line.lower() if ignore_case else line
                matched = (
                    haystack == needle
                    if exact_line
                    else needle in haystack
                )

                if invert:
                    matched = not matched
                if not matched:
                    continue

                if names_only:
                    output.append(filename + "\n")
                    break

                prefix = ""
                if multiple_files:
                    prefix += filename + ":"
                if number_lines:
                    prefix += str(line_number) + ":"

                if raw_line.endswith("\n"):
                    output.append(prefix + raw_line)
                else:
                    output.append(prefix + raw_line + "\n")

    return "".join(output)
