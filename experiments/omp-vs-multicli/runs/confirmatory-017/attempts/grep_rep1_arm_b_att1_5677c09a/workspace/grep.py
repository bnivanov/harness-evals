def _strip_terminator(line):
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def grep(pattern, flags, files):
    options = set()
    tokens = flags.split() if isinstance(flags, str) else flags
    for token in tokens:
        if token.startswith("-"):
            options.update(token[1:])
        else:
            options.update(token)

    opt_i = "i" in options
    opt_x = "x" in options
    opt_v = "v" in options
    opt_l = "l" in options
    opt_n = "n" in options
    comparison_pattern = pattern.casefold() if opt_i else pattern
    multiple_files = len(files) > 1
    output = []

    for filepath in files:
        with open(filepath) as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = _strip_terminator(raw_line)
                comparison_line = line.casefold() if opt_i else line

                if opt_x:
                    selected = comparison_line == comparison_pattern
                else:
                    selected = comparison_pattern in comparison_line

                if opt_v:
                    selected = not selected

                if not selected:
                    continue

                if opt_l:
                    output.append(filepath + "\n")
                    break

                prefix = []
                if multiple_files:
                    prefix.append(filepath)
                if opt_n:
                    prefix.append(str(line_number))

                body = line + "\n"
                if prefix:
                    output.append(":".join(prefix) + ":" + body)
                else:
                    output.append(body)

    return "".join(output)
