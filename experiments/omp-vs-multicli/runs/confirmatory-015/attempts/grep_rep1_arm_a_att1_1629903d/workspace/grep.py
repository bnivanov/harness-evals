def _line_selected(line, search_pattern, ignore_case, invert, exact):
    text = line.rstrip("\r\n")
    if ignore_case:
        text = text.lower()

    if exact:
        matched = text == search_pattern
    else:
        matched = search_pattern in text

    return not matched if invert else matched


def grep(pattern, flags, files):
    flag_set = set(flags.split())
    line_numbers = "-n" in flag_set
    names_only = "-l" in flag_set
    ignore_case = "-i" in flag_set
    invert = "-v" in flag_set
    exact = "-x" in flag_set
    search_pattern = pattern.lower() if ignore_case else pattern
    multiple_files = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, line in enumerate(file, start=1):
                if not _line_selected(
                    line, search_pattern, ignore_case, invert, exact
                ):
                    continue

                if names_only:
                    output.append(filename + "\n")
                    break

                prefix = ""
                if multiple_files:
                    prefix += filename + ":"
                if line_numbers:
                    prefix += str(line_number) + ":"

                if not line.endswith("\n"):
                    line += "\n"
                output.append(prefix + line)

    return "".join(output)
