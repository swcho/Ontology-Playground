# University 학습 경로의 4가지 핵심 개념

## 질문

University 학습 경로가 다루는 4가지 핵심 개념은?

## 답

1. **junction entity** — Enrollment로 Student–Course 다대다 관계를 해소
2. **학사 계층(Academic hierarchies)** — Department가 교수와 강좌를 조직
3. **성적 추적(Grade tracking)** — letter grade와 GPA를 온톨로지 속성으로 표현
4. **시간 데이터(Temporal data)** — 학기, 수강일, 학년도

---

## 전체 맥락: 무엇을 만드는 경로인가

University System 경로는 대학 관리 시스템의 데이터 모델을 설계한다. 최종 결과물은 **5개 엔티티 / 6개 관계**로 구성된 온톨로지다.

| 단계 | 추가 엔티티 | 누적 | 핵심 개념 |
|---|---|---|---|
| 1 | Student, Course, Enrollment | 3 | junction entity, 다대다 |
| 2 | Professor | 4 | transitive query, boolean 속성 |
| 3 | Department | 5 | 조직 계층, hub entity |

데이터는 SIS(학생정보시스템), LMS(학습관리시스템), 인사 시스템, 학사 기획 DB에 흩어져 있고, 온톨로지는 이를 하나의 질의 가능한 그래프로 묶는다.

경로가 내세우는 대표 질문:

> "50% 넘는 수강생이 C 미만을 받은 강좌를 가르치는 교수가 속한 학과는 어디인가?"

이 질문은 `Department → Professor → Course → Enrollment(grade < C) ← Student` 경로 하나로 매핑된다. 4가지 핵심 개념은 모두 이 한 문장을 답하기 위해 필요한 조각들이다.

---

## 개념 1 — Junction entity (Enrollment)

### 왜 필요한가

Student와 Course는 본질적으로 **다대다**다. 한 학생은 여러 강좌를 듣고, 한 강좌는 여러 학생을 받는다. 그런데 이 연결 자체에 붙는 정보가 있다.

- 성적(grade)은 학생의 속성인가? 아니다. 학생은 강좌마다 다른 성적을 받는다.
- 성적은 강좌의 속성인가? 아니다. 강좌는 학생마다 다른 성적을 낸다.

즉 grade/semester/status는 **양 끝단 어느 쪽에도 속하지 않고 연결 그 자체에 속한다.** 그래서 연결을 1급 엔티티로 승격시킨 것이 Enrollment다.

### Enrollment 속성

| 속성 | 타입 | 식별자 |
|---|---|---|
| `enrollmentId` | string | ✓ |
| `semester` | string | |
| `grade` | string | |
| `enrollDate` | date | |
| `status` | string | |

### 관계

- **enrolls_in** — `Student` → `Enrollment` (일대다). 학생은 학기를 거치며 여러 수강 기록을 갖는다.
- **for_course** — `Enrollment` → `Course` (다대일). 각 수강 기록은 정확히 하나의 강좌를 향한다.

핵심 형태는 **다대다를 두 개의 일대다로 쪼개는 것**이다: `Student →(1:N) Enrollment →(N:1) Course`.

### 판별 기준

> 두 엔티티가 다대다이고 **그 관계에 속성이 있으면** junction entity를 만든다.

속성이 전혀 없는 순수 다대다라면 단순 관계로 충분할 수도 있다. Enrollment가 정당화되는 이유는 grade·semester·status라는 관계 고유 속성이 있기 때문이다. 이 덕분에 "이 학생이 이 강좌를 이 학기에 들었을 때 받은 성적은?" 같은 질의가 가능해진다.

---

## 개념 2 — 학사 계층 (Department가 교수·강좌를 조직)

### Department 속성

| 속성 | 타입 | 식별자 |
|---|---|---|
| `departmentId` | string | ✓ |
| `name` | string | |
| `building` | string | |
| `budget` | float | |
| `headOfDept` | string | |

`budget`(float)은 자원 배분 질의를 가능하게 하고, `headOfDept`는 학과를 이끄는 교수를 참조하는 **자기 참조(self-referential) 패턴**으로 조직 계층에서 흔하다.

### 관계

- **belongs_to** — `Professor` → `Department` (다대일). 교수는 소속 학과를 갖는다.
- **offers** — `Department` → `Course` (일대다). 학과는 교육과정으로 강좌를 개설한다.

### 왜 "hub entity"인가

Department는 아래쪽으로 **교원(Professor)** 과 **교육과정(Course)** 두 갈래에 동시에 연결된다. 이 이중 연결 때문에 학과 단위 집계 질의의 자연스러운 기준점이 된다.

| 질문 | 그래프 경로 |
|---|---|
| 평균 학생 GPA가 가장 높은 학과는? | Department → Course ← Enrollment ← Student (avg GPA) |
| 소속 학과 밖의 강좌를 가르치는 교수는? | Professor → Department vs Professor → Course → Department |
| 학과별 수강률은? | Department → Course ← Enrollment (count) / Course.maxEnrollment |
| 정년보장 교원이 가장 많은 학과는? | Department ← Professor (tenured=true, count) |

