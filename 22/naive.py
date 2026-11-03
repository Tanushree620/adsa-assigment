def naive_search(text, pattern):
    """
    Naive String Matching Algorithm.

    Searches for the first occurrence of a pattern
    in the given text.

    Returns:
        position: Starting index of the pattern.
                  Returns -1 if pattern is not found.
        comparisons: Total number of character comparisons.
    """

    n = len(text)
    m = len(pattern)

    comparisons = 0

    # Handle empty pattern
    if m == 0:
        return 0, comparisons

    # Check every possible starting position
    for i in range(n - m + 1):

        j = 0

        # Compare pattern characters with text characters
        while j < m:

            comparisons += 1

            if text[i + j] != pattern[j]:
                break

            j += 1

        # Pattern found completely
        if j == m:
            return i, comparisons

    # Pattern not found
    return -1, comparisons
