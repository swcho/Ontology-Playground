# 세 개념을 "EmployeeProfile" 하나로 합치면 잃는 것

## 카드 내용

- **Question**: 세 개념을 하나의 "EmployeeProfile" 엔티티로 합치면 잃는 유연성 3가지는?
- **Answer**: ① historical staffing changes(배치 이력 변경), ② role transitions(직무 전환), ③ 채용 전에 존재하는 open positions. 셋 다 표현할 수 없게 된다.

학습 자료 Organization Core 편의 "Why this separation matters" 절이 근거다.

> If you collapse these concepts into one "EmployeeProfile" entity, you lose flexibility for:
> - historical staffing changes
> - role transitions
> - open positions that exist before a hire

여기서 "세 개념"은 **Employee(사람)**, **Department(조직 단위)**, **Position(역할 정의)** 이다.

---

## 1. 원래 모델: 세 개의 독립 엔티티

| 엔티티 | 의미하는 것 | 식별자 | 주요 속성 |
|---|---|---|---|
| `Employee` | **사람** | `employeeId` | `name`, `hireDate`, `employmentStatus`, `jobLevel` |
| `Department` | **조직 단위** | `departmentId` | `name`, `budget`, `status` |
| `Position` | **역할 정의** | `positionId` | `title`, `level`, `salaryBand` |

세 엔티티는 존재의 성격이 서로 다르다.

- 사람은 부서를 옮겨도 같은 사람이다 → `Employee`는 배치와 무관하게 존재해야 한다.
- 부서는 소속 인원이 0명이어도 존재한다(예산은 그대로 있다) → `Department`도 독립적이어야 한다.
- 역할은 아무도 앉아 있지 않아도 존재한다(공석) → `Position`도 독립적이어야 한다.

이 세 가지가 각각 **독립적인 수명(lifecycle)** 을 갖는다는 점이 분리의 본질적 이유다.

---

## 2. Anti-pattern: 하나의 평면 레코드로 합치기

이 세 개념을 `EmployeeProfile` 한 엔티티로 합치면 다음과 같은 **평면(flat) 레코드**가 된다.

### EmployeeProfile (합쳐 버린 모습)

| profileId | name | hireDate | department | departmentBudget | position | positionLevel | salaryBand |
|---|---|---|---|---|---|---|---|
| P-001 | 김지훈 | 2021-03-01 | Finance | 1,200,000,000 | Financial Analyst | mid | B2 |
| P-002 | 이서연 | 2019-07-15 | Finance | 1,200,000,000 | Finance Manager | senior | C1 |
| P-003 | 박도현 | 2022-01-10 | Engineering | 3,500,000,000 | Backend Engineer | mid | B2 |

한 행에 **사람 + 조직 + 역할**이 모두 눌려 들어갔다. 겉보기에는 "조회가 편해 보이는" 구조지만, 세 가지 능력을 구조적으로 잃는다. 중요한 건 이것이 "쿼리를 잘 짜면 되는" 문제가 아니라 **모델이 표현할 수 없는 상태가 생기는** 문제라는 점이다.

---

## 3. 손실 ①: historical staffing changes (배치 이력)

### 무엇이 일어나는가

김지훈이 2024-07-01에 Finance에서 Engineering으로 이동했다고 하자. 평면 레코드에서 할 수 있는 유일한 동작은 **같은 컬럼을 덮어쓰는 것**이다.

```
변경 전: P-001 | 김지훈 | department=Finance     | position=Financial Analyst
변경 후: P-001 | 김지훈 | department=Engineering | position=Backend Engineer
```

이것이 **destructive update(파괴적 갱신)** 다. `department` 컬럼은 값을 하나만 담을 수 있으므로, 새 값을 쓰는 순간 이전 값은 **저장소에서 사라진다.**

### 왜 구조적으로 복구 불가능한가

- 과거 값이 **어디에도 남아 있지 않다.** 백업이나 감사 로그가 아닌, 모델 자체가 답을 갖고 있지 않다.
- 설령 이력을 남기려 해도 **"언제부터 언제까지"를 붙일 자리가 없다.** 배치는 사람의 속성도, 부서의 속성도 아니라 **둘 사이 관계의 속성**이기 때문이다. 평면 레코드에는 관계가 없으니 관계 속성을 둘 곳도 없다.
- 결과적으로 학습 자료가 예시로 든 질의들이 전부 불가능해진다.
  - **"Who was in Finance during Q2?"** (2분기에 Finance에 있던 사람은?) → 현재 스냅샷만 있으므로 답할 수 없다. 김지훈은 2분기에 Finance 소속이었지만 지금 레코드는 Engineering이라고 말한다.
  - **"Which employees changed departments this year?"** → 변경 사실 자체가 기록되지 않으므로 답할 수 없다.

### 억지로 버티려 하면

행을 복제해서 이력을 흉내 내면(`P-001`이 두 행), `profileId`가 더 이상 사람을 식별하지 못하고 `name`, `hireDate` 같은 사람 정보가 행마다 중복된다. 사실상 Assignment를 어설프게 재발명하면서 식별자만 망가뜨린 상태가 된다.