주의: hub라고 불리는 이유는 "속성이 제일 많아서"도 "마지막에 추가돼서"도 아니다. **두 갈래(교원·교육과정)를 동시에 붙들고 있어서**다.

### 중간 다리 역할을 하는 Professor

Department가 계층의 꼭대기라면, Professor는 계층과 학사 기록을 잇는 지점이다.

| 속성 | 타입 | 식별자 |
|---|---|---|
| `professorId` | string | ✓ |
| `name` | string | |
| `rank` | string | |
| `tenured` | boolean | |
| `officeHours` | string | |

- **teaches** — `Professor` → `Course` (일대다)
- **advises** — `Professor` → `Student` (일대다)

`rank`(Assistant → Associate → Full)는 학술적 위계를, `tenured`(boolean)는 범주형 필터링을 제공한다. 그리고 `Professor → Course ← Enrollment ← Student` 경로 덕분에 **transitive query**(다중 홉 순회)가 가능해진다 — "정년보장 교수의 수업을 듣는 학생은?"처럼 직접 관계가 없는 엔티티를 중간 노드를 거쳐 잇는 질의다.

---

## 개념 3 — 성적 추적 (letter grade와 GPA를 속성으로)

성적은 **두 층위**로 나뉘어 서로 다른 엔티티에 붙는다. 이 분리가 핵심이다.

| 층위 | 속성 | 타입 | 소속 엔티티 | 성격 |
|---|---|---|---|---|
| 개별 성적 | `grade` | string | Enrollment | letter grade (A/B/C/D/F) |
| 집계 성적 | `gpa` | float | Student | 0.0–4.0 누적 평점 |

- **letter grade는 Enrollment에 둔다.** 성적은 "학생 × 강좌 × 학기" 단위로 발생하므로 junction entity의 속성이어야 한다.
- **GPA는 Student에 둔다.** 여러 수강 기록에서 파생된 집계 지표이며, 학사 경고·우등생 명단 같은 임계값 질의를 가능하게 하는 float다.

성적 추적이 실제로 작동하는 모습 — 평균 성적이 B 미만인(고전 중인) 학과 찾기:

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

`e.grade`(Enrollment의 string)로 필터링하고 Department 단위로 집계한다는 점에 주목하라. 개념 2(계층)와 개념 3(성적)이 한 질의에서 맞물린다.

관련 타입 선택도 함께 익힌다: `credits`, `maxEnrollment`(integer)는 학점·정원 계획을, `level`(100/200/300/400)은 난이도와 선수과목을, `budget`(float)은 예산 질의를 가능하게 한다.

---

## 개념 4 — 시간 데이터 (학기·수강일·학년도)

대학 데이터는 본질적으로 시간에 따라 반복된다. 같은 학생이 같은 강좌를 다른 학기에 다시 들을 수 있고, 학과 통계는 학년도별로 달라진다. 온톨로지는 이를 속성으로 흡수한다.

| 속성 | 타입 | 소속 엔티티 | 의미 |
|---|---|---|---|
| `semester` | string | Enrollment | 학기 (예: Fall 2024) |
| `enrollDate` | date | Enrollment | 수강 신청/등록 일자 |
| `enrollmentYear` | integer | Student | 입학 학년도 |
| `status` | string | Enrollment | 수강 상태 (진행/철회/완료 등) |

시간 속성 대부분이 **Enrollment에 모인다**는 점이 중요하다. Student와 Course는 상대적으로 안정적인 실체지만, 둘의 만남은 매 학기 새로 발생한다. junction entity가 시간축을 담는 그릇 역할을 한다 — 즉 개념 1과 개념 4는 같은 설계 결정의 앞뒷면이다.

`enrollmentYear`(integer)만 Student에 있는데, 이것은 개별 수강이 아니라 학생 자체의 코호트를 규정하기 때문이다.

---

## 네 개념의 연결 구조

```
Department ──offers──────────────► Course
    ▲                                ▲
    │belongs_to                      │for_course
    │                                │
Professor ──teaches──────────────► Course
    │                             Enrollment  ← grade, semester, enrollDate, status
    │advises                         ▲
    ▼                                │enrolls_in
 Student ───────────────────────────┘
   gpa, enrollmentYear
```

- **개념 1(junction)** 이 그래프의 중심 연결을 만들고,
- **개념 2(계층)** 가 그 위에 조직 구조를 씌워 집계 기준을 제공하며,
- **개념 3(성적)** 과 **개념 4(시간)** 은 junction entity에 실리는 속성으로 "무엇을 얼마나 잘, 언제" 했는지를 기록한다.

## 암기 포인트

- 4개를 순서로 외운다: **연결(junction) → 조직(계층) → 성과(성적) → 시점(시간)**.
- 각 개념을 대표 항목 하나와 짝지어 기억한다: junction=Enrollment, 계층=Department, 성적=grade+GPA, 시간=semester.
- grade는 Enrollment, GPA는 Student — 개별 vs 집계로 갈린다.
- Department가 hub인 이유는 Professor와 Course **둘 다**에 연결되기 때문이다.
