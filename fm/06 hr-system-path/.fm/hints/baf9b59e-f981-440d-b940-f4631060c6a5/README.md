# 이 경로가 제시하는 4개 key concepts

> **Q.** 이 경로가 제시하는 4개 key concepts는?
>
> **A.** ① 모든 엔티티에 대한 stable identifiers, ② many-to-many 배치 시나리오를 위한 junction entities, ③ 시간 인식 분석을 위한 temporal properties, ④ 통제된 상태·등급 값을 위한 enum values.

HR System 경로의 Scenario Overview는 학습 목표를 위 네 가지 개념으로 압축한다. 중요한 것은 이 네 개가 추상적인 슬로건이 아니라, 이후 3개 아티클에서 만드는 **5개 엔티티(Employee, Department, Position, Assignment, PerformanceReview)의 속성표 안에 그대로 박혀 있다는 점**이다. 아래에서 개념별로 "모델의 어느 지점에서 실제로 나타나는가"를 매핑한다.

---

## 1. Stable identifiers — 모든 엔티티에 안정적인 식별자

### 모델에서 나타나는 지점

경로가 만드는 5개 엔티티는 예외 없이 `~Id` 속성 하나를 identifier로 표시한다.

| 엔티티 | Identifier | 타입 |
|---|---|---|
| Employee | `employeeId` | string |
| Department | `departmentId` | string |
| Position | `positionId` | string |
| Assignment | `assignmentId` | string |
| PerformanceReview | `reviewId` | string |

"모든 엔티티에 대한(for every entity)"이라는 표현이 문자 그대로다. 새 엔티티를 추가할 때마다 가장 먼저 하는 일이 stable id를 정하는 것이다.

### email을 키로 쓰지 않는 이유

Organization Core는 Employee를 정의하면서 이렇게 못 박는다.

> `employeeId` is a stable business identifier. Avoid using mutable attributes like email as the primary key.

email(또는 이름, 사번 표기 형식, 부서명)을 키로 쓰면 안 되는 이유는 **mutable = 변한다**는 것이다.

- **결혼/개명/조직 이메일 정책 변경**으로 email이 바뀌면, 그 사람을 가리키던 모든 참조가 끊긴다. 그래프 상에서는 "한 사람이 두 사람이 되는" 결과가 나온다.
- **재사용 위험**: 퇴사자의 email 주소가 신입에게 재할당되면, 과거 Assignment와 PerformanceReview가 엉뚱한 사람에게 붙는다.
- **다중 값**: 개인 메일/회사 메일/별칭 등 하나의 사람에 여러 email이 존재할 수 있어 유일성 보장이 어렵다.
- **PII 결합**: 식별자는 로그, URL, 외부 시스템 연동 키로 널리 퍼진다. 여기에 개인정보를 넣으면 삭제·마스킹 요구(예: 개인정보 삭제 요청)에 대응할 수 없다.

반대로 `employeeId`는 사람의 속성이 아무리 바뀌어도 그대로 유지되는 **비의미적(non-semantic) 비즈니스 키**다. 그래서 payroll, HRIS, 스프레드시트, 매니저 노트에 흩어진 데이터를 하나의 그래프로 합칠 때 **조인 앵커** 역할을 할 수 있다. Scenario Overview가 지적한 "데이터가 여러 시스템에 흩어져 있다"는 문제를 푸는 첫 열쇠가 바로 이것이다.

### Position의 identifier가 특별히 중요한 이유

`positionId`는 사람과 무관하게 존재한다. Organization Core는 Position을 별도 엔티티로 두는 이유로 "**open positions that exist before a hire**"를 든다. 즉 아직 아무도 없는 자리도 식별자를 갖고 예산·조직 계획에 등장할 수 있다. 만약 역할 정보를 Employee 안에 접어 넣었다면, 사람이 없는 자리는 표현할 방법이 없다.

---

## 2. Junction entities — many-to-many 배치 시나리오

### 모델에서 나타나는 지점: Assignment

Assignments 아티클이 제시하는 문제 상황은 명확하다.

- 한 employee가 시간에 따라 department/position을 옮긴다.
- 한 department는 여러 employee를 수용한다.
- 한 position은 시간에 따라 다른 사람이 채운다.

즉 Employee–Department–Position은 **1:1이 아니고, 단순 1:N도 아니다.** 그래서 관계 자체를 엔티티로 승격시킨 것이 **Assignment**다.

