import re

ExpectedType = re.Pattern | str | list["ExpectedType"] | dict[str, "ExpectedType"]
ActualType = str | list["ActualType"] | dict[str, "ActualType"]


def assert_matches(expected: ExpectedType, actual: ActualType):
    """
    Recursively compare the expected and actual values.

    Args:
        expected: The expected value. If this is a compiled regex,
                  it will be matched against the actual value.
        actual: The actual value.

    Raises:
        AssertionError: If the expected and actual values do not match.
    """
    if isinstance(expected, dict):
        assert set(expected.keys()) == set(actual.keys())
        for key, value in expected.items():
            assert_matches(value, actual[key])
    elif isinstance(expected, (list, tuple)):
        assert len(expected) == len(actual)
        for a, b in zip(expected, actual, strict=False):
            assert_matches(a, b)
    elif isinstance(expected, re.Pattern):
        assert expected.match(actual)
    else:
        assert expected == actual
