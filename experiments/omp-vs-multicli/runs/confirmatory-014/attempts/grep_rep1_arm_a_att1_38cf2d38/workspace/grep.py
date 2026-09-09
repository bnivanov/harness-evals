def grep(pattern, flags, files):
    options = set(flags.split())
    ignore_case = "-i" in options
    invert = "-v" in options
    whole_line = "-x" in options
    names_only = "-l" in options
    line_numbers = "-n" in options
    multiple_files = len(files) > 1
    needle = pattern.lower() if ignore_case else pattern
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, line in enumerate(file, start=1):
                if line.endswith("\r\n"):
                    content = line[:-2]
                elif line.endswith("\n"):
                    content = line[:-1]
                else:
                    content = line
                haystack = content.lower() if ignore_case else content
                matched = (
                    haystack == needle
                    if whole_line
                    else needle in haystack
                )
                if invert:
                    matched = not matched
                if not matched:
                    continue

                if names_only:
                    output.append(filename + "\n")
                    break

                prefix = f"{filename}:" if multiple_files else ""
                if line_numbers:
                    prefix += f"{line_number}:"
                output.append(prefix + (line if line.endswith("\n") else line + "\n"))

    return "".join(output)
