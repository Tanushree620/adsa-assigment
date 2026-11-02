
from naive import naive_search

# Test cases: text, pattern, expected position
test_cases = [
    ("DATASTRUCTURES", "STRUCT", 4),
    ("HELLO WORLD", "WORLD", 6),
    ("BANANA", "ANA", 1),
    ("PYTHON", "JAVA", -1),
    ("ABC", "ABC", 0),
    ("ABC", "ABCD", -1),
    ("ABC", "", 0)
]

passed = 0
failed = 0

print("NAIVE STRING MATCHING - TESTING")
print("--------------------------------")

for text, pattern, expected in test_cases:

    position, comparisons = naive_search(text, pattern)

    if position == expected:
        print("PASS:", text, "|", pattern,
              "| Position:", position,
              "| Comparisons:", comparisons)
        passed += 1
    else:
        print("FAIL:", text, "|", pattern,
              "| Expected:", expected,
              "| Actual:", position)
        failed += 1

print("\nTEST SUMMARY")
print("Total tests:", passed + failed)
print("Passed:", passed)
print("Failed:", failed)
print("All tests passed:", failed == 0)

