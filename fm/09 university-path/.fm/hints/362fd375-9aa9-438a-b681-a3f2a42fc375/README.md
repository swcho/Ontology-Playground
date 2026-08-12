# 성적이 부진한 학과를 찾는 GQL 질의

## 질문

성적이 부진한 학과를 찾는 GQL 질의는 어떤 형태인가?

## 답

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

"학과가 개설한 과목 중에서 C·D·F 학점을 받은 수강 기록이 많은 순으로 (학과, 과목) 쌍을 뽑아라"는 뜻이다.

---

## 0. 배경: GQL이란 무엇인가

- **GQL(Graph Query Language)** 은 **ISO/IEC 39075:2024** 로 제정된 국제 표준 그래프 질의어다. SQL(ISO/IEC 9075) 이후 ISO가 새로 만든 최초의 데이터베이스 질의어 표준이며, 속성 그래프(property graph) 모델을 1급 대상으로 삼는다.
- 문법적 뿌리는 Neo4j의 **Cypher**(및 openCypher, PGQL, GSQL)다. 특히 `MATCH ... WHERE ... RETURN` 구조와 `(노드)-[:관계]->(노드)` 형태의 **ASCII-art 경로 패턴**은 Cypher에서 그대로 이어졌다. 그래서 위 질의는 Cypher로도 거의 그대로 실행된다.
- 관련 표준으로 **SQL/PGQ**(SQL:2023의 Property Graph Queries)가 있어, 관계형 테이블 위에 그래프 뷰를 얹고 같은 패턴 매칭 문법을 쓸 수 있다.
- 핵심 차이: SQL이라면 `Department JOIN Course JOIN Enrollment JOIN Student` 로 JOIN을 4개 써야 할 것을, GQL은 **경로 한 줄**로 표현한다. 온톨로지가 "다중 홉 관계"를 자연스럽게 다룬다는 점을 보여주는 예다.

---

## 1. MATCH 절: 경로 패턴 분해

```
(d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
```

이 한 줄은 **노드 4개 + 관계 3개(3홉)** 로 이루어진 경로다. 홉 단위로 끊어 보면:

| # | 패턴 조각 | 방향 | 읽는 법 |
|---|---|---|---|
| 1 | `(d:Department)-[:offers]->(c:Course)` | 오른쪽(→) | 학과가 과목을 **개설한다** |
| 2 | `(c:Course)<-[:for_course]-(e:Enrollment)` | 왼쪽(←) | 수강 기록이 그 과목을 **대상으로 한다** |
| 3 | `(e:Enrollment)<-[:enrolls_in]-(s:Student)` | 왼쪽(←) | 학생이 그 수강 기록으로 **등록한다** |

### 화살표 방향이 왜 이렇게 섞이는가

온톨로지에 정의된 관계의 **원래 방향**이 서로 반대를 향하기 때문이다.

- `offers` — `Department → Course` (1:N)
- `for_course` — `Enrollment → Course` (N:1)
- `enrolls_in` — `Student → Enrollment` (1:N)

즉 `Course` 노드는 두 관계가 **모두 들어오는 지점**(Department에서 오고, Enrollment에서 온다)이다. 그래서 경로를 Department에서 Student 쪽으로 왼쪽→오른쪽으로 쓰면, `Course` 이후부터는 관계를 **거슬러 올라가야** 하므로 `<-[:...]-` 로 뒤집힌다.

그림으로 보면 이렇다.

```
Department --offers--> Course <--for_course-- Enrollment <--enrolls_in-- Student
```

화살표를 임의로 `->`로 통일해 쓰면 그래프에 존재하지 않는 방향을 요구하게 되어 **결과가 0건**이 된다. GQL/Cypher에서 방향은 장식이 아니라 매칭 조건이다.

### 변수 바인딩

`d`, `c`, `e`, `s`는 각 위치에 매칭된 노드를 담는 **변수(바인딩)** 다. `:Department`, `:Course` 등은 **레이블(타입)** 로, 매칭 대상을 그 타입의 노드로 제한한다.

- 변수 없이 `(:Department)` 처럼 써도 매칭은 되지만, 이후 `WHERE`/`RETURN`에서 참조할 수 없다.
- 관계에는 변수를 붙이지 않고 `[:offers]` 처럼 타입만 지정했다. 관계 속성을 쓸 일이 없기 때문이다. 필요하면 `[r:offers]` 로 이름을 줄 수 있다.
- MATCH의 결과는 "노드 하나"가 아니라 **경로 한 벌마다 (d, c, e, s) 조합 한 행**이다. 학생 300명이 한 과목을 들으면 그 과목에 대해 300행이 나온다.

