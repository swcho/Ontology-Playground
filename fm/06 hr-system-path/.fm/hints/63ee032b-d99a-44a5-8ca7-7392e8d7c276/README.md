# Assignment 엔티티를 도입해 연결하는 세 관계

## 정답

| # | 관계 | Cardinality |
|---|---|---|
| 1 | `Employee` -> `Assignment` | one-to-many (1:N) |
| 2 | `Assignment` -> `Department` | many-to-one (N:1) |
| 3 | `Assignment` -> `Position` | many-to-one (N:1) |

Assignment는 이 세 관계의 교차점에 놓여 **관계 자체의 컨텍스트**(`startDate`, `endDate`, `isPrimary`)를 보관한다.

---

## 왜 Assignment가 필요한가

HR 현실 세계의 제약을 문장으로 적어 보면 단순 1:1이 아니라는 게 바로 드러난다.

- 한 직원은 시간이 지나며 **여러 부서**를 옮겨 다닌다.
- 한 부서는 **여러 직원**을 수용한다.
- 한 직무(Position)는 시간이 지나며 **여러 사람**이 채운다.
- 한 직원은 커리어 동안 **여러 직무**를 맡는다.

즉 원래 모델에는 many-to-many가 **두 개** 존재한다.

```
Employee  <──── M:N ────>  Department
Employee  <──── M:N ────>  Position
```

M:N 관계는 그 자체로 속성을 걸 곳이 없다. "이 직원이 Finance 부서에 **2024-01-01부터 2024-09-30까지** 있었다"는 사실은 Employee의 속성도 아니고 Department의 속성도 아니다. 오직 **그 둘이 연결된 사건**의 속성이다. 그래서 연결 사건을 1급 엔티티로 승격시킨다. 이것이 junction entity(교차 엔티티) 패턴이다.

---

## 구조 다이어그램

```
                        ┌──────────────┐
                        │   Employee   │
                        │ employeeId ✓ │
                        │ jobLevel     │
                        └──────┬───────┘
                               │ 1
                               │        one-to-many
                               │ N
                        ┌──────┴─────────────┐
                        │    Assignment      │   ← junction entity
                        │ assignmentId ✓     │     (관계의 컨텍스트 보관)
                        │ startDate          │
                        │ endDate            │
                        │ isPrimary          │
                        └───┬────────────┬───┘
                     N      │            │      N
        many-to-one         │            │         many-to-one
                     1      │            │      1
              ┌─────────────┴──┐    ┌────┴───────────┐
              │   Department    │    │   Position     │
              │ departmentId ✓  │    │ positionId ✓   │
              │ budget          │    │ level          │
              └─────────────────┘    │ salaryBand     │
                                     └────────────────┘
```

핵심 관찰: **화살표가 세 개 모두 Assignment를 지나간다.** Employee에서는 내려오고, Department/Position으로는 내려간다. Assignment는 "허브"이며 나머지 셋은 "스포크"다.

---

## 관계 1: `Employee` -> `Assignment` (one-to-many)

**한 직원이 여러 개의 배치 레코드를 갖는다.**

근거:

- 입사 시 최초 배치 1건이 생긴다.
- 부서 이동, 승진, 직무 전환마다 **새 Assignment 레코드가 추가**된다. 기존 레코드를 덮어쓰지 않고 `endDate`만 채운다.
- 겸직(dual reporting)이 있으면 **동시에 활성화된 Assignment가 2건 이상** 존재할 수 있다. 이때 `isPrimary`로 주 소속을 구분한다.

따라서 Employee 1건 : Assignment N건. 반대 방향으로 보면 Assignment 하나는 반드시 정확히 한 사람에 속한다(배치는 특정 개인에 대한 사건이므로). 그래서 `Assignment` -> `Employee`로 뒤집어 표기하면 many-to-one이 된다. 자산 문서는 Employee를 주체로 삼아 one-to-many로 적었을 뿐, 같은 사실을 서술한 것이다.

이 관계 덕분에 **이력이 파괴적 업데이트 없이 누적**된다. Employee에 `departmentId` 컬럼 하나만 두었다면 이동할 때마다 과거 정보가 사라진다.

