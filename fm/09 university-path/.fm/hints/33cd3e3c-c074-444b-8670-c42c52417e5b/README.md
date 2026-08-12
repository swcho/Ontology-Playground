# "정년보장 교수의 강좌를 듣는 학생은?" — 전이적 질의(transitive query) 경로

## 정답 요약

**Professor → Course → Enrollment → Student** 경로를 순회한다.
Professor와 Student 사이에는 이 질문에 맞는 직접 관계가 없지만, **Course와 Enrollment라는 중간 노드**를 거치면 연결된다. 이것이 그래프 기반 온톨로지의 핵심 강점인 *전이적 질의(transitive query)* 다.

---

## 1. University 온톨로지의 관계 지도

완성된 모델은 5 엔티티(Student, Course, Enrollment, Professor, Department), 6 관계다. 이 질문에 관여하는 관계는 다음 세 개.

| 관계 이름 | 선언 방향 | 카디널리티 | 의미 |
|---|---|---|---|
| `teaches` | `Professor` → `Course` | one-to-many | 교수는 한 학기에 하나 이상의 강좌를 가르친다 |
| `for_course` | `Enrollment` → `Course` | many-to-one | 각 수강 기록은 하나의 특정 강좌에 대한 것 |
| `enrolls_in` | `Student` → `Enrollment` | one-to-many | 한 학생은 여러 학기에 걸쳐 여러 수강 기록을 가진다 |

여기에 이 질문에는 쓰이지 **않는** 관계가 하나 더 있다.

| 관계 이름 | 선언 방향 | 의미 |
|---|---|---|
| `advises` | `Professor` → `Student` | 교수가 학생의 지도교수(어드바이저)를 맡는다 |

---

## 2. 홉 단위로 본 경로와 화살표 방향

질문은 Professor에서 출발해 Student로 도착한다. 그런데 **논리적 진행 방향과 관계의 선언 방향이 매 홉마다 같지는 않다.** 이 점이 이 카드의 핵심 함정이다.

| 홉 | 논리적 진행 | 사용 관계 | 선언 방향 | 순회 방향 |
|---|---|---|---|---|
| 1 | Professor → Course | `teaches` | Professor → Course | **정방향** (화살표를 따라감) |
| 2 | Course → Enrollment | `for_course` | Enrollment → Course | **역방향** (화살표를 거슬러 올라감) |
| 3 | Enrollment → Student | `enrolls_in` | Student → Enrollment | **역방향** (화살표를 거슬러 올라감) |

그래서 학습 자료는 같은 경로를 화살표까지 살려 이렇게도 표기한다.

```
Professor -[:teaches]-> Course <-[:for_course]- Enrollment <-[:enrolls_in]- Student
```

즉 `Professor → Course → Enrollment → Student`는 **탐색 순서**를 적은 것이고, `Professor → Course ← Enrollment ← Student`는 **관계의 실제 화살표 방향**을 적은 것이다. 둘은 같은 경로를 다른 관점에서 쓴 표현이므로 어느 쪽으로 외워도 되지만, "Course와 Enrollment 사이 화살표는 Enrollment 쪽에서 나간다"는 사실은 반드시 기억해야 한다.

왜 그런가? Enrollment가 **접합 엔티티(junction entity)** 이기 때문이다. Student–Course의 다대다 관계를 풀기 위해 그 사이에 끼워 넣은 노드이므로, 화살표가 양쪽 끝(Student, Course)이 아니라 **가운데 Enrollment에서 바깥으로**... 정확히는 Student가 Enrollment를 향하고 Enrollment가 Course를 향하는 형태가 된다. 결과적으로 Professor 쪽에서 출발하면 두 번째 홉부터 계속 역방향 순회가 된다.

---

## 3. `tenured = true` 필터는 어디에 걸리는가

**출발 노드인 Professor에 건다.** `tenured`는 Professor 엔티티의 boolean 속성이기 때문이다.

| 엔티티 | 속성 | 타입 |
|---|---|---|
| Professor | `professorId` (식별자), `name`, `rank`, **`tenured`**, `officeHours` | boolean |

- `tenured`는 Course의 속성이 아니다 → 강좌에 필터를 걸 수 없다.
- `tenured`는 Enrollment나 Student의 속성도 아니다 → 경로 뒤쪽에서는 참조 불가.
- 따라서 필터 위치는 **0번째 홉, 경로의 맨 앞**이며, 그래프 엔진 입장에서도 여기서 걸어야 탐색 시작 집합이 가장 작아져 효율적이다. (정년보장 교수만 시드로 삼고 그 아래로 펼치는 방식)

혼동하기 쉬운 다른 필터 위치를 대조해 두면 좋다.

| 조건 | 걸리는 노드 | 속성 |
|---|---|---|
| 정년보장 교수 | Professor | `tenured = true` |
| 400 레벨 강좌 | Course | `level = '400'` |
| 이번 학기 수강 | Enrollment | `semester = '2026-Spring'` |
| C 미만 성적 | Enrollment | `grade IN ['C','D','F']` |
| GPA 3.5 이상 학생 | Student | `gpa >= 3.5` |

특히 **성적·학기 조건은 Student가 아니라 Enrollment에 붙는다**는 점을 함께 기억하자. 접합 엔티티를 둔 이유 자체가 "관계 자체에 붙는 속성"을 담기 위해서다.

---

## 4. GQL 예시

