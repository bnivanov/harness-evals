def grep(pattern, flags, files):
    supported_flags = frozenset("nlivx")
    flag_chars = {
        character
        for token in flags.split()
        if token.startswith("-") and not token.startswith("--")
        for character in token[1:]
        if character in supported_flags
    }
    want_line_numbers = "n" in flag_chars
    list_names_only = "l" in flag_chars
    ignore_case = "i" in flag_chars
    invert = "v" in flag_chars
    whole_line = "x" in flag_chars

    if ignore_case:
        needle = pattern.casefold()
    else:
        needle = pattern

    multiple_files = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                if raw_line.endswith("\r\n"):
                    text = raw_line[:-2]
                elif raw_line.endswith(("\n", "\r")):
                    text = raw_line[:-1]
                else:
                    text = raw_line

                haystack = text.casefold() if ignore_case else text
                if whole_line:
                    raw_match = haystack == needle
                else:
                    raw_match = needle in haystack

                selected = not raw_match if invert else raw_match
                if not selected:
                    continue

                if list_names_only:
                    output.append(filename + "\n")
                    break

                prefix = filename + ":" if multiple_files else ""
                if want_line_numbers:
                    prefix += str(line_number) + ":"

                output.append(prefix + text + "\n")

    return "".join(output)