---

## 4. 손실 ②: role transitions (직무 전환)

### 무엇이 일어나는가

이서연이 Finance Manager에서 Finance Director로 승진한다. 평면 레코드에서는 사람과 역할이 **같은 행에 결합되어 있으므로**:

```
P-002 | 이서연 | position=Finance Manager  | positionLevel=senior | salaryBand=C1
              ↓ 승진(같은 행을 덮어쓴다)
P-002 | 이서연 | position=Finance Director | positionLevel=lead   | salaryBand=D1
```

### 왜 구조적으로 복구 불가능한가

- **전환 전/후를 동시에 표현할 수 없다.** 전환에는 겹치는 구간(인수인계 기간), 예정된 발령일, 소급 적용 같은 상태가 흔하다. 한 행 한 값 구조에서는 "8월까지는 Manager, 9월부터 Director"를 동시에 담을 방법이 없다.
- **사람 정보와 역할 정의가 뒤섞여 수정된다.** 위 갱신에서 실제로 바뀐 것은 "이서연의 배치"인데, 물리적으로는 `salaryBand`, `positionLevel` 같은 **역할 자체의 정의값**을 사람 행에서 고치고 있다. 역할의 정의(Finance Director의 salaryBand는 D1)와 사람의 배치(이서연이 그 역할을 맡는다)가 구분되지 않는다.
- 그 결과 **역할 관점 질의가 무너진다.** "Finance Manager 자리를 지금까지 거쳐 간 사람들"은 역할이 사람 행에 종속되어 있어 추적할 수 없다. 학습 자료의 표현대로 *"a position can be filled by different people over time"* 인데, 평면 모델은 역할을 사람보다 오래 사는 개체로 취급하지 못한다.
- 반대 방향의 오류도 생긴다. Finance Director의 salaryBand가 회사 정책으로 D1 → D2로 바뀌면, 그 역할을 가진 **모든 사람 행을 찾아서 다 고쳐야** 한다. 하나라도 놓치면 같은 역할에 두 개의 salaryBand가 공존한다. 이것이 정규화에서 말하는 **update anomaly(갱신 이상)** 다.

---

## 5. 손실 ③: open positions (채용 전에 존재하는 공석)

### 무엇이 일어나는가

Engineering이 Backend Engineer 한 자리를 새로 승인받았다. 아직 아무도 채용되지 않았다. 이 사실을 `EmployeeProfile`에 어떻게 적는가?

| profileId | name | hireDate | department | position | salaryBand |
|---|---|---|---|---|---|
| ??? | (없음) | (없음) | Engineering | Backend Engineer | B2 |

### 왜 구조적으로 복구 불가능한가

- 엔티티 이름이 이미 답을 말하고 있다. `EmployeeProfile`은 **사람이 있어야 존재하는 레코드**다. 즉 **엔티티의 존재 조건이 사람에 종속되어 있다.**
- 사람이 없으면 `profileId`, `name`, `hireDate`, `employmentStatus`가 모두 비거나 가짜 값이 되어야 한다. 식별자를 비울 수는 없으므로 `VACANT-001` 같은 **더미 사람**을 만들게 되고, 이후 모든 인원 집계 쿼리가 `name != 'VACANT'` 같은 조건을 달아야 정확해진다. 모델이 표현하지 못하는 것을 쿼리 규칙으로 떠넘긴 상태다.
- **채용 파이프라인 전체가 표현되지 않는다.** 채용 요청(headcount request) → 승인된 공석 → 후보자 → 입사는 모두 "사람이 아직 없는 역할"이 먼저 존재해야 성립한다. 인력 계획(workforce planning) 자체가 불가능해진다.
- 대칭적인 문제도 있다. 인원이 0명인 신설 부서(또는 인원을 모두 옮긴 폐지 예정 부서)도 표현할 수 없다. `Department`의 `budget`, `status`는 소속 인원과 무관하게 존재해야 하는 값인데, 평면 모델에서는 사람 행이 없으면 부서도 사라진다.

학습 자료가 Position 절에서 못 박아 둔 문장이 정확히 이 지점이다.

> Position separates role definition from the person currently assigned to it.

---

## 6. 정규화 관점에서 본 같은 이야기

세 가지 손실은 관계형 정규화 이론이 오래전에 정리한 문제와 동일하다.

| 정규화 개념 | EmployeeProfile에서의 증상 |
|---|---|
| **반복 그룹(repeating group)** | 한 사람의 여러 배치를 담으려면 `department1/department2` 같은 컬럼을 늘리거나 행을 복제해야 한다. 1NF 위반. |
| **부분 종속(partial dependency)** | `departmentBudget`은 `profileId`가 아니라 `department`에 종속된다. 사람 키에 붙어 있을 값이 아니다. |
| **update anomaly(갱신 이상)** | Finance 예산이 바뀌면 Finance 소속 **모든 행**을 고쳐야 한다. 일부만 고치면 같은 부서에 서로 다른 예산이 공존한다. |
| **insertion anomaly(삽입 이상)** | 사람 없이 부서/역할만 등록할 수 없다 → 손실 ③. |
| **deletion anomaly(삭제 이상)** | Finance의 마지막 직원 행을 삭제하면 **Finance 부서와 그 예산 정보까지 함께 사라진다.** |

