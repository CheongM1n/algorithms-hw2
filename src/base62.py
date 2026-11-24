"""base62 인코딩.

글자 순서는 0-9, a-z, A-Z 이다. (0 -> "0", 9 -> "9", 10 -> "a", 36 -> "A", 61 -> "Z")
"""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)  # 62


def _digit(ch):
    """글자 하나를 0~61 값으로 바꾼다. base62 글자가 아니면 ValueError."""
    if "0" <= ch <= "9":
        return ord(ch) - ord("0")
    if "a" <= ch <= "z":
        return ord(ch) - ord("a") + 10
    if "A" <= ch <= "Z":
        return ord(ch) - ord("A") + 36
    raise ValueError(f"base62 글자가 아닙니다: {ch!r}")


def encode(n):
    """0 이상의 정수를 base62 문자열로 바꾼다."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("정수만 인코딩할 수 있습니다")
    if n < 0:
        raise ValueError("음수는 인코딩할 수 없습니다")
    if n == 0:
        return ALPHABET[0]
    digits = []
    while n > 0:
        n, r = divmod(n, BASE)
        digits.append(ALPHABET[r])
    return "".join(reversed(digits))


def decode(s):
    """base62 문자열을 정수로 바꾼다. 빈 문자열이나 잘못된 글자는 ValueError."""
    if not isinstance(s, str):
        raise TypeError("문자열만 디코딩할 수 있습니다")
    if s == "":
        raise ValueError("빈 문자열은 디코딩할 수 없습니다")
    n = 0
    for ch in s:
        n = n * BASE + _digit(ch)
    return n
