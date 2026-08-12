# Student 중심 질의와 Professor 중심 질의를 모두 지원한다는 뜻

## 한 줄 요약

**관계는 방향을 갖지만 순회(traversal)는 양방향이다.** 그래서 같은 그래프 하나로
"학생에서 출발해 성적·담당 교수를 보는 질의"와 "교수에서 출발해 수강 학생을 보는 질의"를
모두 처리할 수 있다. 출발점(앵커)만 바꾸면 된다.

---

## 1. 대상이 되는 그래프

University 온톨로지의 관련 부분만 떼어 보면 이렇다.

```
(Student) -[:enrolls_in]-> (Enrollment) -[:for_course]-> (Course) <-[:teaches]- (Professor)
                                                                        |
(Student) <-------------------- [:advises] ----------------------------+
```

| 관계 | 방향 | 카디널리티 |
|---|---|---|
| `enrolls_in` | Student → Enrollment | 1:N |
| `for_course` | Enrollment → Course | N:1 |
| `teaches` | Professor → Course | 1:N |
| `advises` | Professor → Student | 1:N |

여기서 화살표 방향은 **"어느 쪽이 소유/주체인가"라는 의미(semantics)** 를 적어둔 것이지,
"이 방향으로만 읽을 수 있다"는 접근 제약이 아니다.

---

## 2. 방향은 의미, 순회는 양방향

### 왜 반대로도 갈 수 있나

그래프 저장소는 각 노드마다 **나가는 간선 목록(outgoing adjacency)과
들어오는 간선 목록(incoming adjacency)** 을 함께 들고 있다.
`Professor -[:teaches]-> Course` 간선 하나를 저장하면,
Professor 쪽에는 "내가 가르치는 Course들", Course 쪽에는 "나를 가르치는 Professor들"이
동시에 붙는다. 그래서 어느 쪽 노드를 손에 쥐고 있든 간선을 따라 반대편으로 한 홉 이동하는 비용이
같은 수준(포인터 추적, index-free adjacency)이다.

질의 언어(GQL/Cypher 계열)에서는 이 반대 방향 순회를 화살표를 뒤집어 표현한다.

```gql
-- 같은 간선을 두 방향으로 읽는다
(p:Professor)-[:teaches]->(c:Course)     -- 교수에서 과목으로
(c:Course)<-[:teaches]-(p:Professor)     -- 과목에서 교수로
```

두 패턴은 **같은 데이터, 같은 간선**을 가리킨다. 새 관계를 추가하거나
`taught_by` 같은 역관계를 따로 정의할 필요가 없다.

> 주의: 화살표를 아예 빼서 `-[:teaches]-` 로 무방향 매칭을 쓸 수도 있지만,
> 그러면 "교수가 과목을 가르친다"는 방향 의미가 사라져 의도치 않은 매칭이 생길 수 있다.
> 방향은 명시하고, 필요할 때 뒤집어 쓰는 것이 원칙이다.

---

## 3. 대칭 질의 쌍 — 출발점만 바꾼 같은 그래프

### (A) Student 중심: "이 학생이 듣는 과목의 담당 교수는 누구인가"

```gql
MATCH (s:Student {studentId: 'S-1001'})
      -[:enrolls_in]->(e:Enrollment)
      -[:for_course]->(c:Course)
      <-[:teaches]-(p:Professor)
WHERE e.semester = '2026-Spring'
RETURN s.name, c.title, e.grade, p.name, p.rank
```

### (B) Professor 중심: "이 교수의 과목을 듣는 학생은 누구인가"

```gql
MATCH (p:Professor {professorId: 'P-77'})
      -[:teaches]->(c:Course)
      <-[:for_course]-(e:Enrollment)
      <-[:enrolls_in]-(s:Student)
WHERE e.semester = '2026-Spring'
RETURN p.name, c.title, s.name, e.grade
```

두 질의를 나란히 보면 차이는 딱 두 가지다.

