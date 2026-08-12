# Department — 조직 계층의 허브 엔티티

> **Q.** Department 엔티티는 대학 조직에서 어떤 역할을 하는가?
>
> **A.** 교수진을 소속시키고 강좌를 개설하며 학위를 수여하는 행정 단위다. 온톨로지에 조직 계층(organizational hierarchy)을 부여해 전체를 묶는다.

---

## 1. 왜 마지막에 Department를 추가하는가

이 학습 경로는 3단계로 온톨로지를 키운다.

| 단계 | 추가 엔티티 | 누적 | 핵심 개념 |
|---|---|---|---|
| 1 | Student, Course, Enrollment | 3 | junction 엔티티, M:N 해소 |
| 2 | Professor | 4 | 전이 질의, boolean 속성 |
| 3 | **Department** | **5** | **조직 계층, 허브 엔티티** |

2단계까지의 그래프는 **"누가 무엇을 배우고 누가 가르치는가"** 는 답할 수 있지만, **"그것이 누구의 책임이고 누구의 예산인가"** 는 답하지 못한다.

- Professor는 떠 있는 개인이다 — 어느 조직에 속하는지 모른다.
- Course는 떠 있는 과목이다 — 어느 프로그램의 일부인지 모른다.
- 따라서 **집계의 단위(grouping key)가 존재하지 않는다.** 전체 대학 통계 아니면 개별 인스턴스 통계뿐이고, 그 사이의 중간 층위가 없다.

Department는 이 빈 층위를 채운다. 학사 행정에서 실제로 예산을 쓰고, 사람을 채용하고, 커리큘럼을 승인하고, 학위 요건을 정하는 주체가 학과이기 때문에, 이 층위가 곧 **의사결정이 일어나는 단위**다. 온톨로지에서 집계 단위와 의사결정 단위가 일치하면 질의 결과가 그대로 행동으로 이어진다.

---

## 2. 엔티티 정의

| 속성 | 타입 | 식별자 |
|---|---|---|
| `departmentId` | string | ✓ |
| `name` | string | |
| `building` | string | |
| `budget` | float | |
| `headOfDept` | string | |

속성 하나하나가 "행정 단위"라는 성격을 드러낸다.

- `building` — **물리적 공간**의 배정 주체. "같은 건물을 쓰는 학과들" 같은 시설 질의를 가능하게 한다.
- `budget` — **자원 배분**의 주체. float인 이유는 금액이 연속량이고 비율 계산(교수 1인당 예산, 학생 1인당 예산)에 쓰이기 때문이다.
- `headOfDept` — **거버넌스**의 주체. 학과를 이끄는 교수를 가리킨다 (§5에서 따로 다룬다).

세 속성이 각각 공간·돈·사람을 담당한다는 점이 Department가 학문적 개념이 아니라 **행정 개념**임을 말해 준다. Student·Course·Enrollment가 "학문 활동"을 기술한다면, Department는 그 활동을 **떠받치는 조직 구조**를 기술한다.

---

## 3. 두 개의 아래 방향 연결 — `belongs_to` 와 `offers`

Department가 추가되면서 관계 두 개가 생긴다. 이 둘이 정확히 답의 "교수진을 소속시키고(belongs_to) 강좌를 개설한다(offers)"에 대응한다.

| 관계 | 방향 | 카디널리티 | 의미 |
|---|---|---|---|
| `belongs_to` | `Professor` → `Department` | many-to-one | 교수는 한 학과에 소속된다 |
| `offers` | `Department` → `Course` | one-to-many | 학과가 강좌를 개설한다 |

### 3.1 스키마 방향과 계층 방향은 반대일 수 있다

여기가 가장 헷갈리는 지점이다. **개념적으로는 둘 다 Department에서 아래로 뻗는 연결**인데, 스키마상 화살표 방향은 서로 반대다.

```
        ┌──────────────┐
        │  Department  │   ← 조직 계층의 꼭대기
        └──┬────────┬──┘
   belongs_to│(역방향) │offers (정방향)
           ▲ │        │ ▼
    ┌──────┴─┐      ┌─┴──────┐
    │Professor│      │ Course │
    └────┬───┘      └───▲────┘
         │  teaches     │
         └──────────────┘
```

