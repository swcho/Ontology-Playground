# Professor(2단계) 추가에서 얻는 학습 포인트

## 질문

Professor 추가 단계에서 얻는 학습 포인트는?

## 정답

**boolean 속성(`tenured`)이 예/아니오 범주 필터를 만든다**는 것, **transitive query(이행적 질의)가 먼 엔티티를 잇는다**는 것, **학문적 rank가 정해진 위계를 따른다**는 것이다. 그 결과 이제 **학생 중심(student-centric)·교수 중심(faculty-centric) 질의가 모두** 가능해진다.

> 원문 "Faculty" 문서의 **What we learned** 네 줄을 그대로 옮긴 것이다. 항목이 4개(속성 3 + 결과 1)라는 점을 기억하면 빠뜨리지 않는다.

---

## 1. 왜 Professor를 추가하는가

1단계에서 만든 학사 코어는 "누가 무엇을 듣고 몇 점을 받았나"까지만 답한다. 여기서 빠진 질문이 **"그 강좌는 누가 가르치는가?"**다. Professor 엔티티는 이 **teaching dimension(교육 차원)**을 추가하고, 교수를 강좌에 — 그리고 **이행적으로(transitively)** 학생에게까지 — 연결한다.

Professor 추가로 새로 가능해지는 질문(원문 예시):

- "400 레벨 강좌를 가장 많이 가르치는 교수는?"
- "Smith 교수 강좌의 평균 GPA는?"
- "정년보장(tenured) 교수 중 입문 강좌를 가르치는 사람은?"

## 2. Professor 엔티티 스펙

| Property | Type | Identifier? | 메모 |
|---|---|---|---|
| `professorId` | string | ✓ | 식별자 |
| `name` | string | | |
| `rank` | string | | Assistant → Associate → Full 위계 |
| `tenured` | **boolean** | | 정년보장 여부 (예/아니오) |
| `officeHours` | string | | 오피스아워 |

여기서 **`tenured`가 이 경로 전체에서 처음 등장하는 boolean 타입**이라는 점이 핵심이다. 1단계는 string / float / integer / date 만 썼다.

## 3. 새 관계 2개

| 관계 | 방향 | 카디널리티 | 의미 |
|---|---|---|---|
| `teaches` | Professor → Course | 1:N | 한 교수가 학기당 하나 이상의 강좌를 가르친다 |
| `advises` | Professor → Student | 1:N | 교수가 자기 프로그램의 학생을 지도한다 |

`advises`는 Course를 거치지 않고 Professor와 Student를 **직접** 잇는다는 점에서 `teaches`와 성격이 다르다. 즉 Professor는 학생에게 도달하는 경로를 **두 개**(직접 지도 / 강좌 경유) 갖게 된다.

## 4. 학습 포인트 세 가지 깊이 보기

### (1) Boolean 속성 → 예/아니오 범주 필터

`tenured: boolean`은 값이 두 개(true/false)뿐이라 데이터를 **깔끔한 두 범주로 자른다**. 임계값을 정할 필요가 없다는 점이 float(GPA)나 integer(credits)와 다르다.

| 타입 | 예시 | 필터 방식 |
|---|---|---|
| float | `gpa` | 임계값 비교 (`gpa >= 3.5`) — 기준선을 사람이 정해야 함 |
| integer | `credits`, `maxEnrollment` | 범위·집계 (용량 계획) |
| string(범주) | `rank`, `level` | 열거값 매칭, 순서는 별도 정의 필요 |
| **boolean** | **`tenured`** | **`= true` / `= false`, 이분 분할이 즉시 확정** |

활용 예: `Department ← Professor (tenured=true, count)` — "정년보장 교수가 가장 많은 학과"는 boolean 하나로 곧장 집계된다.

### (2) Transitive query(이행적 질의) → 먼 엔티티를 잇기

Professor와 Student 사이에는 (advises를 빼면) **직접 관계가 없다.** 그런데도 다음 경로로 연결된다.

```
Professor → Course ← Enrollment ← Student
   teaches      for_course    enrolls_in
```

이렇게 **중간 노드를 경유해 직접 연결이 없는 엔티티끼리 답을 만드는 것**이 이행적 질의다. 대표 질문: *"정년보장 교수의 강좌를 듣는 학생은 누구인가?"* → boolean 필터(`tenured=true`) + 3홉 순회의 조합.

원문 표현: *"Transitive queries are one of the greatest strengths of graph-based ontologies."* 그래프 온톨로지가 관계형 조인 대비 갖는 강점이 바로 이 다중 홉 순회다.

퀴즈에서 나오는 오답 보기와 구분:
- ❌ 단일 엔티티의 속성 조회 → 이행적 아님(0홉)
- ❌ ID로 교수 한 명 찾기 → 룩업
- ❌ 강좌 개수 세기 → 단순 집계
- ✅ **Professor → Course → Enrollment → Student 순회** → 이행적 질의

