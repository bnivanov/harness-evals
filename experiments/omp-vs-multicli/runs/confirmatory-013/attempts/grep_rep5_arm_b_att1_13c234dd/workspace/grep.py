def grep(pattern, flags, files):
    flag_list = flags.split() if isinstance(flags, str) else list(flags)
    supported_flags = {"-i", "-v", "-x", "-n", "-l"}
    parsed_flags = set()
    for flag in flag_list:
        if not isinstance(flag, str):
            continue
        if flag in supported_flags:
            parsed_flags.add(flag)
        elif (
            len(flag) > 2
            and flag.startswith("-")
            and all("-" + character in supported_flags for character in flag[1:])
        ):
            parsed_flags.update("-" + character for character in flag[1:])

    ignore_case = "-i" in parsed_flags
    invert = "-v" in parsed_flags
    entire_line = "-x" in parsed_flags
    show_number = "-n" in parsed_flags
    files_only = "-l" in parsed_flags
    show_file = len(files) > 1

    needle = pattern.casefold() if ignore_case else pattern
    records = []

    for filename in files:
        with open(filename, encoding="utf-8") as file_handle:
            for line_number, raw_line in enumerate(file_handle, start=1):
                text = raw_line.removesuffix("\r\n").removesuffix("\n")
                haystack = text.casefold() if ignore_case else text
                matched = (
                    haystack == needle
                    if entire_line
                    else needle in haystack
                )

                if invert:
                    matched = not matched
                if not matched:
                    continue

                if files_only:
                    records.append(filename + "\n")
                    break

                prefix = []
                if show_file:
                    prefix.append(filename)
                if show_number:
                    prefix.append(str(line_number))

                if prefix:
                    records.append(":".join(prefix) + ":" + text + "\n")
                else:
                    records.append(text + "\n")

    return "".join(records)