- `offers`는 Department에서 **출발**한다 → 질의에서 정방향으로 탄다: `(d)-[:offers]->(c)`
- `belongs_to`는 Professor에서 **출발**해 Department로 들어온다 → 질의에서는 **역방향**으로 타야 한다: `(d)<-[:belongs_to]-(p)`

카디널리티가 방향을 결정했다. many-to-one 관계는 "many" 쪽에서 화살표를 쏘는 것이 자연스럽다 (교수 한 명은 학과 하나를 가리키는 외래키를 갖는다). 반대로 one-to-many인 `offers`는 "one" 쪽인 Department에서 쏜다.

> **핵심:** 계층에서의 위/아래는 **의미론**이고, 간선의 화살표는 **카디널리티**다. 둘은 일치할 수도 어긋날 수도 있다. 질의를 쓸 때는 항상 스키마상의 실제 방향을 확인하고, 필요하면 `<-[:rel]-`로 역방향 traversal을 해야 한다.

### 3.2 Department는 왜 "허브"인가

허브라는 말은 단순히 간선이 많다는 뜻이 아니라, **서로 다른 두 갈래를 한 노드가 이어 준다**는 뜻이다.

- 교원(faculty) 갈래: `Department ← Professor → Student` (advises)
- 교과(curriculum) 갈래: `Department → Course ← Enrollment ← Student`

Department 없이는 이 두 갈래가 `Professor -teaches-> Course` 하나로만 연결된다. Department가 들어오면 **인사 데이터와 커리큘럼 데이터를 같은 그룹 키로 묶어** 볼 수 있다. "종신교수 비율이 높은 학과가 실제로 학점도 높은가?" 같은, 두 갈래를 교차하는 질문이 이때 비로소 가능해진다.

### 3.3 Course에 도달하는 두 경로 — 그리고 그 불일치가 정보다

주의 깊게 보면 Department에서 Course로 가는 길이 **두 개**다.

1. `Department -offers-> Course` (행정적 개설 주체)
2. `Department <-belongs_to- Professor -teaches-> Course` (실제 강의 담당자의 소속)

정상적인 경우 두 경로의 결과는 대체로 겹친다. 그런데 **어긋나는 경우가 오히려 의미 있는 신호**다.

```gql
MATCH (p:Professor)-[:belongs_to]->(home:Department)
MATCH (p)-[:teaches]->(c:Course)<-[:offers]-(owner:Department)
WHERE home.departmentId <> owner.departmentId
RETURN p.name, home.name AS 소속, owner.name AS 개설학과, c.title
```

이것이 학습 경로의 *"Which professors teach outside their department's courses?"* 질의다. 결과는 교차 임용, 공동 개설(cross-listing), 강의 부담 전가 같은 조직 현실을 드러낸다. **두 경로를 모두 남겨 두었기 때문에** 이런 질문이 가능하다는 점이 중요하다. 만약 "교수 소속 = 강의 개설 학과"라고 단정하고 관계를 하나로 합쳤다면 이 정보는 영원히 사라진다.

### 3.4 "학위를 수여한다" — 서술에는 있고 모델에는 없는 것

답에는 학과의 역할로 학위 수여가 포함되지만, 5-엔티티 온톨로지에는 `Degree` 엔티티도 `grants` 관계도 없다. 현재 모델에서 학위와 가장 가까운 것은 `Student.major`라는 **string 속성**뿐이다.

이는 의도된 단순화이지만, 대가가 있다.

- `Student.major = "Computer Science"` 는 문자열이라 `Department.name` 과 **참조 무결성이 보장되지 않는다.** 오타나 표기 흔들림("CS" vs "Computer Science")이 그대로 통과한다.
- "전공 학과의 강좌를 몇 학점 들었는가" 같은 학위 요건 질의를 그래프로 탈 수 없다. 문자열 비교로 우회해야 한다.

