# 명세: URL 단축기

> AI 초안을 채청민이 검토해 확정함. 에이전트는 이 파일을 읽고 구현한다.

## 1. 무엇을 만드는가

사용자가 긴 URL을 넣으면 짧은 코드(예: `http://localhost:8000/a3`)를 돌려주고,
그 코드로 접속하면 원래 URL로 보내 주는 서비스. 저장은 직접 만든 해시 테이블로 한다.

## 2. base62 인코딩

- 파일: `src/base62.py`, 함수 `encode(n) -> str`, `decode(s) -> int`
- 글자 순서: `0-9`, `a-z`, `A-Z` (0→`"0"`, 10→`"a"`, 36→`"A"`, 61→`"Z"`)
- `encode(0)` 은 `"0"`
- 음수: `ValueError`. 정수가 아닌 값(`bool` 포함): `TypeError`
- `decode("")`, base62가 아닌 글자: `ValueError`. 대소문자를 구분한다

## 3. 해시 테이블

- 파일: `src/hash_table.py`
- 해시 함수: Horner 방식 `h = (31·h + ord(c)) mod M`, `h`는 0에서 시작. 키는 문자열만
- 충돌 처리: **분리 연결(chaining)**. 버킷마다 연결 리스트, 새 키는 리스트 끝에 붙인다
- 인터페이스 (`HashTable`)
  - `HashTable(capacity=16, max_load=0.75)`
  - `put(key, value)`: 있으면 값 교체, 없으면 추가
  - `get(key)`: 값, 없으면 `KeyError`
  - `find(key)`: `(찾았는가, 값 또는 None, 비교 횟수)` — 실험용
  - `len(t)`, `key in t`, `load_factor()` = 원소 수 / 버킷 수
- 크기: 처음 16. `max_load`를 넘으면 버킷 수를 2배로 늘리고 모두 다시 넣는다.
  `max_load=None`이면 늘리지 않는다 (실험용)
- **쓰면 안 되는 것**: `dict`, `set`, 내장 `hash()` (`src/` 전체)
- 삭제는 이번 과제에서 만들지 않는다
- 과제용 두 번째 방식 `LinearProbingHashTable`: 선형 탐사(충돌하면 다음 칸, 끝에서 처음으로 넘어감)
  - 인터페이스는 `HashTable`과 같다. 처음 16칸, 50%를 넘으면 2배
  - 꽉 찬 테이블에 새 키를 넣으면 `OverflowError`
  - 단축기는 `Shortener(table_class=...)`로 둘 중 하나를 고른다

## 4. 단축기

- 파일: `src/shortener.py`, 클래스 `Shortener(table_class=HashTable)`
- `shorten(url) -> code`: 코드는 **일련번호를 base62로 인코딩**한 것 (1부터 시작: 첫 코드는 `"1"`).
  URL의 해시값으로 코드를 만들지 않는다 (충돌하면 두 URL이 같은 코드가 된다)
- 같은 URL을 두 번 넣으면 처음 받은 코드를 그대로 돌려준다 (새 번호를 쓰지 않는다)
- 테이블 두 개: 코드 → URL, URL → 코드
- `expand(code) -> url`: 없는 코드나 base62가 아닌 코드는 `None`
- 잘못된 URL은 `ValueError`
  - 문자열이 아님, 빈 문자열
  - `http://` 또는 `https://`로 시작하지 않음, 그 뒤에 호스트가 없음
  - 공백·제어 문자 포함, 2048자 초과
- 앞뒤 공백은 지우고 처리한다. 그 밖의 정규화(대소문자, 끝의 `/`)는 하지 않는다

## 5. 웹 서버

- 파일: `src/server.py`, 표준 모듈 `http.server`만 사용. `make serve`로 포트 8000
- `GET /`: URL 입력 폼
- `POST /shorten`: 폼 값 `url` → 결과 페이지(단축 링크). 잘못된 URL이면 400과 안내 문구
- `GET /<code>`: 있으면 `302` + `Location: 원래 URL`, 없으면 `404`
- `GET /table`: 코드→URL 테이블의 버킷(체인)과 각 코드의 Horner 해시 계산 과정

## 6. 경계 사례

base62
- `encode(0) == "0"`, `encode(61) == "Z"`, `encode(62) == "10"`
- 음수, 실수, `True`, 빈 문자열, `"-"`, `"가"` 같은 잘못된 입력
- 큰 수 왕복 (`2**64`)

해시 테이블
- 빈 테이블에서 `get` → `KeyError`, `in` → False, `len` → 0
- 같은 키를 두 번 `put` → 값만 바뀌고 `len`은 그대로
- 빈 문자열 키, 한글 키
- 해시값이 같은 키들 (예: `M=11`에서 충돌하는 키) 모두 찾을 수 있다
- 늘어난 뒤에도 모든 키를 찾을 수 있다
- 문자열이 아닌 키 → `TypeError`
- `dict`, `set`, `hash(` 가 소스에 없다

단축기
- 첫 코드 `"1"`, 다음 `"2"`. 같은 URL 다시 넣으면 같은 코드
- `expand` 왕복, 없는 코드 → `None`, `"!!"` 같은 코드 → `None`
- 잘못된 URL: `""`, `"   "`, `"example.com"`, `"ftp://a.com"`, `"http://"`, 공백 포함, 2049자
- 앞뒤 공백이 있는 URL은 지운 것과 같은 코드
- 많은 URL(1000개) 넣고 모두 왕복
