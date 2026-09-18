def contains_company_alias(
    *,
    aliases: list[str],
    title: str | None = None,
    description: str | None = None,
    content: str | None = None,
) -> bool:
    haystack = " ".join(
        value
        for value in (
            title,
            description,
            content,
        )
        if value
    ).casefold()

    normalized_aliases = {
        alias.strip().casefold()
        for alias in aliases
        if alias and alias.strip()
    }

    if not normalized_aliases:
        return False

    for alias in normalized_aliases:
        if alias == "chatgpt":
            if alias in haystack and "openai" in haystack:
                return True
            continue

        if alias in haystack:
            return True

    return False
