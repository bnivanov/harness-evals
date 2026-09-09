def grep(pattern, flags, files):
    options = _parse_flags(flags)
    multi_file = len(files) > 1
    needle = pattern.casefold() if options["i"] else pattern
    results = []

    for filename in files:
        with open(filename, encoding="utf-8") as file_handle:
            for line_number, raw_line in enumerate(file_handle, start=1):
                # Iterating over the text stream handles standard newlines without
                # treating characters such as form feed as line separators.
                line = raw_line.rstrip("\r\n")
                haystack = line.casefold() if options["i"] else line
                matched = (
                    haystack == needle
                    if options["x"]
                    else needle in haystack
                )
                if options["v"]:
                    matched = not matched
                if not matched:
                    continue

                if options["l"]:
                    results.append(filename + "\n")
                    break

                prefix = ""
                if multi_file:
                    prefix += filename + ":"
                if options["n"]:
                    prefix += str(line_number) + ":"
                results.append(prefix + line + "\n")

    return "".join(results)


def _parse_flags(flags):
    """Return the supported flags, including bundled short options."""
    flag_tokens = flags.split() if isinstance(flags, str) else list(flags)
    supported = {"n", "l", "i", "v", "x"}
    enabled = set()

    for token in flag_tokens:
        if token in {"-" + option for option in supported}:
            enabled.add(token[1:])
        elif (
            len(token) > 2
            and token.startswith("-")
            and not token.startswith("--")
            and all(option in supported for option in token[1:])
        ):
            enabled.update(token[1:])

    return {option: option in enabled for option in supported}