## 관계 2: `Assignment` -> `Department` (many-to-one)

**한 배치는 정확히 하나의 부서를 지목하지만, 하나의 부서는 수많은 배치에 등장한다.**

근거:

- "many" 쪽(Assignment): Finance 부서에는 과거·현재 배치 레코드가 수백 건 쌓인다. 서로 다른 직원, 서로 다른 기간.
- "one" 쪽(Department): 배치 레코드 하나가 "Finance이면서 동시에 Engineering"일 수는 없다. 두 부서에 걸치면 그건 **배치 2건**이다.

이 "정확히 하나를 지목한다"는 성질이 many-to-one의 정의다. 함수적 종속(functional dependency)으로 쓰면 `assignmentId -> departmentId`가 성립한다.

## 관계 3: `Assignment` -> `Position` (many-to-one)

**한 배치는 정확히 하나의 직무를 지목하지만, 하나의 직무는 여러 배치에 등장한다.**

근거:

- "many" 쪽(Assignment): "Senior Backend Engineer" 직무는 시간이 지나며 여러 사람이 채운다 → 배치 레코드 여러 건.
- "one" 쪽(Position): 배치 하나가 두 직무를 동시에 의미하면 모호해진다. 직무가 바뀌면 새 배치를 만든다.
- Position은 사람이 없어도 독립 존재한다(**공석/open position**). 그래서 Assignment 0건인 Position도 유효하다 — many-to-one의 "many"는 0을 포함한다.

`assignmentId -> positionId` 역시 함수적 종속이다.

---

## 왜 "many" 쪽은 항상 Assignment인가

세 관계를 나란히 세워 보면 규칙이 하나로 정리된다.

| 관계 | one 쪽 | many 쪽 | many인 이유 |
|---|---|---|---|
| Employee ↔ Assignment | Employee | **Assignment** | 한 사람이 여러 번 배치된다 |
| Assignment ↔ Department | Department | **Assignment** | 한 부서에 여러 배치가 쌓인다 |
| Assignment ↔ Position | Position | **Assignment** | 한 직무를 여러 배치가 거쳐간다 |

Employee, Department, Position은 모두 **오래 지속되는 마스터 데이터**다. 사람, 조직, 역할 정의는 각각 하나의 안정된 실체다. 반면 Assignment는 **이벤트/사실(fact) 레코드**다. 이벤트는 마스터 데이터의 조합마다 생성되므로 언제나 개수가 더 많다.

이것은 데이터 웨어하우스의 star schema와 정확히 같은 구조다. Assignment = fact table, 나머지 셋 = dimension table. Fact는 항상 여러 dimension을 향해 many-to-one으로 붙는다.

---

## 관계 대수: 두 개의 M:N을 하나로 해소한다

Assignment의 진짜 위력은 **하나의 junction으로 두 개의 M:N을 동시에 분해**한다는 점이다.

```
[분해 전]
   Employee ═══ M:N ═══ Department        ← 속성 걸 곳 없음
   Employee ═══ M:N ═══ Position          ← 속성 걸 곳 없음

[분해 후]
   Employee ──1:N──> Assignment ──N:1──> Department
                          │
                          └────N:1──────> Position
```

관계 대수적으로 보면:

- `Employee 1:N Assignment` 와 `Assignment N:1 Department`를 조인하면 **원래의 Employee M:N Department가 복원된다.**
- 같은 Assignment를 Position 쪽으로 조인하면 **Employee M:N Position이 복원된다.**
- 즉 Assignment는 두 M:N의 **공통 분해 지점**이다. 정보를 잃지 않고(lossless decomposition) 오히려 `startDate` / `endDate` / `isPrimary`라는 정보를 **추가**로 얻었다.

만약 junction을 두 개로 쪼개 `EmployeeDepartment`와 `EmployeePosition`을 따로 만들었다면, "Finance 부서에서 Senior Engineer로 일한 기간"이라는 삼원(ternary) 사실을 표현할 수 없다. 두 테이블의 기간을 억지로 교차시켜야 한다. Assignment 하나가 (Employee, Department, Position, 기간) 4-tuple을 원자적으로 담기 때문에 이 문제가 발생하지 않는다.