1. **앵커(시작 노드)** 가 `Student`냐 `Professor`냐
2. **화살표 방향 표기**가 뒤집혔을 뿐, 경유하는 관계 이름은 `enrolls_in`, `for_course`, `teaches`로 동일

즉 **스키마도 그대로, 적재된 간선도 그대로**다. 이것이 "Student 중심 질의와 Professor 중심 질의를
모두 지원한다"는 말의 실제 내용이다.

### 보너스: 지도 관계도 같은 방식

```gql
-- 학생 → 지도교수
MATCH (s:Student {studentId: 'S-1001'})<-[:advises]-(p:Professor)
RETURN p.name, p.officeHours

-- 교수 → 지도 학생
MATCH (p:Professor {professorId: 'P-77'})-[:advises]->(s:Student)
RETURN s.name, s.gpa
```

---

## 4. 관계형 DB의 테이블 중심 설계와의 대비

같은 데이터를 RDB로 두면 대략 이렇다.

```sql
student(student_id PK, name, gpa, ...)
course(course_id PK, title, professor_id FK, ...)
enrollment(enrollment_id PK, student_id FK, course_id FK, grade, semester, ...)
professor(professor_id PK, name, rank, tenured, ...)
```

SQL 자체는 조인 방향에 문법적 제약이 없지만, **실행 성능은 물리 설계에 강하게 묶여 있다.**

| 항목 | 그래프/온톨로지 | 관계형 테이블 중심 |
|---|---|---|
| 반대 방향 탐색 | 간선 하나를 뒤집어 읽음 (`<-[:teaches]-`) | FK 반대 방향을 쓰려면 **그 컬럼에 인덱스가 따로 있어야** 함 |
| 접근 경로 | 노드에서 인접 간선으로 포인터 추적 | 조인마다 인덱스 조회 + 매칭, 홉이 늘수록 조인 테이블 수 증가 |
| 질의 방향 추가 | 스키마 변경 없음 | 새 질의 패턴마다 **커버링 인덱스·조인 순서·통계**를 다시 튜닝 |
| 모델의 관점 | 관계가 1급 시민, 관점 중립 | 테이블 = 집합. "주 테이블이 무엇인가"를 질의마다 다시 정함 |

구체적으로: `enrollment(student_id, course_id)`에 `(student_id, semester)` 복합 인덱스만 만들어 두면
학생 중심 질의는 빠르지만, 교수 중심 질의(과목 → 수강생)는 `course_id`로 훑어야 하므로
`(course_id, semester)` 인덱스를 **추가로** 만들어야 한다. 인덱스가 늘면 쓰기 비용과 저장 비용이 붙는다.
게다가 4홉짜리 `Professor → Course → Enrollment → Student` 질의는 조인 순서가 바뀌면
실행 계획이 완전히 달라져서 옵티마이저 힌트나 통계 갱신에 의존하게 된다.

온톨로지에서는 이 튜닝 부담이 사라지는 것이 아니라 **모델 계층에서 사라진다.**
개념 모델은 하나로 유지하고, 방향별 최적화는 저장 엔진과 옵티마이저의 문제로 내려간다.

---

## 5. 중요한 단서 — 순회가 양방향이라고 카디널리티까지 대칭은 아니다

여기서 흔히 하는 오해가 있다. "양방향 순회 가능 = 두 질의의 비용이 같다"는 착각이다. **아니다.**

`teaches`는 1:N, `for_course`는 N:1, `enrolls_in`은 1:N이다.
방향을 뒤집으면 **팬아웃(fan-out) 크기가 통째로 달라진다.**

현실적인 규모를 넣어보자.

| 방향 | 홉별 확장 | 방문 노드 수 |
|---|---|---|
| 학생 → 교수 (A) | 학생 1 → 수강 5 → 과목 5 → 교수 최대 5 | **약 16개** |
| 교수 → 학생 (B) | 교수 1 → 과목 4 → 수강 4×200 → 학생 800 | **약 1,600개** |

