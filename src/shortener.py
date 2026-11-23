"""URL 단축기.

코드는 일련번호(1, 2, 3, ...)를 base62로 바꾼 것이다.
URL의 해시값으로 코드를 만들지 않는다. 해시는 충돌하므로 서로 다른 URL이 같은 코드를 받게 된다.
"""

from base62 import decode, encode
from hash_table import HashTable

MAX_URL_LENGTH = 2048
SCHEMES = ("http://", "https://")


def validate_url(url):
    """검사를 통과하면 앞뒤 공백을 지운 URL을, 아니면 ValueError."""
    if not isinstance(url, str):
        raise ValueError("URL은 문자열이어야 합니다")
    url = url.strip()
    if url == "":
        raise ValueError("빈 URL입니다")
    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f"URL이 {MAX_URL_LENGTH}자를 넘습니다")
    for ch in url:
        if ch.isspace() or ord(ch) < 32 or ord(ch) == 127:
            raise ValueError("URL에 공백이나 제어 문자가 있습니다")
    scheme = None
    for s in SCHEMES:
        if url.lower().startswith(s):
            scheme = s
    if scheme is None:
        raise ValueError("http:// 또는 https:// 로 시작해야 합니다")
    rest = url[len(scheme):]
    host = rest
    for sep in "/?#":
        host = host.split(sep, 1)[0]
    if host == "":
        raise ValueError("호스트가 없습니다")
    return url


class Shortener:
    def __init__(self, table_class=HashTable):
        self.table_class = table_class
        self.by_code = table_class()  # 코드 -> URL
        self.by_url = table_class()   # URL -> 코드
        self._next = 1

    def shorten(self, url):
        url = validate_url(url)
        found, code, _ = self.by_url.find(url)
        if found:
            return code
        code = encode(self._next)
        self._next += 1
        self.by_code.put(code, url)
        self.by_url.put(url, code)
        return code

    def expand(self, code):
        """원래 URL. 없는 코드나 base62가 아닌 코드는 None."""
        if not isinstance(code, str):
            return None
        try:
            decode(code)
        except ValueError:
            return None
        found, url, _ = self.by_code.find(code)
        return url if found else None

    def __len__(self):
        return len(self.by_code)