특히 조직 속성 중복은 눈으로도 바로 보인다. 위 표에서 `departmentBudget=1,200,000,000`이 Finance 소속 **사람 수만큼 반복**된다. Finance에 300명이 있으면 같은 예산 값이 300번 저장되고, 300곳이 모두 동시에 정확해야 한다.

### 추가로 잃는 것: 겸직(다중 배치)

카드가 묻는 3가지는 아니지만 같은 뿌리에서 나오는 손실이다. 한 사람이 두 부서에 걸쳐 있는 경우(예: Engineering 소속이면서 Data Platform TF 겸직)를 평면 레코드는 표현할 수 없다. `department` 컬럼이 하나뿐이기 때문이다.

학습 자료가 지적한 그대로다.

> An employee can move between departments or positions over time. A department can host many employees. A position can be filled by different people over time.
> **This is not a simple one-to-one structure.**

평면 레코드는 사람 : 부서 : 역할을 **1:1:1로 강제**한다. 현실은 다대다이므로 모델이 현실을 담지 못한다.

---

## 7. 해법: 분리 + Assignment junction entity

세 개념을 분리하는 것만으로는 절반이다. 분리하면 "누가, 어디에, 어떤 역할로, 언제부터 언제까지"를 담을 곳이 필요해지는데, 이것이 **Assignment** 라는 junction entity(교차 엔티티)다.

```
Employee ──(one-to-many)──▶ Assignment ──(many-to-one)──▶ Department
                                 │
                                 └──(many-to-one)──▶ Position
```

### Assignment 속성

| Property | Type | Identifier? |
|---|---|---|
| `assignmentId` | string | ✓ |
| `startDate` | date | |
| `endDate` | date | |
| `isPrimary` | boolean | |

`startDate`/`endDate`/`isPrimary`는 Employee의 속성도, Department의 속성도, Position의 속성도 아니다. **관계 자체의 속성**이다. 학습 자료의 원칙: *"Use junction entities when relationships need their own attributes."*

### 세 손실이 어떻게 복구되는가

| 손실 | 분리 + Assignment로 해결되는 방식 |
|---|---|
| **① historical staffing changes** | 부서 이동 = 기존 Assignment에 `endDate`를 채우고 **새 Assignment 행을 추가**한다. 덮어쓰기가 아니라 append이므로 과거가 보존된다. "Who was in Finance during Q2?"는 `startDate <= Q2말 AND (endDate IS NULL OR endDate >= Q2초)` 조건의 시간 구간 질의로 답한다. |
| **② role transitions** | 같은 `Employee`에 Position이 다른 Assignment가 여러 개 붙는다. 전환 전/후가 **동시에 두 레코드로 공존**하며, 겹치는 구간도 표현된다. 역할 정의(`salaryBand`, `level`)는 `Position` 한 곳에만 있으므로 정책 변경 시 한 번만 고친다. 학습 자료의 그래프 경로: `Employee -> Assignment (multiple records by date) -> Position`. |
| **③ open positions** | `Position`이 독립 엔티티이므로 **Assignment가 0개인 Position = 공석**이라는 자연스러운 표현이 생긴다. 더미 사람이 필요 없다. 채용이 끝나면 Assignment 하나를 추가하면 된다. 같은 논리로 인원 0명인 Department도 정상 상태다. |

부수적으로 겸직은 `isPrimary`로 정리된다. 한 사람에게 활성 Assignment가 둘 있고, 하나는 `isPrimary=true`(주 소속), 다른 하나는 `false`(겸직)다. 부서 예산 중복도 사라진다. `budget`은 `Department` 한 행에만 존재한다.

---

## 8. 같은 패턴의 다른 이름들

이 구조는 HR에만 있는 특수 해법이 아니라 도메인을 가로지르는 표준 패턴이다.

| 도메인 | 두 축 | junction entity |
|---|---|---|
| 교육 | Student ↔ Course | **Enrollment** |
| 커머스 | Customer ↔ Product | **Order line item** |
| HR | Employee ↔ Department ↔ Position | **Assignment** |

---

## 한 줄 정리

세 개념을 `EmployeeProfile` 하나로 합치면, **덮어쓰기 때문에 과거가 사라지고(① 배치 이력)**, **사람과 역할이 한 행에 결합되어 전환을 표현할 수 없고(② 직무 전환)**, **사람 없는 행이 존재할 수 없어 공석을 표현할 수 없다(③ open positions)**. 세 가지 모두 쿼리로 우회할 수 있는 불편이 아니라, 모델이 그 상태를 담을 자리를 갖지 못하는 **구조적 손실**이다. 해법은 Employee/Department/Position을 분리하고, 그 사이를 `startDate`/`endDate`를 가진 **Assignment junction entity**로 잇는 것이다.
