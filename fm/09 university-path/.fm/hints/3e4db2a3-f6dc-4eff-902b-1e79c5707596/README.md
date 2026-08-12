# 학사 코어(Academic Core) 단계의 3가지 교훈

> **Q.** 학사 코어 단계에서 배우는 3가지 교훈은?
>
> **A.** junction entity가 속성 있는 다대다를 해소한다는 것, float 속성(GPA)이 집계·임계값 질의를 가능하게 한다는 것, integer 속성(credits·maxEnrollment)이 정원·수업량 계획을 가능하게 한다는 것이다.

---

## 0. 학사 코어 단계란?

University System 학습 경로는 3단계로 엔티티를 쌓아 올린다.

| 단계 | 추가 엔티티 | 누적 | 핵심 개념 |
|---|---|---|---|
| 1. **학사 코어(Academic Core)** | Student, Course, Enrollment | 3 | junction entity, 다대다 |
| 2. 교수진(Faculty) | Professor | 4 | 전이적 질의, boolean 속성 |
| 3. 완성 모델 | Department | 5 | 조직 계층, 허브 엔티티 |

학사 코어는 "**어떤 학생이 어떤 과목을 듣고, 성적은 어떠한가**"라는 단 하나의 질문에 답하기 위한 최소 구성이다. 이 단계에서 얻는 교훈은 아래 세 가지(원문의 네 번째 항목 "학사 코어는 Student → Enrollment → Course 순서를 따른다"는 구조 요약에 가깝다)이다.

---

## 1. Junction entity가 "속성을 가진 다대다"를 해소한다

### 문제 상황

- 한 학생은 여러 과목을 듣는다.
- 한 과목은 여러 학생을 받는다.
- 즉 Student ↔ Course 는 **다대다(many-to-many)** 이다.

그런데 이 연결에는 연결 그 자체에만 속하는 정보가 붙는다.

- `grade` (성적): 학생의 속성도, 과목의 속성도 아니다. "이 학생이 이 과목에서" 받은 값이다.
- `semester` (학기): 같은 학생·같은 과목이라도 재수강하면 값이 달라진다.
- `status` (수강 상태: 수강중/철회/완료 등)

Student에 `grade`를 두면 "어느 과목의 성적인가"를 표현할 수 없고, Course에 두면 "누구의 성적인가"를 표현할 수 없다. 관계 자체가 속성을 가져야 한다.

### 해법: 연결을 1급 엔티티로 승격

**Enrollment(수강신청)** 라는 엔티티를 사이에 끼워 넣어 다대다를 두 개의 일대다/다대일로 분해한다.

```
Student --enrolls_in(1:N)--> Enrollment --for_course(N:1)--> Course
```

| Enrollment 속성 | 타입 | 식별자 |
|---|---|---|
| `enrollmentId` | string | ✓ |
| `semester` | string | |
| `grade` | string | |
| `enrollDate` | date | |
| `status` | string | |

- **enrolls_in** — Student → Enrollment (일대다). 학생은 여러 학기에 걸쳐 여러 수강 기록을 가진다.
- **for_course** — Enrollment → Course (다대일). 하나의 수강 기록은 정확히 하나의 과목을 향한다.

### 왜 중요한가

- 관계형 DB의 조인 테이블과 발상은 같지만, 온톨로지에서는 Enrollment가 **조회·질의 가능한 1급 노드**가 된다. 자체 식별자(`enrollmentId`)를 갖고, 다른 엔티티가 이를 참조할 수도 있다.
- "이 학생이 이번 학기에 이 과목에서 받은 성적은?" 처럼 **연결 위의 속성**을 조건으로 거는 질의가 가능해진다.
- 나중에 Department가 추가되면 Enrollment는 전이 경로의 중간 허브가 된다.
  ```gql
  MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
  WHERE e.grade IN ['C', 'D', 'F']
  RETURN d.name, c.title, COUNT(e) AS struggling_count
  ORDER BY struggling_count DESC
  ```
- 학습 경로 퀴즈의 정답 근거도 동일하다: "Enrollment는 어느 한쪽 엔티티에 속하지 않는 자기 자신의 속성(grade, semester, status)을 지니기 때문"이다. 노드 수를 늘리려는 것도, 엔티티가 3개 이상이어야 한다는 규칙 때문도 아니다.

