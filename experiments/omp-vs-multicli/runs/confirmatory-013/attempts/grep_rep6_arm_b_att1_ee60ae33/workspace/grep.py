def grep(pattern, flags, files):
    flag_set = set()
    for token in (flags or "").split():
        if token.startswith("-"):
            flag_set.update(token[1:])

    list_only = "l" in flag_set
    invert = "v" in flag_set
    entire_line = "x" in flag_set
    ignore_case = "i" in flag_set
    show_line_numbers = "n" in flag_set
    multi_file = len(files) > 1

    needle = pattern.casefold() if ignore_case else pattern
    results = []

    for filename in files:
        with open(filename) as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.rstrip("\r\n")
                haystack = text.casefold() if ignore_case else text

                if entire_line:
                    matched = haystack == needle
                else:
                    matched = needle in haystack

                if invert:
                    matched = not matched

                if not matched:
                    continue

                if list_only:
                    results.append(filename + "\n")
                    break

                body = text + "\n"
                if multi_file and show_line_numbers:
                    results.append(f"{filename}:{line_no}:{body}")
                elif multi_file:
                    results.append(f"{filename}:{body}")
                elif show_line_numbers:
                    results.append(f"{line_no}:{body}")
                else:
                    results.append(body)

    return "".join(results)
