# University 학습 경로의 5가지 최종 교훈

> **Q.** University 학습 경로의 5가지 최종 교훈은?
>
> **A.** junction entity가 속성 있는 다대다를 해소하고, transitive query가 다중 홉 통찰을 열며, boolean 속성이 범주 필터를 만들고, 조직 계층이 집계 그룹을 제공하며, hub entity가 온톨로지의 여러 갈래를 연결한다는 것이다.

University System 학습 경로는 **5 entity / 6 relationship** 규모의 대학 행정 온톨로지를 3단계에 걸쳐 쌓아 올린다. 마지막 문서의 "Key takeaways"가 바로 이 다섯 문장이며, 각 교훈은 모델 안의 특정 요소에 정확히 대응한다.

전체 모델을 먼저 그려 두면 이해가 쉽다.

```
Department ──offers──▶ Course ◀──for_course── Enrollment ◀──enrolls_in── Student
     ▲                    ▲                                                  ▲
     └──belongs_to── Professor ──teaches──┘                                  │
                          └───────────────────advises───────────────────────┘
```

---

## 교훈 1 — Junction entity: 속성 있는 다대다를 해소한다

**모델 요소: `Enrollment`**

학생은 여러 과목을 듣고, 과목은 여러 학생을 받는다. 전형적인 many-to-many다. 그런데 이 연결 자체가 **성적(`grade`), 학기(`semester`), 수강 상태(`status`), 수강신청일(`enrollDate`)** 이라는 고유한 속성을 갖는다.

- 이 속성들은 `Student`의 것도 아니고(과목마다 성적이 다르다), `Course`의 것도 아니다(학생마다 성적이 다르다).
- 그래서 관계 자체를 일급 엔티티로 승격시킨다. 이것이 junction entity다.
- 결과적으로 `Student --enrolls_in--> Enrollment --for_course--> Course` 형태로, 하나의 다대다가 **두 개의 일대다(one-to-many) + 다대일(many-to-one)** 로 분해된다.
- 이 덕분에 "이 학생이 이번 학기 이 과목에서 받은 학점은?" 같은, 연결선 위에 값이 있어야만 답할 수 있는 질문이 가능해진다.

> 다른 도메인으로: 주문–상품 사이의 `OrderLine`(수량·단가), 배우–영화 사이의 `Casting`(배역·출연료), 사용자–권한 사이의 `RoleAssignment`(부여일·만료일)처럼 **관계에 값이 붙는 순간 그 관계는 엔티티가 되어야 한다.**

---

## 교훈 2 — Transitive query: 다중 홉 통찰을 연다

**모델 요소: `Professor → Course → Enrollment → Student` 경로**

Professor와 Student 사이에는 `advises` 직접 관계도 있지만, **가르치는 관계**는 직접 연결되어 있지 않다. 대신 Course와 Enrollment를 경유하면 도달할 수 있다.

- "정년보장 교수의 수업을 듣고 있는 학생은 누구인가?"는 어느 한 엔티티도 단독으로 답할 수 없다.
- 그래프를 3홉(hop) 따라가면 답이 나온다: `Professor(tenured=true) → Course → Enrollment → Student`.
- 즉 직접 관계를 새로 만들지 않고도, 기존 엣지의 **조합**으로 새로운 질문이 생겨난다. 엔티티를 하나 추가할 때마다 답할 수 있는 질문의 수가 곱셈으로 늘어나는 이유다.
- 완성 모델의 GQL 예시가 그대로 이 패턴이다.

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

> 다른 도메인으로: 공급망에서 `Supplier → Part → Product → Customer`로 특정 부품 리콜의 영향 고객을 추적하거나, 금융에서 `Account → Transaction → Account`를 반복 순회해 자금 세탁 경로를 찾는 것과 같은 원리다.

---

## 교훈 3 — Boolean 속성: 범주 필터를 만든다

**모델 요소: `Professor.tenured`**

`tenured`는 참/거짓 하나뿐이지만, 이 한 비트가 교수 집합을 **정확히 두 개의 배타적 그룹**으로 쪼갠다.

- "정년보장 교수는 입문 과목을 얼마나 맡는가?", "어느 학과에 정년보장 교원이 가장 많은가?" 같은 질문이 곧바로 `WHERE tenured = true` 한 줄로 표현된다.
- 문자열 속성인 `rank`(Assistant / Associate / Full)와 대비해 보면 차이가 뚜렷하다. `rank`는 순서 있는 다분류라 비교·정렬이 필요하지만, boolean은 **집합을 즉시 분할**하는 가장 값싼 필터다.
- boolean은 집계와도 잘 맞는다. 참인 항목을 세면 그대로 비율(정년보장 비율)이 된다.

> 다른 도메인으로: `Customer.isVip`, `Transaction.isFlagged`, `Employee.isActive`처럼 **"둘 중 하나"로 확실히 갈리는 상태는 열거형이나 문자열이 아니라 boolean으로 두어야 필터·집계가 단순해진다.**

---

## 교훈 4 — 조직 계층: 집계 그룹을 제공한다

**모델 요소: `Department`(계층 축으로서)**