> **일반 규칙:** 두 엔티티가 다대다이고 **그 연결에 속성이 붙는다면** junction entity를 만든다. 온톨로지 설계에서 가장 흔히 쓰이는 패턴이다.

---

## 2. Float 속성(GPA)이 집계 계산과 임계값 질의를 가능하게 한다

### Student 엔티티

| 속성 | 타입 | 식별자 |
|---|---|---|
| `studentId` | string | ✓ |
| `name` | string | |
| `gpa` | float | |
| `enrollmentYear` | integer | |
| `major` | string | |

`gpa`는 0.0 ~ 4.0 범위의 **float**이다. 정수로는 3.75 같은 값을 표현할 수 없고, 문자열로 두면 비교·평균이 불가능하다.

### float이 열어주는 질의 유형

- **집계(aggregate)**: 학과별 평균 GPA, 전공별 GPA 분포. 완성 모델의 "어느 학과의 평균 학생 GPA가 가장 높은가?"가 `Department → Course ← Enrollment ← Student (avg GPA)` 경로로 풀린다.
- **임계값(threshold)**: "GPA ≥ 3.5인 우등생 명단", "GPA < 2.0인 학사경고 대상" 같은 부등호 필터. 학업 성취도(academic standing) 판정이 여기 해당한다.
- **정렬·순위**: ORDER BY, 상위 N명 추출.

핵심은 타입 선택이 곧 **질의 능력의 선택**이라는 점이다. 같은 값이라도 float으로 모델링해야 평균·비교·구간 필터가 성립한다.

> 참고: 같은 원리가 완성 단계 Department의 `budget`(float)에도 적용된다 — 예산 기반 자원 배분 질의가 가능해진다.

---

## 3. Integer 속성(credits, maxEnrollment)이 정원·수업량 계획을 가능하게 한다

### Course 엔티티

| 속성 | 타입 | 식별자 |
|---|---|---|
| `courseId` | string | ✓ |
| `title` | string | |
| `credits` | integer | |
| `level` | string | |
| `maxEnrollment` | integer | |

- **`credits` (학점, integer)** — 수업량(workload) 계획의 단위. "이번 학기 총 이수 학점", "졸업 요건 120학점 충족 여부", "학생별 학기 평균 이수 학점" 같은 합산 질의를 가능하게 한다.
- **`maxEnrollment` (정원, integer)** — 수용 능력(capacity) 계획의 단위. 실제 수강 인원(Enrollment 개수)과 대비해 충원율을 계산할 수 있다. 완성 모델의 "학과별 수강 충원율"이 바로 `Department → Course ← Enrollment (count) / Course.maxEnrollment` 로 표현된다.
- 참고로 **`level`**(100/200/300/400)은 값이 숫자처럼 보이지만 **string**으로 모델링되어 있다. 난이도·선수과목 체계를 나타내는 범주형 라벨이지 산술 대상이 아니기 때문이다. "숫자처럼 생겼다고 전부 숫자 타입이 아니다"는 대비 사례로 기억해 두면 좋다.

---

## 4. 한 줄 요약과 암기 포인트

| 교훈 | 대표 속성/엔티티 | 열리는 질의 |
|---|---|---|
| junction entity가 속성 있는 다대다를 해소 | Enrollment (grade, semester, status) | "이 학생이 이 학기 이 과목에서 받은 성적은?" |
| float 속성이 집계·임계값 질의를 가능하게 함 | Student.gpa | 평균 GPA, GPA ≥ 3.5 우등생 |
| integer 속성이 정원·수업량 계획을 가능하게 함 | Course.credits, Course.maxEnrollment | 총 이수 학점, 충원율 |

암기 팁: **"연결(Enrollment) → 소수(float) → 정수(integer)"** 순서. 먼저 구조(다대다 해소), 그다음 타입 선택이 만들어내는 질의 능력(연속값 집계 / 개수·용량 계획)이라는 흐름으로 기억한다.

혼동 주의: `tenured`(boolean, 범주형 필터)와 **전이적 질의(transitive query)** 는 학사 코어가 아니라 **교수진(Faculty) 단계**의 교훈이고, 조직 계층·허브 엔티티는 **완성 모델(Department) 단계**의 교훈이다.
