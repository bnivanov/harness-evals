def grep(pattern, flags, files):
    """Return the lines selected by a fixed-string grep search."""
    flag_set = set(flags.split())
    ignore_case = "-i" in flag_set
    invert = "-v" in flag_set
    exact_line = "-x" in flag_set
    show_number = "-n" in flag_set
    names_only = "-l" in flag_set
    multiple_files = len(files) > 1

    needle = pattern.lower() if ignore_case else pattern
    output = []

    for filename in files:
        with open(filename) as file:
            if names_only:
                for line in file:
                    content = line.rstrip("\r\n")
                    haystack = content.lower() if ignore_case else content
                    if (haystack == needle if exact_line else needle in haystack) != invert:
                        output.append(filename + "\n")
                        break
                continue

            for line_number, line in enumerate(file, start=1):
                content = line.rstrip("\r\n")
                haystack = content.lower() if ignore_case else content
                matched = haystack == needle if exact_line else needle in haystack
                if matched == invert:
                    continue

                prefix = []
                if multiple_files:
                    prefix.append(filename)
                if show_number:
                    prefix.append(str(line_number))
                if prefix:
                    output.append(":".join(prefix) + ":" + content + "\n")
                else:
                    output.append(content + "\n")

    return "".join(output)
