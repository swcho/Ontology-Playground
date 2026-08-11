# junction entity를 써야 하는 판단 기준

## 카드 내용

- **Question**: junction entity를 써야 하는 판단 기준은?
- **Answer**: 관계가 자신만의 속성(attributes)을 필요로 할 때다. 속성이 없다면 단순 관계로 충분하다.

학습 자료가 이 기준을 한 문장으로 못 박아 둔 곳이 Assignments 아티클의 마지막 줄이다.

> **Use junction entities when relationships need their own attributes.**

즉 판단의 출발점은 "many-to-many인가?"가 아니라 **"이 관계가 스스로 데이터를 들고 있어야 하는가?"** 다. M:N은 junction entity가 등장하는 흔한 정황일 뿐, 그 자체가 이유가 아니다.

## 판단 체크리스트

아래 네 가지 중 **하나라도 '예'면 junction entity**로 승격한다.

### (1) 관계에 속성이 필요한가?

관계가 참인 사실만으로 부족하고, "언제부터/언제까지, 얼마나, 어떤 등급으로, 주(main)인가"를 함께 기록해야 하는가.

전형적인 관계 속성들:

| 속성 유형 | 예시 |
|---|---|
| 기간 | `startDate`, `endDate`, `effectiveFrom` |
| 수량 | 주문 라인의 `quantity`, 배분율 `allocationPct` |
| 등급·역할 | 프로젝트 참여의 `role`, 평가의 `grade` |
| 주 여부 | `isPrimary` (겸직 중 주 소속 표시) |

이 속성들은 양쪽 엔티티 어디에도 자연스럽게 놓일 수 없다는 점이 핵심 신호다. `startDate`를 Employee에 두면 "어느 부서 배치의 시작일인지" 알 수 없고, Department에 두면 "누구의 시작일인지" 알 수 없다. **속성이 두 엔티티의 조합에 의존한다면 그 속성의 집은 관계다.**

### (2) 같은 두 개체 쌍이 시기를 달리해 반복될 수 있는가?

Employee A가 Finance 부서에 2023년에 있다가 → Sales로 옮기고 → 2026년에 다시 Finance로 돌아올 수 있는가.

돌아올 수 있다면 단순 링크로는 끝이다. 단순 관계는 사실상 `(A, Finance)`라는 **쌍의 집합(set)** 이고, 집합은 같은 원소를 두 번 담지 못한다. 두 번의 Finance 근무를 구분할 자리가 없어서 하나로 뭉개지거나 나중 값이 앞 값을 덮어쓴다.

junction entity는 각 근무 기간을 **별개의 레코드**로 만들어 이 중복을 구분한다. 학습 자료의 그래프 질문 표가 이 점을 정확히 노린다.

> Which employees changed roles in the last year? → `Employee -> Assignment (multiple records by date) -> Position`

"multiple records by date"라는 표현이 곧 (2)번 기준이다.

### (3) 관계 자체를 다른 엔티티가 참조하는가?

관계에 딸린 결재·증빙·이력을 붙여야 하는 경우다. 예를 들어 "이 배치를 승인한 결재 문서", "이 배치에 연동된 급여 조정 레코드", "이 주문 라인에 대한 반품"처럼 다른 엔티티가 관계를 가리켜야 한다면, 관계는 참조 대상이 될 수 있는 **일급 노드**여야 한다. 단순 관계는 화살표일 뿐이므로 무언가가 그것을 향해 화살표를 쏠 수 없다.

### (4) 관계에 고유 식별자를 부여해 외부에서 지목할 필요가 있는가?

"3월 결재 건 A-2041을 취소해 달라"처럼 관계 하나를 **이름 불러 지목**해야 하는가. API 응답, 감사 로그, 타 시스템 연동, 사람 간 커뮤니케이션에서 관계를 단독으로 언급해야 한다면 stable identifier가 필요하고, 식별자를 가질 수 있는 것은 엔티티다.

## HR 맥락 대입: Assignment는 왜 junction인가

학습 자료의 Assignment 속성표를 체크리스트에 그대로 대입해 보자.

| Property | Type | Identifier? |
|---|---|---|
| `assignmentId` | string | ✓ |
| `startDate` | date | |
| `endDate` | date | |
| `isPrimary` | boolean | |

- **(1) 충족** — `startDate`/`endDate`(기간)와 `isPrimary`(주 여부)를 갖는다. 넷 중 셋이 순수한 관계 속성이다.
- **(2) 충족** — 자료가 명시한 전제가 "An employee can move between departments or positions over time"이다. 부서 복귀·재배치가 가능하므로 같은 쌍이 시기를 달리해 반복된다.
- **(4) 충족** — `assignmentId`라는 stable identifier가 있어 특정 배치 건을 외부에서 지목할 수 있다.

관계 구조는 다음과 같이 세 갈래로 갈라진다.

```
Employee   -> Assignment   (one-to-many)
Assignment -> Department   (many-to-one)
Assignment -> Position     (many-to-one)
```

