# 구현 계획

`SPEC.md`를 기준으로 한다. 코드는 이 문서에 쓰지 않는다.

## 순서 (테스트가 먼저)

1. **테스트 먼저** (4단계)
   - `tests/test_hash_table.py`: SPEC §6 해시 테이블 경계 사례
   - `tests/test_shortener.py`: SPEC §6 단축기 경계 사례
   - 이 시점에는 실패하는 것이 정상이다
2. **해시 테이블** `src/hash_table.py`
   - `horner_hash(key, m)`: 글자마다 `h = (31·h + ord(c)) % m`
   - `Node`(key, value, next)로 연결 리스트를 만든다. 버킷 배열은 파이썬 `list`
   - `put`/`get`/`find`/`__len__`/`__contains__`/`load_factor`
   - `max_load`를 넘으면 버킷 2배, 모든 노드 다시 넣기
3. **단축기** `src/shortener.py`
   - 테이블 두 개(코드→URL, URL→코드)를 `table_class`로 만든다
   - 일련번호 카운터(1부터) → `base62.encode`로 코드
   - URL 검사 함수 하나로 잘못된 입력을 모은다
4. `make test` 통과까지 **코드만** 고친다. 테스트는 고치지 않는다
5. 규칙 파일 (5단계), 실험 (6단계), 서버 (7단계)
6. 과제: `LinearProbingHashTable`을 같은 파일에, 같은 테스트를 두 클래스에 돌린다

## 명세와 맞는지 점검한 항목

- 코드→URL, URL→코드 저장 모두 직접 만든 `HashTable` 사용, `dict` 없음 (SPEC §3)
- 코드는 일련번호의 base62. URL 해시값으로 만들지 않음 — 해시는 충돌하므로
  두 URL이 같은 코드를 받을 수 있다 (SPEC §4)
- 테스트 작성이 구현보다 먼저

## 확인 방법

- `make test` 결과
- `grep -nE "dict\(|\{\}|set\(|hash\(" src/` 로 금지 항목 점검 (`horner_hash(`는 예외)