같은 패턴이 다른 도메인에도 그대로 나타난다.

| 도메인 | M:N 양쪽 | Junction |
|---|---|---|
| 교육 | Student ↔ Course | Enrollment (수강 기간, 성적) |
| 커머스 | Customer ↔ Product | Order line item (수량, 단가) |
| HR | Employee ↔ Department, Employee ↔ Position | **Assignment** (startDate, endDate, isPrimary) |

판단 기준: **관계가 자기만의 속성을 가져야 한다면 junction 엔티티로 만든다.**

---

## 화살표 방향 ≠ 질의 순회 방향

여기서 자주 헷갈리는 지점을 분리해 두자.

**화살표 방향(스키마 선언)** 은 cardinality 제약을 어느 쪽에서 서술하는지를 나타낸다. `Assignment -> Department (many-to-one)`은 "Assignment 쪽이 many, Department 쪽이 one"이라는 **정적 구조 사실**이다. 물리 구현에서는 보통 many 쪽이 외래 키를 들고 있다 → Assignment 테이블에 `departmentId` 컬럼이 있다.

**순회 방향(질의 실행)** 은 그래프를 어느 쪽에서 출발해 걷는지를 나타낸다. 이건 스키마와 무관하게 **양방향 모두 가능**하다. 관계는 한 번 선언되면 정방향/역방향 모두 탐색된다.

자산 문서의 질의 예시가 이를 잘 보여준다.

| 질문 | 그래프 경로 | 방향 해석 |
|---|---|---|
| 어느 부서에 시니어 직원이 가장 많은가? | `Department <- Assignment <- Employee (jobLevel=senior)` | **역방향** 순회 |
| 최근 1년간 역할이 바뀐 직원은? | `Employee -> Assignment (날짜별 복수 레코드) -> Position` | **정방향** 순회 |
| 미해결 리뷰가 많은 팀은? | `Department <- Assignment <- Employee -> PerformanceReview` | 역방향 + 정방향 **혼합** |

첫 번째 경로 `Department <- Assignment <- Employee`를 읽어 보면:

1. Department에서 시작한다.
2. `<-` 로 그 부서를 가리키는 Assignment들을 **역방향으로 모은다**(one → many 팬아웃).
3. 다시 `<-` 로 각 Assignment가 속한 Employee를 찾아 `jobLevel=senior`로 필터한다.

스키마상 화살표는 `Assignment -> Department`인데 순회는 `Department <- Assignment`다. **모순이 아니다.** 화살표는 "누가 many인가"를 말하고, 순회 기호는 "지금 어느 쪽으로 걷는가"를 말한다. one 쪽에서 many 쪽으로 역방향 순회할 때는 결과가 팬아웃(1건 → N건)되고, many 쪽에서 one 쪽으로 정방향 순회할 때는 결과가 수렴(N건 → 1건)된다는 점만 기억하면 된다.

---

## 자주 하는 실수

- **Employee에 `departmentId` / `positionId`를 직접 두기** → 현재 상태만 남고 이력이 소멸한다. 겸직도 표현 불가.
- **Assignment에 `departmentId`를 여러 개 담기(배열)** → many-to-one이 깨지고 함수적 종속이 사라진다. 부서가 둘이면 Assignment를 둘로 나눈다.
- **화살표 방향을 질의 방향으로 착각** → `Assignment -> Department`라서 Department에서 출발할 수 없다고 오해한다. 역방향 순회는 정상이다.
- **`endDate`를 비우지 않고 삭제** → 활성 배치는 `endDate`가 null, 종료된 배치는 값이 채워진다. 레코드를 지우면 이력 추적이 무의미해진다.

---

## 한 줄 요약

Assignment는 Employee로부터 1:N을 받고 Department·Position으로 각각 N:1을 내보내는 junction 엔티티로, Employee↔Department와 Employee↔Position 두 개의 many-to-many를 동시에 분해하면서 `startDate` / `endDate` / `isPrimary`라는 관계 고유 속성을 담을 자리를 만든다.
