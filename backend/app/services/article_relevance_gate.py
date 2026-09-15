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

    return any(
        alias in haystack
        for alias in normalized_aliases
    )
