def grep(pattern, flags, files):
    tokens = flags.split()
    flag_chars = {
        character
        for token in tokens
        if token.startswith("-")
        for character in token[1:]
    }
    show_line_numbers = "-n" in tokens or "n" in flag_chars
    only_filenames = "-l" in tokens or "l" in flag_chars
    ignore_case = "-i" in tokens or "i" in flag_chars
    invert = "-v" in tokens or "v" in flag_chars
    entire_line = "-x" in tokens or "x" in flag_chars

    needle = pattern.casefold() if ignore_case else pattern
    multi_file = len(files) > 1
    output = []

    for filename in files:
        with open(filename) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.removesuffix("\r\n").removesuffix("\n")
                haystack = line.casefold() if ignore_case else line

                matched = (
                    haystack == needle
                    if entire_line
                    else needle in haystack
                )
                if invert:
                    matched = not matched

                if not matched:
                    continue

                if only_filenames:
                    output.append(filename + "\n")
                    break

                parts = []
                if multi_file:
                    parts.append(filename)
                if show_line_numbers:
                    parts.append(str(line_number))

                if parts:
                    output.append(":".join(parts) + ":" + line + "\n")
                else:
                    output.append(line + "\n")

    return "".join(output)