---

## 2. WHERE 절: 성적 필터

```gql
WHERE e.grade IN ['C', 'D', 'F']
```

- `e.grade`는 **Enrollment 엔티티의 `grade` 속성**이다. 학점은 Student에도 Course에도 없다 — "이 학생이 이 과목에서 받은 성적"은 두 엔티티 어디에도 속하지 않고, 오직 둘을 잇는 **정션 엔티티(junction entity)** 인 Enrollment에만 존재한다. 이 질의는 정션 엔티티 패턴이 왜 필요한지 보여주는 실제 사례다.
- `grade`는 문자열 타입이므로 `< 'B'` 같은 비교 대신 **`IN` 으로 값 집합을 열거**했다. 문자열 사전순 비교를 쓰면 `'A+'`, `'B-'` 같은 표기나 `'W'`(withdrawal), `'I'`(incomplete) 등에서 의도치 않은 결과가 나올 수 있다. 열거 방식이 명시적이고 안전하다.
- WHERE는 MATCH가 만들어 낸 행들을 **집계 이전에** 걸러낸다. 따라서 뒤의 `COUNT(e)`는 "부진 학점 수강 기록의 수"만 센다.
- 자료의 설명 문구는 "평균 학점이 B 미만"이라고 되어 있지만, 실제 질의는 평균을 계산하지 않고 **C/D/F 건수를 세는** 방식이다. 설명과 구현이 정확히 일치하지는 않는다는 점을 알아두면 좋다.

---

## 3. RETURN 절: 집계와 암묵적 GROUP BY

```gql
RETURN d.name, c.title, COUNT(e) AS struggling_count
```

- `d.name`(학과명), `c.title`(과목명), 그리고 집계값 `COUNT(e)`를 반환한다.
- `AS struggling_count` 는 결과 컬럼에 **별칭**을 붙인다. 이 별칭은 `ORDER BY`에서 다시 참조된다.

### 암묵적 GROUP BY가 핵심

GQL/Cypher에는 **`GROUP BY` 절이 없다.** 대신 규칙이 이렇다.

> RETURN 목록에서 **집계 함수가 아닌 표현식들**이 자동으로 그룹화 키가 된다.

여기서는 `d.name`과 `c.title`이 비집계 표현식이므로, **(학과명, 과목명) 쌍**이 그룹 키다. SQL로 옮기면 다음과 같다.

```sql
GROUP BY d.name, c.title
```

즉 결과는 "학과별"이 아니라 **"학과 × 과목별" 한 줄씩**이다. 학과 단위 합계를 원하면 `c.title`을 RETURN에서 빼야 한다.