- **(A) 학생 중심**은 좁은 방향이다. 한 학생의 학기당 수강은 4~6건으로 상한이 사실상 고정이라
  결과 집합이 작고 응답이 안정적이다.
- **(B) 교수 중심**은 넓은 방향이다. 대형 강의 하나가 200~500명이면 한 교수가 수백~수천 학생으로
  퍼진다. 페이지네이션, 집계로의 축약(`COUNT`, `AVG`), 조기 필터가 필요해진다.

```gql
-- 넓은 방향은 개별 행 대신 집계로 좁히는 편이 낫다
MATCH (p:Professor {professorId: 'P-77'})-[:teaches]->(c:Course)
      <-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.semester = '2026-Spring'
RETURN c.title, COUNT(e) AS enrolled, AVG(s.gpa) AS avg_gpa
ORDER BY enrolled DESC
```

### 실무 원칙

1. **선택도가 높은 쪽을 앵커로 잡아라.** 두 질의가 논리적으로 동치라도, 선택적인 끝점
   (예: `studentId`로 특정된 학생 1명, `tenured = true`로 걸러진 소수 교수)에서 시작하면
   중간 결과가 작게 유지된다. 옵티마이저가 대개 알아서 하지만, 다중 앵커일 때는 사람이 도와야 한다.
2. **필터를 늦추지 마라.** `WHERE e.semester = ...`, `WHERE e.grade IN ['C','D','F']` 같은 조건을
   팬아웃이 커지기 전 홉에 붙이면 방문 노드가 급감한다.
3. **넓은 방향은 결과 형태를 바꿔라.** 학생 목록 전체가 아니라 학생 수·평균 성적 같은 집계로 답하면
   같은 질문을 훨씬 싸게 처리할 수 있다.
4. **양방향 지원은 "모델의 대칭성"이지 "비용의 대칭성"이 아니다.**
   모델링 관점에서는 어느 쪽에서 물어도 되지만, 실행 계획은 방향마다 다르게 세워야 한다.

---

## 6. 왜 이게 온톨로지의 강점인가

전통적 시스템에서는 학생 포털(학생 중심 뷰)과 교원 시스템(교수 중심 뷰)이
서로 다른 스키마·다른 조인 전략·심지어 다른 데이터베이스로 갈라지기 쉽다.
그러면 같은 사실(“S-1001이 P-77의 CS-301에서 B를 받았다”)이 두 곳에 중복 표현되고
불일치가 생긴다.

온톨로지는 이 사실을 **간선 하나로 한 번만** 표현하고, 학생 포털과 교원 시스템은
같은 그래프에 서로 다른 출발점으로 질의할 뿐이다. 이것이 자료의 단일 출처(single source of truth)와
관점 독립성(perspective independence)을 동시에 얻는 방식이다.

같은 원리를 더 밀면 학습 경로 본문의 문장이 된다.
*"The graph now supports both student-centric and faculty-centric queries."*
그리고 Department를 허브로 추가하면 여기에 **부서 중심 질의**라는 세 번째 출발점이
스키마 변경 없이 그대로 얹힌다.

```gql
-- 세 번째 출발점: 부서 중심 — 역시 같은 그래프
MATCH (d:Department)-[:offers]->(c:Course)
      <-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

---

## 핵심 정리

- 관계의 **방향은 의미**를 담고, **순회는 양방향**이다. 화살표를 뒤집어 읽으면 된다.
- 그래서 **같은 그래프·같은 스키마**로 Student 중심 질의와 Professor 중심 질의를 모두 답할 수 있다.
  달라지는 건 앵커(출발점)뿐이다.
- 관계형 테이블 중심 설계에서는 질의 방향이 바뀔 때마다 **인덱스와 조인 순서를 새로 설계**해야 한다.
  온톨로지는 그 부담을 모델 계층에서 걷어낸다.
- 다만 **팬아웃은 방향마다 다르다.** 학생 → 교수는 좁고, 교수 → 학생은 넓다.
  양방향 순회 가능성과 양방향 성능 대칭성은 별개다.