확장한다면 `majors_in — Student → Department (many-to-one)` 관계를 추가하는 것이 자연스럽고, 학위 요건까지 다루려면 `Degree` 엔티티와 `grants — Department → Degree`, `requires — Degree → Course` 를 두는 것이 정석이다. **"현재 모델이 무엇을 못 하는가"를 아는 것이 모델을 아는 것의 절반이다.**

---

## 4. 학과 수준 집계 질의

Department의 실용적 가치는 대부분 여기서 나온다. 집계 질의는 형태적으로 이렇게 쓸 수 있다.

$$\text{agg}(d) = f\Big(\big\{\, x \;:\; d \rightsquigarrow x \,\big\}\Big)$$

즉 **학과에서 그래프를 타고 도달 가능한 집합을 모아 하나의 수치로 접는다.** Department는 이 접기 연산의 **그룹 키(grouping key)** 역할을 한다.

### 4.1 학습 경로가 제시하는 네 가지

| 질문 | 그래프 경로 | 집계 |
|---|---|---|
| 평균 학생 GPA가 가장 높은 학과는? | Department → Course ← Enrollment ← Student | `AVG(s.gpa)` |
| 학과별 수강률은? | Department → Course ← Enrollment | `COUNT(e) / c.maxEnrollment` |
| 종신교수가 가장 많은 학과는? | Department ← Professor (tenured=true) | `COUNT(p)` |
| 자기 학과 밖 과목을 가르치는 교수는? | 두 경로 비교 (§3.3) | 집합 차 |

### 4.2 대표 질의 — 학생들이 고전하는 학과 찾기

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

읽는 순서가 중요하다.

1. `(d:Department)-[:offers]->(c:Course)` — **정방향**. 학과가 개설한 과목으로 내려간다.
2. `(c)<-[:for_course]-(e:Enrollment)` — **역방향**. 그 과목을 향한 수강 기록을 끌어올린다.
3. `(e)<-[:enrolls_in]-(s:Student)` — **역방향**. 수강 기록의 주인 학생에 닿는다.

세 홉 중 두 홉이 역방향이다. 그래도 성립하는 이유는 그래프 질의가 간선을 양방향으로 탐색할 수 있기 때문이다. 그리고 필터 `e.grade IN [...]` 는 **중간 노드인 Enrollment의 속성**에 걸린다 — junction 엔티티를 만들어 둔 보상이 여기서 나온다.

### 4.3 집계에서 자주 틀리는 것들

**(1) 중복 계수(double counting).** 한 학생이 같은 학과 과목을 세 개 들으면 위 경로에서 Student 노드가 세 번 나온다. "학과별 수강생 수"를 구할 거라면 반드시 `COUNT(DISTINCT s)` 를 써야 한다. `COUNT(e)`(수강 건수)와 `COUNT(DISTINCT s)`(학생 수)는 **다른 질문에 대한 답**이다.

**(2) 평균의 단위.** "학과 평균 GPA"에서 `AVG(s.gpa)` 는 학생별 GPA를 평균한 값인데, 경로 중복 때문에 사실상 **수강 건수 가중 평균**이 된다. 학생 단위 평균을 원하면 먼저 학생을 dedup 해야 한다.

```gql
MATCH (d:Department)-[:offers]->(:Course)<-[:for_course]-(:Enrollment)<-[:enrolls_in]-(s:Student)
WITH d, COLLECT(DISTINCT s) AS students
RETURN d.name, SIZE(students) AS 학생수,
       REDUCE(t = 0.0, x IN students | t + x.gpa) / SIZE(students) AS 평균GPA
ORDER BY 평균GPA DESC
```

또한 `Student.gpa`는 이미 **전과목 누적 평균**이다. 특정 학과 과목만의 성취도를 보고 싶다면 학생의 gpa가 아니라 그 학과 Enrollment들의 `grade`를 환산해서 집계해야 한다. 미리 계산된 집계 속성을 다른 범위의 집계에 그대로 쓰면 조용히 틀린 숫자가 나온다.

