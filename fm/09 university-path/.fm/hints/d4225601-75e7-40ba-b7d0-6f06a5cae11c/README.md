# Professor 엔티티는 온톨로지에 어떤 차원을 더하는가?

## 정답 요약

**"누가 가르치는가(who teaches)"라는 교수(teaching) 차원**을 더한다.
교수진(faculty)을 강좌(Course)에 연결하고, 그 강좌를 통해 **간접적으로(transitively)** 학생(Student)과도 연결한다.

> Who teaches the courses? The **Professor** entity adds the teaching dimension — connecting faculty to courses and, transitively, to students.

---

## 1. 왜 "차원"이라는 표현을 쓰는가

University System 학습 경로는 3단계로 온톨로지를 키워 나간다.

| 단계 | 추가 엔티티 | 누적 | 새로 열리는 질문의 축 |
|---|---|---|---|
| 1 | Student, Course, Enrollment | 3 | "누가 무엇을 수강하고 성적은 어떤가" (학생 중심) |
| 2 | **Professor** | 4 | **"누가 가르치는가"** (교수 중심) |
| 3 | Department | 5 | "어느 조직에 속하는가" (조직 중심) |

1단계의 학문적 핵심(academic core)은 세 가지 질문에 답한다.

- **Student** — 누가 배우는가? (who is learning?)
- **Course** — 무엇이 가르쳐지는가? (what is being taught?)
- **Enrollment** — 학생과 강좌를 성적과 함께 잇는 기록

여기에는 결정적으로 빠진 축이 하나 있다. 강좌가 "가르쳐지는" 대상이라는 것까지는 표현되지만, **그 강좌를 실제로 누가 가르치는지**는 어디에도 없다. Professor가 채우는 것이 바로 이 빈 축이다. 즉 단순히 노드가 하나 늘어난 게 아니라, 기존에는 물어볼 수조차 없던 **질문의 종류(category of question)** 자체가 새로 생긴다는 뜻에서 "차원(dimension)"이라 부른다.

---

## 2. Professor 엔티티 정의

| Property | Type | Identifier? |
|---|---|---|
| `professorId` | string | ✓ |
| `name` | string | |
| `rank` | string | |
| `tenured` | boolean | |
| `officeHours` | string | |

- `rank` — Assistant / Associate / Full. 학문적 위계(academic hierarchy)를 반영하는 정해진 서열이 있다.
- `tenured` — **boolean 속성**. 정년 보장 여부를 예/아니오로 범주화하여 필터링에 쓴다. 학습 경로에서 Professor 단계의 대표 학습 포인트 중 하나가 바로 "boolean 속성으로 yes/no 범주를 만든다"는 것이다.
- `officeHours` — 상담 가능 시간.

---

## 3. Professor가 추가하는 두 개의 관계

Professor는 두 방향으로 그래프에 붙는다.

- **teaches** — `Professor` → `Course` (one-to-many)
  한 교수는 학기당 하나 이상의 강좌를 가르친다. → **강좌와의 직접 연결**

- **advises** — `Professor` → `Student` (one-to-many)
  한 교수는 자기 학위 과정의 학생들을 지도한다. → **학생과의 직접 연결(지도 관계)**

여기서 헷갈리기 쉬운 지점을 정리해 두자.

- `advises`는 **지도(advising) 관계**로 학생과 직접 연결된다.
- 답에서 말하는 "강좌를 통해 **간접적으로** 학생과 연결"은 **가르치는(teaching) 맥락**을 뜻한다. 수업에서 만나는 학생들은 `advises`로 이어지지 않는다. 교수가 강좌를 가르치고, 그 강좌에 학생들이 등록(Enrollment)되어 있기 때문에 이어지는 것이다.

---

## 4. 핵심: 전이적 질의(transitive query)

Professor 단계의 진짜 값어치는 **전이적 질의**가 가능해진다는 데 있다. 경로는 다음과 같다.

```
Professor → Course ← Enrollment ← Student
```

즉 Professor와 Student 사이에는 (teaching 맥락에서) **직접 연결선이 없다**. 그런데도 중간 노드인 Course와 Enrollment를 거쳐 두 엔티티를 이을 수 있다.

