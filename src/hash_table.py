"""직접 만든 해시 테이블.

- horner_hash: Horner 방식 문자열 해시  h = (31*h + ord(c)) mod m
- HashTable: 분리 연결(chaining). 버킷마다 연결 리스트

파이썬 내장 사전·집합 자료형과 내장 해시 함수는 쓰지 않는다.
버킷 배열만 파이썬 list를 쓴다.
"""

MULTIPLIER = 31


def horner_hash(key, m):
    """문자열 key를 0 ~ m-1 사이 정수로 바꾼다."""
    h = 0
    for ch in key:
        h = (MULTIPLIER * h + ord(ch)) % m
    return h


def horner_steps(key, m):
    """/table 화면용: 글자마다 (글자, ord, 계산 전 h, 계산 후 h)."""
    steps = []
    h = 0
    for ch in key:
        new_h = (MULTIPLIER * h + ord(ch)) % m
        steps.append((ch, ord(ch), h, new_h))
        h = new_h
    return steps


def _check_args(capacity, max_load):
    if not isinstance(capacity, int) or capacity < 1:
        raise ValueError("capacity는 1 이상의 정수여야 합니다")
    if max_load is not None and not max_load > 0:
        raise ValueError("max_load는 0보다 커야 합니다 (늘리지 않으려면 None)")


def _check_key(key):
    if not isinstance(key, str):
        raise TypeError("키는 문자열이어야 합니다")


class Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next=None):
        self.key = key
        self.value = value
        self.next = next


class HashTable:
    """분리 연결 해시 테이블."""

    kind = "chaining"

    def __init__(self, capacity=16, max_load=0.75):
        _check_args(capacity, max_load)
        self.capacity = capacity
        self.max_load = max_load
        self._buckets = [None] * capacity
        self._size = 0

    # --- 기본 연산 -------------------------------------------------

    def _index(self, key):
        return horner_hash(key, self.capacity)

    def put(self, key, value):
        _check_key(key)
        i = self._index(key)
        node = self._buckets[i]
        if node is None:
            self._buckets[i] = Node(key, value)
        else:
            while True:
                if node.key == key:
                    node.value = value  # 있던 키: 값만 바꾼다
                    return
                if node.next is None:
                    break
                node = node.next
            node.next = Node(key, value)  # 체인 끝에 붙인다
        self._size += 1
        if self.max_load is not None and self.load_factor() > self.max_load:
            self._resize(self.capacity * 2)

    def find(self, key):
        """(찾았는가, 값 또는 None, 비교한 노드 수)."""
        _check_key(key)
        node = self._buckets[self._index(key)]
        compares = 0
        while node is not None:
            compares += 1
            if node.key == key:
                return True, node.value, compares
            node = node.next
        return False, None, compares

    def get(self, key):
        found, value, _ = self.find(key)
        if not found:
            raise KeyError(key)
        return value

    def __contains__(self, key):
        if not isinstance(key, str):
            return False
        return self.find(key)[0]

    def __len__(self):
        return self._size

    def load_factor(self):
        return self._size / self.capacity

    # --- 내부 ------------------------------------------------------

    def _resize(self, new_capacity):
        old = self._buckets
        self.capacity = new_capacity
        self._buckets = [None] * new_capacity
        self._size = 0
        max_load, self.max_load = self.max_load, None  # 다시 넣는 동안 또 늘리지 않는다
        for node in old:
            while node is not None:
                self.put(node.key, node.value)
                node = node.next
        self.max_load = max_load

    # --- 보기용 ----------------------------------------------------

    def buckets(self):
        """버킷마다 [(key, value), ...] 체인 목록."""
        out = []
        for node in self._buckets:
            chain = []
            while node is not None:
                chain.append((node.key, node.value))
                node = node.next
            out.append(chain)
        return out

    def items(self):
        for chain in self.buckets():
            for kv in chain:
                yield kv


# 서버가 --table 옵션으로 고르는 목록: (이름, 클래스)
TABLES = [("chaining", HashTable)]