**(3) 0건 학과의 소실.** 수강 기록이 하나도 없는 신설 학과는 위 패턴에서 아예 결과에 나타나지 않는다. "수강률 0%인 학과"를 찾는 것이 목적이라면 OPTIONAL MATCH(외부 조인)가 필요하다.

**(4) 비율은 정규화된 것을 쓴다.** 예산 총액이 큰 학과는 대개 규모도 크다. 학과 비교에는 절대량보다 정규화 지표가 낫다.

$$\text{교수 1인당 예산} = \frac{d.budget}{|\{p : p \xrightarrow{belongs\_to} d\}|}$$

```gql
MATCH (d:Department)<-[:belongs_to]-(p:Professor)
WITH d, COUNT(p) AS faculty, SUM(CASE WHEN p.tenured THEN 1 ELSE 0 END) AS tenured
RETURN d.name, faculty, tenured,
       1.0 * tenured / faculty AS 종신비율,
       d.budget / faculty      AS 교수1인당예산
ORDER BY 종신비율 DESC
```

이 질의는 `belongs_to` 를 **역방향**으로 타는 전형이다. 그리고 `d.budget` 은 Department 자신의 속성이므로 추가 홉 없이 바로 쓸 수 있다 — 허브 노드에 집계에 쓸 스칼라 속성을 붙여 두는 것이 유용한 이유다.

---

## 5. `headOfDept` — 자기 참조 패턴

`headOfDept`는 이 온톨로지에서 가장 흥미로운 속성이다. **학과장은 교수이고, 그 교수는 다시 그 학과에 속한다.**

### 5.1 무엇이 "자기 참조"인가

엄밀히 말하면 Department가 Department를 가리키는 것이 아니라, **Professor → Department → Professor 로 닫히는 사이클**이다.

```
Professor ──belongs_to──▶ Department
    ▲                          │
    └────── headOfDept ────────┘   (개념상의 역방향 간선)
```

조직도에서 흔한 구조다. "관리자도 결국 조직의 구성원"이라는 사실이 그래프에서는 **사이클**로 나타난다. 순수한 자기 참조(예: `Course.prerequisite → Course`, `Department.parentDepartment → Department`)와 구분해서, 이런 형태는 **두 엔티티를 오가는 상호 참조 사이클**이라 부르는 편이 정확하다.

### 5.2 문자열로 둔 것의 대가

학습 자료의 정의에서 `headOfDept`의 타입은 **string**이다. 관계가 아니라 속성으로 모델링되어 있다.

| 항목 | string 속성 | 관계 `headed_by → Professor` |
|---|---|---|
| 참조 무결성 | 없음 — 존재하지 않는 교수 ID도 저장된다 | 그래프가 보장 |
| 그래프 탐색 | 불가 — 별도 lookup 필요 | `(d)-[:headed_by]->(p)` 로 traversal |
| 학과장의 속성 조회 | 불가 (rank, tenured 등) | 자유롭게 접근 |
| 교수 삭제 시 | dangling reference 발생 | 간선 정리로 처리 |
| 구현 난이도 | 낮음 | 사이클 처리 필요 |

즉 `headOfDept`를 문자열로 두는 순간 **"학과장이 종신교수인 학과는?"** 을 그래프 질의로 풀 수 없다. 관계로 승격하면 이렇게 된다.

```gql
MATCH (d:Department)-[:headed_by]->(head:Professor)
WHERE head.tenured = false
RETURN d.name, head.name, head.rank
```

한 걸음 더 나아가면 **학과장이 자기 학과 소속인지** 검증하는 무결성 질의도 쓸 수 있다.

```gql
MATCH (d:Department)-[:headed_by]->(head:Professor)
WHERE NOT (head)-[:belongs_to]->(d)
RETURN d.name AS 이상한학과, head.name AS 학과장
```

이 사이클 제약 — "학과장은 반드시 그 학과 소속이어야 한다" — 은 문자열 속성으로는 표현조차 되지 않는다. 튜토리얼이 string으로 둔 것은 5-엔티티 규모를 유지하려는 교육적 단순화이고, 실제 시스템이라면 관계로 올리는 것이 옳다.