```
Employee ──(one-to-many)──> Assignment ──(many-to-one)──> Department
                                 └──────(many-to-one)──> Position
```

Assignment는 "누가 / 어느 조직에서 / 어떤 역할로 / 언제부터 언제까지 / 주 배치인지"라는 **관계의 문맥(context of the relationship)** 을 담는다.

| 속성 | 타입 | 역할 |
|---|---|---|
| `assignmentId` | string | 식별자 (개념 ①과 맞물림) |
| `startDate` | date | 시작 시점 (개념 ③) |
| `endDate` | date | 종료 시점 (개념 ③) |
| `isPrimary` | boolean | 겸직 시 주 배치 표시 |

`isPrimary`의 존재는 "한 사람이 동시에 둘 이상의 Assignment를 가질 수 있다"는 것을 전제한다. 겸직/파견/프로젝트 배치를 모델이 이미 허용하고 있고, 헤드카운트 집계 시 중복을 막을 장치가 `isPrimary`다.

### 동형 패턴 — 이 패턴은 HR에만 있는 게 아니다

아티클은 같은 구조가 여러 도메인에서 반복된다고 명시한다.

| 도메인 | 양쪽 엔티티 | junction entity | junction이 갖는 고유 속성(예) |
|---|---|---|---|
| 교육 | Student ↔ Course | **Enrollment** | 수강 학기, 성적, 등록/철회일 |
| 커머스 | Customer ↔ Product | **Order line item** | 수량, 단가, 할인 |
| HR | Employee ↔ Department/Position | **Assignment** | startDate, endDate, isPrimary |

판별 기준은 한 문장으로 요약된다: **"Use junction entities when relationships need their own attributes."** 관계에 붙일 속성이 생기는 순간(성적, 수량, 기간), 그 관계는 더 이상 화살표가 아니라 엔티티다.

역으로 이런 식으로 판단하면 된다 — "이 정보는 Employee의 속성인가, Department의 속성인가?" 어느 쪽에도 자연스럽게 속하지 않는다면(예: 재직 시작일이 아니라 *그 부서에서의* 시작일) 그것은 관계의 속성이고, junction entity가 필요하다.

### junction이 없으면 무엇이 깨지는가

Employee에 `departmentId`, `positionId`를 직접 필드로 넣으면:

- 값이 덮어써져 **이력이 소실**된다. "작년에 어디 있었나"에 답할 수 없다.
- 겸직을 표현할 수 없다(필드가 하나뿐).
- 기간을 붙일 자리가 없다. `startDate`를 Employee에 두면 그것이 입사일인지 현 부서 배치일인지 모호해진다.

Complete HR Model의 퀴즈가 "시간에 따른 역할·부서 변경 이력 분석을 가능하게 하는 엔티티"의 정답으로 Assignment를 꼽는 이유가 이것이다.

---

## 3. Temporal properties — 시간 인식(time-aware) 분석

### 모델에서 나타나는 지점

날짜 속성은 세 엔티티에 흩어져 있고, 각각 답하는 질문의 종류가 다르다.

| 속성 | 소속 엔티티 | 의미 | 답할 수 있는 질문 |
|---|---|---|---|
| `hireDate` | Employee | 조직 최초 입사 시점 | 재직 기간(tenure), 코호트별 유지율, 연차 산정 |
| `startDate` | Assignment | *그 배치*의 시작 | "2분기에 Finance에 있던 사람은?" |
| `endDate` | Assignment | *그 배치*의 종료 (미설정 = 현재 진행) | "지금 활성 배치는?", "올해 부서를 옮긴 사람은?" |
| `reviewDate` | PerformanceReview | 평가 시점 | "직전 리뷰 사이클 결과는?", 사이클 간 등급 추이 |

`hireDate`와 `startDate`가 **분리되어 있다는 점**이 핵심이다. 같은 회사에 5년 있었지만 현 부서 배치는 3개월 차인 사람 — 이 둘을 하나의 날짜로 합치면 표현할 수 없다. 사람의 시간축(입사~퇴사)과 배치의 시간축(부서/역할 구간)과 평가의 시간축(사이클)은 서로 다른 축이며, 각각 자기 엔티티에 자기 날짜를 갖는다.

### startDate + endDate = 구간(interval) 모델

