def pluralize(n: int, form1: str, form2: str, form5: str) -> str:
    """Return the correct Belarusian plural form for a number.

    Args:
        n: The number to pluralize for.
        form1: Singular form (1 дзень).
        form2: Few form (2 дні).
        form5: Many form (5 дзён).
    """
    remainder100 = abs(n) % 100
    remainder10 = remainder100 % 10
    if 11 <= remainder100 <= 19:
        return form5
    if remainder10 == 1:
        return form1
    if 2 <= remainder10 <= 4:
        return form2
    return form5