### 5.3 자기 참조·사이클을 다룰 때의 주의점

1. **탐색 시 사이클 감지가 필수다.** `Department → Professor → Department → …` 로 무한히 돌 수 있으므로 방문 노드 집합을 유지하거나 홉 수 상한을 둔다.
2. **생성 순서 문제(닭과 달걀).** 학과를 만들려면 학과장이 있어야 하고 교수를 등록하려면 학과가 있어야 한다. 해법은 `headOfDept`를 **nullable**로 두고 나중에 채우는 것이다.
3. **역할과 정체성을 구분한다.** "학과장"은 사람의 속성이 아니라 **임기가 있는 역할**이다. 이력을 남겨야 한다면 `HeadTerm(startDate, endDate)` 같은 junction 엔티티로 승격해야 한다 — Enrollment가 Student–Course 사이에서 한 것과 똑같은 패턴이다.
4. **계층 확장.** 실제 대학은 College → Department → Division 처럼 여러 층이다. 이때 `parentDepartment → Department` 라는 **진짜 자기 참조**가 등장하고, 학과 수준 집계는 하위 조직까지 재귀적으로 합산하는 문제(재귀 CTE / 가변 길이 경로 `-[:parent*]->`)로 바뀐다.

---

## 6. 자주 하는 오해

| 오해 | 사실 |
|---|---|
| Department가 허브인 이유는 속성이 가장 많아서 | 아니다. Professor(교원)와 Course(교과) 두 갈래에 동시에 닿기 때문이다 |
| Department가 허브인 이유는 마지막에 추가돼서 | 순서와 무관하다. 연결 구조의 문제다 |
| `belongs_to`가 Department에서 나가는 간선이다 | 아니다. Professor → Department (many-to-one)이라 질의에서는 역방향으로 탄다 |
| Department는 Student와 직접 연결된다 | 직접 간선은 없다. Course/Enrollment 또는 Professor를 경유하는 전이 질의로만 닿는다 |
| `headOfDept`로 학과장의 종신 여부를 바로 질의할 수 있다 | 못 한다. 현재는 string 속성이라 그래프를 탈 수 없다 |
| 학위 수여가 모델에 표현되어 있다 | 없다. 서술상의 역할일 뿐, `Degree` 엔티티는 존재하지 않는다 |
| 학과별 학생 수는 `COUNT(s)`면 된다 | 경로 중복 때문에 `COUNT(DISTINCT s)` 여야 한다 |

---

## 7. 핵심 요약

1. Department는 **행정 단위**다 — 교수진 소속(`belongs_to`), 강좌 개설(`offers`), 학위 수여를 담당한다.
2. 속성 `building`(공간) · `budget`(자원) · `headOfDept`(거버넌스)가 그 행정적 성격을 그대로 드러낸다.
3. **두 개의 아래 방향 연결**이 핵심이다. 다만 `offers`는 정방향, `belongs_to`는 many-to-one이라 질의에서 **역방향**으로 탄다 — 계층의 위/아래와 화살표 방향은 별개다.
4. Course로 가는 경로가 `offers` 와 `belongs_to + teaches` 두 갈래이고, **둘의 불일치**가 교차 임용·공동 개설을 드러내는 신호다.
5. Department는 **집계의 그룹 키**다. 평균 GPA, 수강률, 종신교수 비율, 교수 1인당 예산이 모두 이 층위에서 계산된다.
6. 집계에서는 **중복 계수(`DISTINCT`)**, **평균의 단위**, **0건 학과 소실**, **규모 정규화**를 늘 확인한다.
7. `headOfDept`는 Professor–Department **사이클**을 만드는 자기 참조 패턴이다. 현재는 string이라 참조 무결성도 그래프 탐색도 없다 — 관계로 승격하면 "학과장이 종신교수인가", "학과장이 그 학과 소속인가"까지 질의할 수 있다.
8. 학위 요건, 다층 조직(College → Department), 학과장 임기 이력은 모두 이 5-엔티티 모델의 **의도된 공백**이며, 확장 방향이기도 하다.