Assignment가 시작·종료를 함께 가지면 **시점 질의(as-of query)** 가 가능해진다.

- **"Who was in Finance during Q2?"** → `startDate <= Q2말` AND (`endDate` is null OR `endDate >= Q2초`)인 Assignment를 통해 Department=Finance를 역추적.
- **"Which employees changed departments this year?"** → 올해 안에 같은 Employee의 Assignment가 종료되고 다른 Department의 Assignment가 시작된 패턴.
- **"Which assignments are no longer active?"** → Complete HR Model의 표대로 `endDate`가 설정되었거나 `isPrimary=false`인 Assignment.

여기서 중요한 관용(convention)이 하나 있다: **`endDate`가 비어 있음(null) = 아직 진행 중**. 이 규칙이 "현재 조직도"를 별도 테이블 없이 같은 데이터에서 파생할 수 있게 해준다. 현재 상태는 이력의 특수한 단면(now 기준 스냅샷)일 뿐이다.

### PerformanceReview의 시간축

PerformanceReview는 `reviewDate`(정확한 시점)와 `reviewPeriod`(사이클 라벨, 예: "2024-H1")를 **둘 다** 갖는다. 사이클 라벨은 사람이 사이클 단위로 묶어 보기 위한 것이고, `reviewDate`는 "last review cycle" 같은 상대적 시간 조건을 계산하기 위한 것이다. Scenario Overview의 대표 질문 — "**Which departments have the highest number of senior employees rated outstanding in the last review cycle?**" — 은 `reviewDate`/`reviewPeriod`로 사이클을 잘라내고, Assignment의 `startDate`/`endDate`로 그 시점의 소속 부서를 확정해야 비로소 답이 된다. temporal properties가 없으면 이 질문은 "현재 부서 기준"으로만 답할 수 있고, 그건 원래 질문과 다른 질문이다.

---

## 4. Enum values — 통제된 상태·등급 값

### 모델에서 나타나는 지점

enum으로 선언된 속성은 5개 엔티티 중 4곳에 등장한다.

| 엔티티 | enum 속성 | 역할 |
|---|---|---|
| Employee | `employmentStatus` | 재직 상태 (예: active / on-leave / terminated) |
| Employee | `jobLevel` | 직급 (예: junior / mid / senior) |
| Department | `status` | 조직 활성 여부 (예: active / inactive) |
| Position | `level` | 역할 자체의 레벨 |
| PerformanceReview | `rating` | 평가 등급 (예: outstanding / exceeds / meets / …) |

Position의 `level`과 Employee의 `jobLevel`이 **따로 존재하는 것**도 눈여겨볼 지점이다. 자리에 요구되는 레벨과 사람이 현재 가진 레벨은 다를 수 있고(승진 전 임시 수행, 상위 직무 대행), 그 차이 자체가 분석 대상이 된다.

### 통제 어휘(controlled vocabulary)가 없으면 집계가 깨지는 이유

enum이 아니라 자유 텍스트였다고 상상해 보자. 여러 시스템(payroll, HRIS, 스프레드시트, 매니저 노트)에서 데이터가 흘러들어오므로 같은 뜻의 값이 이렇게 갈라진다.

- `senior` / `Senior` / `SENIOR` / `Sr.` / `Sr` / `시니어` / `senior engineer`
- `outstanding` / `Outstanding` / `O` / `5` / `최우수` / `exceptional`
- `active` / `Active` / `현직` / `재직중` / `Y`

이 상태에서 무엇이 깨지는가.

1. **GROUP BY가 쪼개진다.** "senior 직원 수"를 세면 표기별로 7개 그룹이 나오고, 어떤 그룹도 진짜 총계가 아니다. Complete HR Model의 `jobLevel=senior` 필터는 단 하나의 표기만 잡아내므로 **조용히 과소 집계**된다. 오류가 나지 않고 그냥 틀린 숫자가 나오는 것이 가장 위험하다.
2. **필터가 침묵 실패한다.** `rating=outstanding`으로 쿼리했는데 어떤 시스템은 `Outstanding`으로 적어 넣었다면, 그 부서는 리포트에서 아예 사라진다.
3. **순서(ordinal)를 잃는다.** 등급과 직급은 본질적으로 순서가 있다(junior < mid < senior, meets < exceeds < outstanding). 자유 텍스트는 순서를 모르므로 "senior 이상", "meets 미만" 같은 범위 조건, 등급 분포 히스토그램, 사이클 간 상승/하락 추이 계산이 불가능해진다.
4. **정합성 검증이 불가능하다.** enum이면 "허용되지 않은 값"을 입력 시점에 막을 수 있다. 자유 텍스트는 오타(`snior`)가 그대로 저장되고, 사후에 사람이 눈으로 찾아야 한다.
5. **UI/문서/거버넌스가 흔들린다.** 드롭다운 목록, 리포트 범례, 정책 문서가 모두 같은 값 집합을 참조해야 한다. enum은 그 목록의 **단일 정의 지점(single source of truth)** 이 된다.

