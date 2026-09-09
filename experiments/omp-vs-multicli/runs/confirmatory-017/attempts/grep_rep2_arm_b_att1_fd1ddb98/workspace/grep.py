def grep(pattern, flags, files):
    """Return the lines in *files* selected by the simplified grep flags."""
    files = list(files)
    valid_flags = {"n", "l", "i", "v", "x"}
    options = set()

    for token in (flags or "").split():
        if token.startswith("-") and not token.startswith("--"):
            for flag in token[1:]:
                if flag in valid_flags:
                    options.add(flag)

    case_insensitive = "i" in options
    invert = "v" in options
    entire_line = "x" in options
    names_only = "l" in options
    show_number = "n" in options
    show_filename = len(files) > 1

    needle = pattern.casefold() if case_insensitive else pattern
    output = []

    for filename in files:
        with open(filename) as file_handle:
            for line_number, raw_line in enumerate(file_handle, start=1):
                text = raw_line.removesuffix("\r\n").removesuffix("\n").removesuffix("\r")

                haystack = text.casefold() if case_insensitive else text
                matched = haystack == needle if entire_line else needle in haystack
                if invert:
                    matched = not matched

                if not matched:
                    continue

                if names_only:
                    output.append(filename + "\n")
                    break

                prefix = ""
                if show_filename:
                    prefix += filename + ":"
                if show_number:
                    prefix += str(line_number) + ":"
                output.append(prefix + text + "\n")

    return "".join(output)