### 4-1. 기본형 — 정년보장 교수의 강좌를 듣는 학생

```gql
MATCH (p:Professor)-[:teaches]->(c:Course)
      <-[:for_course]-(e:Enrollment)
      <-[:enrolls_in]-(s:Student)
WHERE p.tenured = true
RETURN DISTINCT s.studentId, s.name, s.major
```

- `WHERE p.tenured = true` — 필터가 경로 맨 앞 Professor에 걸려 있음에 주목.
- `DISTINCT`가 필요한 이유: 한 학생이 같은 교수의 여러 강좌를 듣거나 여러 학기에 걸쳐 수강하면 Enrollment가 여러 건이라 학생이 중복 반환된다.

### 4-2. 어떤 교수의 어떤 강좌인지까지 보기

```gql
MATCH (p:Professor)-[:teaches]->(c:Course)
      <-[:for_course]-(e:Enrollment)
      <-[:enrolls_in]-(s:Student)
WHERE p.tenured = true
  AND e.status = 'active'
RETURN p.name AS professor,
       c.title AS course,
       e.semester AS semester,
       s.name AS student
ORDER BY professor, course
```

중간 노드를 `RETURN`에 함께 노출하면 경로가 실제로 어떻게 이어졌는지 검증할 수 있다.

### 4-3. 집계로 확장 — 정년보장 교수 강좌의 평균 GPA

```gql
MATCH (p:Professor)-[:teaches]->(c:Course)
      <-[:for_course]-(e:Enrollment)
      <-[:enrolls_in]-(s:Student)
WHERE p.tenured = true
RETURN p.name AS professor,
       COUNT(DISTINCT s) AS student_count,
       AVG(s.gpa) AS avg_gpa
ORDER BY avg_gpa DESC
```

### 4-4. Department까지 한 홉 더 — 허브 엔티티 붙이기

```gql
MATCH (d:Department)<-[:belongs_to]-(p:Professor)-[:teaches]->(c:Course)
      <-[:for_course]-(e:Enrollment)
      <-[:enrolls_in]-(s:Student)
WHERE p.tenured = true
RETURN d.name AS department,
       COUNT(DISTINCT s) AS students_taught_by_tenured
ORDER BY students_taught_by_tenured DESC
```

`belongs_to`는 `Professor → Department` (many-to-one)이므로 Department에서 출발하면 역방향(`<-[:belongs_to]-`)이 된다.

---

## 5. `advises`로 답하면 왜 틀리는가

`advises`는 `Professor → Student` 방향의 **직접 관계**다. 한 홉이면 끝나므로 훨씬 간단해 보이고, 그래서 오답으로 고르기 쉽다.

```gql
-- 이건 "정년보장 교수가 지도하는 학생은?"에 대한 답이다
MATCH (p:Professor)-[:advises]->(s:Student)
WHERE p.tenured = true
RETURN s.studentId, s.name
```

**질문이 달라지는 지점:**

| 구분 | `teaches` 경로 | `advises` 경로 |
|---|---|---|
| 답하는 질문 | 그 교수의 **강좌를 수강하는** 학생 | 그 교수가 **지도(어드바이징)하는** 학생 |
| 홉 수 | 3홉 (Course, Enrollment 경유) | 1홉 (직접) |
| 관계의 의미 | 교육 활동 / 강의실 관계 | 학사 지도 / 멘토링 관계 |
| 중간 노드 | Course, Enrollment | 없음 |
| 학기·성적 정보 | Enrollment에 있으므로 활용 가능 | 접근 경로 없음 |

두 집합은 **거의 겹치지 않을 수도 있다.** 지도교수는 보통 학생의 전공 소속을 기준으로 배정되므로, 지도학생이 그 교수의 강의를 한 번도 안 들었을 수 있다. 반대로 교양·필수 과목을 가르치는 교수의 수강생 수백 명 중 지도학생은 서너 명뿐일 수 있다.

또한 `advises`로는 "언제, 어떤 과목에서, 어떤 성적으로"를 전혀 답할 수 없다. 그 정보는 전부 Enrollment 접합 엔티티에 들어 있고, `advises` 경로는 Enrollment를 지나가지 않기 때문이다.

정리하면, **직접 관계가 존재한다고 해서 그것이 질문에 맞는 관계인 것은 아니다.** 온톨로지에서 경로를 고를 때는 "몇 홉으로 갈 수 있는가"가 아니라 "이 관계의 의미가 질문의 의미와 일치하는가"를 먼저 따져야 한다.

---

## 6. 기억할 핵심

1. 경로는 **Professor → Course → Enrollment → Student**. 관계 이름은 순서대로 `teaches`, `for_course`(역방향), `enrolls_in`(역방향).
2. `tenured = true`는 **Professor 노드**에 건다. boolean 속성은 이렇게 범주형 필터로 쓰인다.
3. Enrollment는 접합 엔티티라 화살표가 `Student → Enrollment → Course`로 나가므로, Professor 쪽에서 출발하면 뒤쪽 두 홉은 역방향 순회다.
4. 직접 관계가 없어도 **중간 노드를 경유해 연결**할 수 있다는 것이 전이적 질의의 정의이자 그래프 온톨로지의 강점이다.
5. `advises`는 지도 관계로, "수강" 질문이 아니라 "지도" 질문에 답한다. 홉 수가 적다는 이유로 고르면 안 된다.