```
Professor --teaches--> Course <--for_course-- Enrollment <--enrolls_in-- Student
```

이 경로 덕분에 새로 답할 수 있게 되는 질문들:

- "어떤 교수가 400-레벨 강좌를 가장 많이 가르치는가?" (Professor → Course, `level` 필터)
- "Smith 교수 강좌의 평균 GPA는 얼마인가?" (Professor → Course → Enrollment → Student, `gpa` 집계)
- "정년 보장 교수의 강좌를 듣는 학생은 누구인가?" (`tenured = true` 필터 + 전 경로 순회)
- "어떤 정년 보장 교수가 입문 강좌를 가르치는가?"

> **Transitive queries:** With Professor → Course ← Enrollment ← Student, you can now ask questions that cross the teaching relationship: "Which students are taking courses from tenured professors?"

학습 경로는 이를 두고 **"그래프 기반 온톨로지의 가장 큰 강점 중 하나(one of the greatest strengths of graph-based ontologies)"**라고 못박는다. 직접적인 관계가 없는 엔티티들을 중간 노드를 통해 이어 주기 때문이다.

---

## 5. 그래프 시점의 변화: 학생 중심 → 학생 + 교수 중심

Professor 추가 후 학습 경로가 정리하는 성과는 이렇다.

- boolean 속성(`tenured`)이 yes/no 범주 필터를 만든다
- 전이적 질의가 여러 관계를 넘나들며 멀리 떨어진 엔티티를 잇는다
- 학문적 서열(rank)이 정해진 위계를 따른다 (Assistant → Associate → Full)
- **그래프가 이제 학생 중심(student-centric) 질의와 교수 중심(faculty-centric) 질의를 모두 지원한다**

마지막 항목이 "차원이 하나 늘었다"는 말의 가장 직접적인 표현이다. 1단계에서는 "이 학생이 무엇을 들었나"만 물을 수 있었다면, 2단계에서는 반대 방향으로 "이 교수의 수업을 듣는 학생들은 어떤가"를 물을 수 있다. **같은 데이터를 교수라는 새 진입점(entry point)에서 조회**할 수 있게 되는 것이다.

---

## 6. 전체 그림에서의 위치

Professor는 이후 Department가 붙을 때 **연결 고리** 역할도 한다.

- **belongs_to** — `Professor` → `Department` (many-to-one): 교수는 학과에 소속된다
- Department의 `headOfDept` 속성은 학과장을 맡은 교수를 참조한다 (조직 위계에서 흔한 자기 참조 패턴)

그 결과 시나리오 개요에서 제시했던 최종 목표 질의가 완성된다.

```
Department → Professor → Course → Enrollment (grade < C) ← Student
```

*"등록 학생의 50% 이상이 C 미만을 받은 강좌를 가르치는 교수가 있는 학과는 어디인가?"*

이 문장에서 **Professor가 빠지면 경로가 끊긴다**. 학과 기록 · 교원 배정 · 강좌 개설 · 학생 성적을 하나로 꿰는 다리가 바로 Professor다.

---

## 7. 시험 대비 정리

| 물음 | 답 |
|---|---|
| Professor가 더하는 차원은? | "누가 가르치는가" = 교수(teaching) 차원 |
| 직접 연결되는 엔티티는? | Course (`teaches`), Student (`advises`), Department (`belongs_to`) |
| 간접(전이적)으로 연결되는 대상은? | 수강생 — Professor → Course → Enrollment → Student |
| 대표 학습 개념은? | 전이적 질의(transitive query), boolean 속성(`tenured`) |
| 새로 열리는 질의 시점은? | 교수 중심(faculty-centric) 질의 |

### 자주 하는 실수

- ❌ "Professor가 Student와 직접 연결되지 않는다" → `advises` 관계로 **직접 연결도 된다**. 다만 *가르치는* 맥락에서는 강좌를 경유한다.
- ❌ "Professor가 허브 엔티티다" → 허브 엔티티는 **Department**다. Professor와 Course 양쪽으로 뻗어 조직 위계 최상단에 앉기 때문이다.
- ❌ "Professor는 junction entity다" → junction entity는 **Enrollment**다. Student–Course 다대다를 속성과 함께 해소하는 역할이다.
