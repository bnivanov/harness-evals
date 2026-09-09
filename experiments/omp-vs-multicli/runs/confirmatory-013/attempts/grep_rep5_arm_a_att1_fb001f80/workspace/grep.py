def grep(pattern, flags, files):
    flag_set = set(flags.split())
    ignore_case = "-i" in flag_set
    needle = pattern.lower() if ignore_case else pattern
    include_line_number = "-n" in flag_set
    list_files = "-l" in flag_set
    invert = "-v" in flag_set
    whole_line = "-x" in flag_set
    multiple_files = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.rstrip("\n")
                haystack = line.lower() if ignore_case else line
                matches = (
                    haystack == needle
                    if whole_line
                    else needle in haystack
                )
                if invert:
                    matches = not matches
                if not matches:
                    continue

                if list_files:
                    output.append(filename + "\n")
                    break

                prefix = ""
                if multiple_files:
                    prefix += filename + ":"
                if include_line_number:
                    prefix += f"{line_number}:"
                output.append(prefix + line + "\n")

    return "".join(output)
