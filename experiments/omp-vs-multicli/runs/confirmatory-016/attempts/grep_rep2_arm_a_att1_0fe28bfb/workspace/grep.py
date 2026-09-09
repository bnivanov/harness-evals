def grep(pattern, flags, files):
    flag_set = set(flags.split())
    show_line_numbers = "-n" in flag_set
    list_files = "-l" in flag_set
    ignore_case = "-i" in flag_set
    invert_match = "-v" in flag_set
    match_entire_line = "-x" in flag_set

    needle = pattern.lower() if ignore_case else pattern
    multiple_files = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, line in enumerate(file, start=1):
                line_body = line[:-1] if line.endswith("\n") else line
                haystack = line_body.lower() if ignore_case else line_body
                matches = (
                    haystack == needle
                    if match_entire_line
                    else needle in haystack
                )
                if invert_match:
                    matches = not matches

                if not matches:
                    continue

                if list_files:
                    output.append(filename + "\n")
                    break

                prefix = filename + ":" if multiple_files else ""
                if show_line_numbers:
                    prefix += f"{line_number}:"
                output.append(prefix + line)

    return "".join(output)