여기서 두 번째 힌트가 나온다. Assignment는 Employee-Department 두 개체만 잇는 게 아니라 **Employee-Department-Position 세 개체를 한 번에 묶는다**. 3항 이상의 관계(ternary relationship)는 단순 관계 두 개로 쪼개면 "어느 부서에서 어느 직책이었는지"의 짝이 깨지므로, 사실상 junction entity가 유일한 표현 수단이다.

같은 패턴이 도메인을 갈아타도 반복된다고 자료가 짚어 준다.

- Student-Course via **Enrollment** (성적, 수강 학기)
- Customer-Product via **Order line items** (수량, 단가)
- Employee-Department-Position via **Assignment** (기간, 주 여부)

## 반례: 속성이 없다면 단순 관계로 충분하다

M:N이라는 사실만으로 junction entity를 만들면 안 된다. 순수한 **분류·태깅·소속**은 관계가 참인지 거짓인지만 알면 되는 경우가 많다.

`Employee` - `Skill` 태깅을 생각해 보자. "이 직원은 Python을 할 수 있다" 이상의 정보가 필요 없다면:

- (1) 속성 없음 — 기간도 등급도 수량도 없다.
- (2) 반복 없음 — "A는 Python 가능"이라는 사실은 시기를 달리해 두 번 존재할 이유가 없다. 참이면 한 번 참이다.
- (3) 참조 없음 — 이 태그를 가리키는 다른 엔티티가 없다.
- (4) 식별자 불필요 — "직원 A의 Python 태그 #7"을 지목할 상황이 없다.

전부 '아니오'이므로 `Employee -> Skill` 단순 M:N 관계로 끝낸다. EmployeeSkill 같은 엔티티를 만들면 실질 정보 없이 노드 하나만 늘어난다.

단, 이 판단은 **요구사항이 바뀌면 뒤집힌다.** "숙련도(proficiency)", "인증 취득일", "재인증 만료일"을 관리하기로 하면 (1)이 즉시 충족되어 EmployeeSkill이 junction entity로 승격되어야 한다. 판단 기준은 M:N 카디널리티가 아니라 요구사항이라는 점이 여기서 드러난다.

## 대비: PerformanceReview는 junction이 아니다

같은 모델 안에서 헷갈리기 쉬운 대비 사례다. PerformanceReview도 `reviewId` 식별자와 `reviewDate`, `rating` 같은 속성을 잔뜩 갖고 있지만 **junction entity가 아니다.**

```
Employee -> PerformanceReview  (one-to-many)
```

이유는 단순하다. **Employee 한쪽에만 붙는 one-to-many**이기 때문이다. junction entity의 정의적 특징은 둘 이상의 엔티티 사이에 끼어들어(inter-join) 그들을 연결하는 것인데, PerformanceReview는 연결할 반대편 엔티티가 없다. 그저 Employee에 종속된 **일반 엔티티(하위 엔티티, dependent entity)** 다.

| 구분 | Assignment | PerformanceReview |
|---|---|---|
| 연결 대상 | Employee + Department + Position (3개) | Employee (1개) |
| 관계 형태 | 여러 방향으로 many-to-one 분기 | Employee로부터 one-to-many |
| 역할 | 관계를 실체화(reify) | Employee의 이벤트/측정값 기록 |
| 분류 | junction entity | 일반 엔티티 |

정리하면: **속성을 가진 것만으로는 junction이 아니다. 속성을 가진 관계가 둘 이상의 엔티티를 잇고 있을 때** junction entity다. 반대로 Assignment에서 Department와 Position 참조를 떼어내면 그것도 junction이 아니게 된다.

## 과도한 junction 도입의 비용

체크리스트가 전부 '아니오'인데도 습관적으로 junction을 넣으면 실제 대가가 있다.

- **경로 길이 증가**: `Employee -> Department`가 `Employee -> Assignment -> Department`로 한 홉 늘어난다. 자료의 그래프 질문에서 부서별 우수 평가자를 찾는 경로가 `Department <- Assignment <- Employee -> PerformanceReview`처럼 길어지는 것이 그 결과다.
- **질의 복잡도**: 홉이 늘면 조인/순회 단계가 늘고, 게다가 시간 축이 붙은 junction은 "질의 시점에 유효한 레코드만" 골라내는 조건(`endDate is null` 또는 기간 겹침 판정)을 매번 함께 써야 한다. 단순 관계에는 없던 부담이다.
- **인지 부하와 데이터 입력 비용**: 모델을 읽는 사람이 의미 없는 중간 노드를 계속 해석해야 하고, 실제 데이터에도 빈 레코드가 쌓인다.

그래서 균형점은 이렇다. Assignment처럼 **기간·주 여부·이력 추적이라는 실질 요구가 있으면 비용을 내고 도입할 값어치가 충분**하다. 반면 속성 없는 순수 분류에 junction을 두면 비용만 내고 얻는 것이 없다. 판단 기준을 "관계가 자신만의 속성을 필요로 하는가"로 잡는 이유가 바로 이 비용-효용 균형에 있다.

## 한 줄 요약

관계에 붙일 속성이 있는가, 같은 쌍이 시기를 달리해 반복되는가, 관계를 남이 참조하거나 지목해야 하는가 — 하나라도 '예'면 junction entity, 전부 '아니오'면 단순 관계로 충분하다.