그래서 Complete HR Model의 takeaway는 identifiers와 enum을 한 문장에 묶는다: "**Keep identifiers stable and statuses controlled via enum values.**" 식별자는 *행(row)이 무엇을 가리키는지*를 안정시키고, enum은 *열(column)의 값이 무엇을 의미하는지*를 안정시킨다.

---

## 네 개념은 어떻게 맞물려 governance-ready 구조가 되는가

Scenario Overview는 학습 결과를 "practical HR domain with clear **governance-ready structure**"로 표현한다. 네 개념은 각각 독립된 팁이 아니라, 이 governance를 네 방향에서 지탱하는 다리다.

```
                    stable identifiers  ← 무엇에 대한 데이터인가 (identity)
                            │
                            ▼
temporal properties ──► junction entity ◄── enum values
   언제 유효한가              (Assignment)      값이 무엇을 뜻하는가
   (validity)                   │              (vocabulary)
                                ▼
                    "그 시점, 그 사람, 그 부서, 그 등급" 을
                       단일 그래프에서 질의 가능
```

- **identifiers → junction 성립 조건.** Assignment는 employee/department/position을 안정적으로 가리킬 수 있어야 성립한다. 참조 대상의 키가 흔들리면 junction 레코드는 곧 고아(orphan)가 된다. 또 `assignmentId` 자체가 있어야 "이 배치 건"을 감사 로그·정정·승인 흐름에서 지목할 수 있다.
- **temporal + junction → 이력이 데이터가 된다.** 날짜는 junction 안에 있을 때 비로소 힘을 낸다. Employee에 붙은 날짜는 사람의 이력이지 배치의 이력이 아니다. 둘이 결합해 "언제, 누가, 어디에" 라는 3중 사실이 하나의 불변 레코드로 남고, 덮어쓰기(destructive update)가 사라진다. 이것이 감사 가능성(auditability)의 실체다.
- **enum + temporal → 시계열 비교가 가능해진다.** 통제 어휘가 사이클마다 흔들리면 "지난 사이클 대비 outstanding 비율 변화"를 계산할 수 없다. 값의 안정성이 시간축 비교의 전제다.
- **enum + junction → 집계 축이 정의된다.** Department ← Assignment ← Employee(`jobLevel=senior`) → PerformanceReview(`rating=outstanding`) 라는 Complete HR Model의 그래프 경로는, junction이 경로를 만들고 enum이 필터 조건을 만드는 구조다. 어느 한쪽이 없으면 이 경로는 답을 내지 못한다.

정리하면, 네 개념은 **"무엇(identity) · 어떻게 연결(junction) · 언제(time) · 어떤 값으로(vocabulary)"** 라는 데이터 모델의 네 축이다. 그래서 Scenario Overview의 대표 질문 하나 — 최근 리뷰 사이클에서 outstanding을 받은 senior 직원이 가장 많은 부서 — 를 답하려면 네 개념이 동시에 필요하다: senior와 outstanding은 **enum**, "최근 사이클"과 "그 시점의 소속"은 **temporal**, 부서-사람 연결은 **junction**, 그 모든 참조가 끊기지 않게 붙잡아 주는 것은 **stable identifiers**.

---

## 암기 정리

- 네 개념 순서: **식별자 → 정션 → 시간 → 열거값** (ID → Junction → Time → Enum). "**아이지테**(IJTE)"로 기억.
- 각 개념의 대표 필드 한 개씩만 떠올려도 복원 가능: `employeeId` / `Assignment` / `startDate` / `rating`.
- 한 줄 요약: **안정된 키로 무엇인지 고정하고, 정션으로 다대다를 펼치고, 날짜로 이력을 남기고, enum으로 집계 어휘를 통제한다.**