Department는 대학의 행정 단위다. 교수와 과목이 모두 어느 학과엔가 소속되므로, Department는 자연스러운 **group-by 축**이 된다.

- "학과별 평균 학생 GPA", "학과별 수강률(`COUNT(Enrollment) / Course.maxEnrollment`)", "학과별 정년보장 교원 수" — 모두 Department를 기준으로 묶는 질문이다.
- 계층이 없으면 개별 과목·개별 교수 수준의 사실만 남고, 조직 단위의 비교나 예산 배분 판단이 불가능하다. `budget` float 속성이 있는 이유도 여기에 있다.
- `headOfDept`가 교수를 가리키는 **자기 참조(self-referential) 패턴**도 조직 계층의 전형적 장치다.

> 다른 도메인으로: HR의 `Department`/`Team`, 제조의 `Plant`/`Line`, 유통의 `Region`/`Store`처럼 **롤업 리포트가 필요한 순간 조직 계층 엔티티가 그 리포트의 행(row) 정의가 된다.**

---

## 교훈 5 — Hub entity: 온톨로지의 여러 갈래를 연결한다

**모델 요소: `Department`(허브로서)**

같은 Department지만 역할이 다르다. 교훈 4가 "위로 묶는 축"이라면, 교훈 5는 "**옆으로 잇는 다리**"다.

- Department는 아래로 두 갈래에 동시에 연결된다: `belongs_to`로 **교원(Professor)** 갈래, `offers`로 **교과과정(Course)** 갈래.
- 이 이중 연결이 있어야만 두 갈래를 교차하는 질문이 가능하다. 예: "자기 학과 소속이 아닌 과목을 가르치는 교수는?" → `Professor → Department`(소속)와 `Professor → Course → Department`(강의 학과)를 비교한다.
- 허브가 없으면 교원 데이터와 교과과정 데이터는 서로 만나지 못하는 두 섬으로 남는다. 허브는 새 속성을 주는 게 아니라 **새로운 경로**를 준다.
- 퀴즈에서 강조하듯, Department가 허브인 이유는 속성이 많아서도, 마지막에 추가되어서도 아니다. **Professor와 Course 양쪽에 모두 연결되기 때문**이다.

> 다른 도메인으로: 커머스의 `Order`가 고객·상품·결제·배송을 잇고, 의료의 `Patient`가 진료·처방·보험을 잇는 것처럼, **서로 다른 서브도메인이 만나는 지점에 놓인 엔티티가 허브다.**

---

## 단계별 교훈과 최종 5교훈의 대응

| 단계 | 추가 엔티티 | 누적 | 단계 핵심 개념 | 대응하는 최종 교훈 |
|---|---|---|---|---|
| 1단계 (Academic Core) | Student, Course, Enrollment | 3 | Junction entity, 속성 있는 many-to-many | **① Junction entity — 속성 있는 다대다 해소** |
| 2단계 (Faculty) | Professor | 4 | Transitive query, boolean 속성 | **② Transitive query — 다중 홉 통찰**<br>**③ Boolean 속성 — 범주 필터** |
| 3단계 (Complete Model) | Department | 5 | 조직 계층, hub entity | **④ 조직 계층 — 집계 그룹**<br>**⑤ Hub entity — 갈래 연결** |

대응 관계를 보면 구조가 드러난다. **1단계는 교훈 1개, 2단계와 3단계는 각각 2개씩**을 낳는다. 2단계는 "관계를 쓰는 법(transitive)"과 "속성을 쓰는 법(boolean)"을 하나씩, 3단계는 같은 Department 엔티티의 "위로 묶는 역할(계층)"과 "옆으로 잇는 역할(허브)"을 하나씩 담당한다.

즉 다섯 교훈은 **엔티티 설계(①) → 관계 활용(②) → 속성 활용(③) → 조직화(④⑤)** 순으로 추상도가 올라가며, 앞 단계가 없으면 뒤 단계가 성립하지 않는 누적 구조다. Enrollment 없이는 Professor→Student 경로가 끊기고, Professor 없이는 Department가 교원 갈래를 가질 수 없다.

---

## 외우기 요령

앞글자로 **"정 · 이 · 불 · 계 · 허"** — **정**션(junction) → **이**행(transitive) → **불**리언(boolean) → **계**층(hierarchy) → **허**브(hub).

또는 모델 요소 순서로 기억해도 된다: **Enrollment → (Professor→Course→Enrollment→Student) → tenured → Department → Department**. 마지막 둘이 같은 엔티티라는 점이 오히려 기억의 고리가 된다.

## 흔한 오해 짚기

- **"Enrollment는 노드를 늘리려고 만든 것"** → 아니다. grade/semester/status가 양 끝 어디에도 속하지 않기 때문이다.
- **"Department가 허브인 건 속성이 많거나 마지막에 추가되어서"** → 아니다. Professor와 Course 두 갈래에 모두 연결되기 때문이다.
- **"교훈 4와 5는 같은 말"** → 아니다. 4는 group-by 축(수직 집계), 5는 서브도메인 간 다리(수평 연결)로 역할이 다르다.
