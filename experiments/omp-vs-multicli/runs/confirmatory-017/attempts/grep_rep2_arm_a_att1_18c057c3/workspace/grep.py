def grep(pattern, flags, files):
    flag_set = set(flags.split())
    numbered = "-n" in flag_set
    files_only = "-l" in flag_set
    insensitive = "-i" in flag_set
    invert = "-v" in flag_set
    exact = "-x" in flag_set
    multi = len(files) > 1
    search_pattern = pattern.lower() if insensitive else pattern
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.rstrip("\r\n")
                haystack = line.lower() if insensitive else line

                matches = haystack == search_pattern if exact else search_pattern in haystack
                if invert:
                    matches = not matches
                if not matches:
                    continue

                if files_only:
                    output.append(f"{filename}\n")
                    break

                if multi and numbered:
                    output.append(f"{filename}:{line_number}:{line}\n")
                elif multi:
                    output.append(f"{filename}:{line}\n")
                elif numbered:
                    output.append(f"{line_number}:{line}\n")
                else:
                    output.append(f"{line}\n")

    return "".join(output)