```gql
RETURN d.name, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

이 암묵 규칙은 편리하지만 실수를 낳기 쉽다. RETURN에 컬럼을 하나 추가하는 순간 **그룹 단위가 소리 없이 바뀌고 숫자가 전부 달라진다**. GQL을 읽을 때는 "비집계 컬럼이 무엇인가"를 먼저 확인하는 습관이 필요하다.

### `s`는 RETURN에 없는데 왜 필요한가

`s:Student`는 WHERE에도 RETURN에도 등장하지 않는다. 그럼에도 빼면 안 되는 이유는 두 가지다.

1. **존재 조건(구조 필터) 역할.** 마지막 홉을 유지하면 "실제 학생이 연결된 Enrollment"만 매칭된다. 학생 연결이 끊긴 고아(orphan) 수강 기록, 데이터 정합성이 깨진 레코드, 시스템이 만든 더미 등록은 자동으로 제외된다. 패턴의 존재 자체가 필터다.
2. **의미 표현과 확장 지점.** 질문은 "학생들이 부진하다"이므로 경로에 Student가 있어야 도메인 의도가 드러난다. 또한 나중에 `WHERE s.enrollmentYear = 2024` 같은 조건이나 `COUNT(DISTINCT s)` 를 추가하려면 이 바인딩이 있어야 한다.

다만 **주의점**도 있다. `enrolls_in`은 Student → Enrollment 1:N이므로 Enrollment 하나에 학생이 하나 붙는 것이 정상이다. 만약 데이터가 어긋나 한 Enrollment에 학생이 여러 명 연결되면 **경로가 늘어나 `COUNT(e)`가 부풀려진다**. 이런 위험을 없애려면 `COUNT(DISTINCT e)` 를 쓰거나, s가 정말 불필요하면 마지막 홉을 제거하는 편이 안전하다.

---

## 4. ORDER BY 절

```gql
ORDER BY struggling_count DESC
```

- 집계 결과를 **내림차순(DESC)** 으로 정렬해, 부진 건수가 가장 많은 (학과, 과목)이 맨 위에 온다. 기본값은 오름차순(ASC)이다.
- RETURN에서 정의한 **별칭을 그대로 사용**할 수 있다. `ORDER BY COUNT(e) DESC` 라고 다시 써도 되지만 별칭 쪽이 읽기 좋다.
- 실무에서는 상위 몇 건만 보면 되므로 `LIMIT 10` 을 덧붙이는 경우가 많다.

---

## 5. 이 질의의 한계: "건수"만 세고 "비율"은 세지 않는다

이것이 이 질의에서 가장 중요한 함정이다.

`COUNT(e)`는 **절대 건수**다. 따라서 **수강생이 많은 대형 과목이 무조건 상위에 오른다.**

| 과목 | 전체 수강 | C/D/F | struggling_count | 실제 부진 비율 |
|---|---|---|---|---|
| 심리학 개론 (대형) | 500 | 60 | **60** | 12% |
| 고급 위상수학 (소형) | 15 | 12 | 12 | **80%** |

정렬 결과에서는 심리학 개론이 1위지만, 정작 심각한 문제가 있는 과목은 80%가 부진한 위상수학이다. 이 질의는 그것을 잡아내지 못한다.

원래 시나리오가 던진 질문은 **"수강생의 50% 초과가 C 미만인 과목"** 이었다는 점을 상기하자. 그것은 비율 질문이지 건수 질문이 아니다. 즉 이 예시 질의는 그 질문에 대한 **부분적인 근사**일 뿐이다.

### 비율까지 구하려면

전체 수강 건수와 부진 건수를 **함께** 집계해야 한다. WHERE로 미리 걸러 버리면 분모가 사라지므로, 필터를 집계 안쪽으로 옮기는 것이 요령이다. (Cypher 계열 표현 예시)

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)
WITH d.name AS dept,
     c.title AS course,
     COUNT(e) AS total,
     COUNT(CASE WHEN e.grade IN ['C','D','F'] THEN 1 END) AS struggling
WHERE total >= 10
RETURN dept, course, struggling, total,
       toFloat(struggling) / total AS struggling_rate
ORDER BY struggling_rate DESC
```

여기서 배울 점:

- **WHERE의 위치가 의미를 바꾼다.** MATCH 직후의 WHERE는 "무엇을 셀지"를 정하고, 집계 후(WITH 뒤)의 WHERE는 "어떤 그룹을 남길지"를 정한다. SQL의 `WHERE` vs `HAVING` 구분과 같다.
- **분모를 지키려면 필터를 집계식 안으로 넣어야 한다** (조건부 집계).
- `total >= 10` 같은 **최소 표본 조건**이 없으면 "3명 중 3명 부진 = 100%" 같은 잡음이 상위를 차지한다.

### 그 밖의 한계

- `WITHDRAWN`, `AUDIT` 등 `e.status`를 무시하므로 실제 이수하지 않은 기록도 함께 센다.
- 성적이 아직 없는(`grade`가 null) 진행 중 수강은 자연히 빠지지만, 이것이 의도한 동작인지는 명시되어 있지 않다.
- `semester` 필터가 없어 여러 학기가 뭉뚱그려진다. 시계열 추세는 볼 수 없다.
- 학과명(`d.name`)으로 그룹화하므로 동명이 학과가 있으면 병합된다. 엄밀히는 식별자인 `d.departmentId` 로 그룹화하는 편이 안전하다.

---

## 6. 한 줄 요약 암기 포인트

1. 경로: `Department -offers-> Course <-for_course- Enrollment <-enrolls_in- Student` (**3홉, Course에서 화살표가 마주본다**)
2. 필터: `WHERE e.grade IN ['C','D','F']` — 학점은 **정션 엔티티 Enrollment**의 속성
3. 집계: `COUNT(e) AS struggling_count`, 그룹 키는 **비집계 컬럼인 `d.name`, `c.title`** (암묵적 GROUP BY)
4. 정렬: `ORDER BY struggling_count DESC`
5. 한계: **건수 ≠ 비율**. 대형 강의 편향이 있으며 분모(전체 수강)를 함께 세야 진짜 답이 나온다
6. `s`는 출력에 없어도 **존재 조건이자 확장 지점**으로 필요하다
