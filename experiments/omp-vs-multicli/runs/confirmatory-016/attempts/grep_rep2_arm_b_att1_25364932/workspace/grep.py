def grep(pattern, flags, files):
    flag_tokens = set(flags.split())
    want_line_numbers = "-n" in flag_tokens
    want_filenames_only = "-l" in flag_tokens
    ignore_case = "-i" in flag_tokens
    invert = "-v" in flag_tokens
    entire_line = "-x" in flag_tokens

    needle = pattern.lower() if ignore_case else pattern
    multiple_files = len(files) > 1
    parts = []

    for filename in files:
        with open(filename) as fh:
            for line_no, line in enumerate(fh, start=1):
                text = line[:-1] if line.endswith("\n") else line
                haystack = text.lower() if ignore_case else text

                matched = haystack == needle if entire_line else needle in haystack
                if invert:
                    matched = not matched
                if not matched:
                    continue

                if want_filenames_only:
                    parts.append(filename + "\n")
                    break

                prefix = ""
                if multiple_files:
                    prefix += filename + ":"
                if want_line_numbers:
                    prefix += str(line_no) + ":"
                parts.append(prefix + text + "\n")

    return "".join(parts)