### (3) Academic rank → 정해진 위계(defined hierarchy)

`rank`는 타입은 string이지만 값에 **순서**가 있다.

```
Assistant  →  Associate  →  Full
(조교수)      (부교수)      (정교수)
```

즉 단순 라벨이 아니라 **순서형(ordinal) 범주**다. "부교수 이상", "승진 대상" 같은 질의가 성립하려면 이 순서가 모델 지식으로 존재해야 한다. 여기서 주의할 점: **rank는 hierarchy(값의 위계)이고, 3단계 Department의 hierarchy는 organizational hierarchy(엔티티 간 조직 계층)**다. 이름은 같은 "위계"지만 층위가 완전히 다르다 — 아래 대비표 참조.

### (4) 결과: 양방향 질의 가능

Professor가 붙기 전 그래프는 Student에서 출발하는 질의만 자연스러웠다. 이제는

- **학생 중심(student-centric)**: "이 학생은 어떤 강좌를, 누구에게 배우는가?"
- **교수 중심(faculty-centric)**: "이 교수의 강좌 수강생 성적 분포는?"

두 방향 모두 같은 그래프에서 성립한다. 이것이 "이제 학생 중심·교수 중심 질의 모두가 가능해진다"의 의미다.

## 5. ★ 단계별 교훈 대비표 (헷갈리지 않기)

이 경로는 3단계 모두 "What we learned"를 갖는다. **어떤 교훈이 어느 단계 것인지**가 시험 포인트다.

| | **1단계 — 학사 코어** | **2단계 — Professor (이 카드)** | **3단계 — Department** |
|---|---|---|---|
| 추가 엔티티 | Student, Course, Enrollment | **+ Professor** | + Department |
| 누적 엔티티 수 | 3 | **4** | 5 |
| 추가 관계 | `enrolls_in`, `for_course` | **`teaches`, `advises`** | `belongs_to`, `offers` |
| 대표 패턴 | **Junction entity(정션 엔티티)** | **Transitive query(이행적 질의)** | **Hub entity(허브 엔티티)** |
| 강조 데이터 타입 | **float**(gpa), **integer**(credits, maxEnrollment) | **boolean**(tenured) | **float**(budget) |
| "위계"의 의미 | (없음) | **값의 위계** — rank: Assistant→Associate→Full | **조직 계층** — Department가 Professor·Course를 조직 |
| 핵심 한 줄 | 다대다 + 속성 → 관계를 일급 엔티티로 승격 | 중간 노드를 거쳐 먼 엔티티를 연결 | 두 갈래(교수/커리큘럼)를 묶는 집계 기준점 |
| 가능해지는 질의 | Student → Enrollment → Course | 학생 중심 + **교수 중심** | **학과 단위 집계(department-level statistics)** |

### 자주 틀리는 3가지 혼동

1. **"boolean 속성" ↔ 1단계 "float/integer 속성"**
   1단계 교훈은 *float(GPA)가 집계·임계값을 가능하게 하고, integer(credits/maxEnrollment)가 용량·부하 계획을 가능하게 한다*였다. boolean(tenured)은 **2단계**다.
2. **"위계(hierarchy)" 두 종류**
   2단계 = `rank` **값**의 위계(Assistant→Associate→Full). 3단계 = Department라는 **조직**의 계층. "hierarchy가 나왔으니 Department"라고 반사적으로 답하면 틀린다.
3. **"transitive query" ↔ 3단계 "hub entity"**
   이행적 질의는 **경로를 여러 홉 순회하는 기법**(2단계 도입). 허브 엔티티는 **여러 가지에 동시에 연결된 노드의 위치적 성격**(3단계, Department). 3단계의 긴 GQL 예시가 이행적이긴 하지만, **개념이 처음 명시된 곳은 2단계**다.

## 6. 암기용 압축

> **Professor = boolean + 이행 + rank위계 → 양방향 질의**

- **b**oolean (`tenured`) → 예/아니오 필터
- **t**ransitive (`Professor → Course → Enrollment → Student`) → 먼 엔티티 연결
- **r**ank (Assistant→Associate→Full) → 정해진 위계
- 결과 → student-centric **and** faculty-centric

## 7. 참고 GQL 감각 잡기

이 단계에서 새로 성립하는 전형적 질의 형태(2단계 관계만 사용):

```gql
MATCH (p:Professor)-[:teaches]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE p.tenured = true
RETURN p.name, c.title, s.name
```

`p.tenured = true`가 **boolean 범주 필터**, `-[:teaches]->…<-[:enrolls_in]-` 3홉이 **이행적 질의**다. 한 쿼리 안에 이 단계의 교훈 두 개가 동시에 들어 있다.
