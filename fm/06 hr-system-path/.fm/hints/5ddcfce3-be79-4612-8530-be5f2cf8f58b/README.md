# Employee의 식별자로 `employeeId`를 쓰고 email을 쓰지 않는 이유

## 질문

Employee의 식별자로 `employeeId`를 쓰고 email을 쓰지 않는 이유는?

## 답

`employeeId`는 stable business identifier이지만 email은 mutable attribute다. 바뀔 수 있는 값을 primary key로 쓰면 참조가 깨진다.

원문(Organization Core)의 한 줄이 정확히 이 지점을 짚는다.

> `employeeId` is a stable business identifier. Avoid using mutable attributes like email as the primary key.

---

## 1. 식별자(identifier)가 만족해야 하는 세 가지 요건

온톨로지에서 어떤 속성을 식별자로 승격시킬 때는 아래 세 조건을 모두 통과해야 한다.

| 요건 | 의미 | 위반 시 증상 |
|---|---|---|
| **안정성 (stability / immutability)** | 엔티티가 존재하는 전 생애 동안 값이 바뀌지 않는다 | 값이 바뀌면 그 값을 가리키던 모든 참조가 허공을 가리킨다 |
| **유일성 (uniqueness)** | 같은 값이 두 인스턴스에 절대 붙지 않는다 | 두 사람이 한 사람으로 합쳐지거나(merge) 집계가 왜곡된다 |
| **도메인 의미 (domain meaning)** | 그 도메인이 공식적으로 인정·관리하는 키다 | 조직이 값을 통제하지 못하고, 외부 시스템 정합성을 보장할 수 없다 |

`employeeId`는 세 요건을 모두 만족한다. HR 부서가 발급하고, 발급 이후 값을 바꾸지 않는다는 규칙 아래 관리되며, "이 사람이 우리 조직의 누구인가"라는 도메인 의미를 그 자체로 갖는다. 그래서 payroll, HRIS, 스프레드시트, 매니저 노트가 흩어져 있어도 서로를 같은 사람으로 맞출 수 있는 공통 축이 된다.

email도 언뜻 보면 유일하고(회사 메일은 중복 발급하지 않는다) 도메인 의미도 있는 것처럼 보인다. 문제는 **안정성 하나에서 확실하게 실패**한다는 점이다. 그리고 식별자는 세 요건 중 하나만 무너져도 식별자 자격을 잃는다.

## 2. email이 안정성에서 실패하는 구체적 시나리오

email은 본질적으로 **연락 수단(attribute)** 이지 **정체성(identity)** 이 아니다. 값이 사람에 묶여 있지 않고, 사람의 "현재 상태"에 묶여 있다.

- **개명 / 결혼에 따른 성 변경** — `jisoo.kim@corp.com` → `jisoo.lee@corp.com`. 사람은 그대로인데 키가 바뀐다.
- **회사 도메인 변경** — 리브랜딩, 법인 분할, 인수합병으로 `@corp.com` → `@newcorp.com`. 전 직원의 키가 한꺼번에 바뀐다. 식별자가 사내 정치·법인 구조 변경에 종속되는 셈이다.
- **email 정책 변경** — `first.last@` 규칙에서 `flast@` 규칙으로, 또는 동명이인 처리 규칙 변경(`kim2@`)으로 기존 주소가 재편된다.
- **동명이인 충돌 재할당** — 같은 이름의 신입이 들어와 기존 사람의 주소를 재조정하는 경우.
- **퇴사자 email 회수 및 재할당** — 퇴사 후 주소를 회수하고, 나중에 같은 로컬파트를 **다른 사람**에게 다시 발급하는 조직이 흔하다. 이 순간 email은 안정성뿐 아니라 **유일성(시간축을 포함한 유일성)** 까지 깨진다. 과거 데이터의 `jisoo.kim@corp.com`과 현재의 `jisoo.kim@corp.com`이 서로 다른 사람이 된다.
- **재입사(rehire)** — 퇴사 후 재입사 시 새 주소를 받으면, 같은 사람의 과거 근무 이력과 현재 이력이 서로 다른 키로 갈라진다.
- **개인/회사 email 혼용, 다중 주소 보유** — 어떤 주소가 "그 사람"인지 판정 불가. alias가 여러 개면 식별자가 1:1이 아니게 된다.

이 카드의 핵심 대비는 다음 한 줄로 요약된다.

```
employeeId : 조직이 발급하고 절대 재사용하지 않는 값  → identity
email      : 사람의 이름·조직 도메인·재직 상태에 따라 변하는 값 → attribute
```

`email`은 Employee의 **일반 속성으로 두면 충분하다.** 지우라는 얘기가 아니다. 식별자 자리에서 내려오게 하라는 얘기다.

## 3. 식별자가 깨지면 HR 그래프에서 무슨 일이 벌어지는가

이 학습 경로의 모델은 Employee를 중심으로 두 개의 1:N 관계가 뻗어 나간다.

```
Department <- Assignment <- Employee -> PerformanceReview
                  |
                  v
              Position
```

- `Employee -> Assignment` (one-to-many): 부서·직무 배치 이력
- `Assignment -> Department` (many-to-one), `Assignment -> Position` (many-to-one)
- `Employee -> PerformanceReview` (one-to-many): 평가 이력

Assignment와 PerformanceReview는 **자기 자신을 스스로 설명하지 못한다.** Assignment 한 건은 "언제부터 언제까지, 어느 부서, 어느 직무"만 알고, "누구의"는 Employee 참조로만 안다. PerformanceReview도 "어느 리뷰 사이클에 어떤 rating"만 알고, "누구의"는 Employee 참조에 전적으로 의존한다.

여기서 Employee의 키를 email로 뒀다고 가정하고, 어떤 사람이 결혼해서 주소가 `jisoo.kim@corp.com` → `jisoo.lee@corp.com`으로 바뀌었다고 하자.

### (a) Dangling reference (매달린 참조)

Employee 레코드의 키만 새 주소로 갱신하고 하위 레코드를 못 따라가면, 기존 Assignment 5건과 PerformanceReview 6건은 여전히 `jisoo.kim@corp.com`을 가리킨다. 그 키를 가진 Employee는 이제 그래프에 없다. 참조가 끊긴 고아 레코드가 된다.

- "Which departments have the most senior employees?" (`Department <- Assignment <- Employee`) — 이 사람의 Assignment가 Employee에 붙지 못하므로 소속 부서 집계에서 사라진다.
- "Which teams have many outstanding reviews?" (`Department <- Assignment <- Employee -> PerformanceReview`) — 3-hop 경로 중 한 링크만 끊겨도 경로 전체가 끊긴다. 이 사람의 outstanding 평가가 어느 팀에도 집계되지 않는다.

### (b) 이력 단절 (history split)

반대로 새 주소로 Employee를 새로 만들고 기존 레코드를 남겨 두면, 한 사람이 그래프상 **두 사람으로 쪼개진다.**

- 이전 주소 쪽: 과거 Assignment/PerformanceReview만 달린 "유령 직원"
- 새 주소 쪽: 이력이 하나도 없는 "신입처럼 보이는 직원"

이 상태에서 "Which employees changed roles in the last year?" (`Employee -> Assignment -> Position`) 를 물으면, 이 사람의 실제 직무 전환은 두 Employee에 나뉘어 있어서 **전환으로 인식되지 않는다.** 승진 이력, 재직 기간, 평가 추이 같은 시계열 분석이 통째로 무너진다. Assignment를 junction entity로 분리해 힘들게 확보한 시간축 분석 능력이, 식별자 하나가 흔들려서 무의미해지는 구조다.

### (c) 퇴사자 email 재할당 시 — 잘못된 병합

가장 위험한 경우다. 퇴사자의 `jisoo.kim@corp.com`을 회수해 다른 신입에게 재발급하면, 신입의 새 Assignment와 PerformanceReview가 **퇴사자의 과거 이력에 붙는다.** 참조가 깨지는 것보다 나쁘다. 참조가 조용히 **틀린 사람에게 연결되고**, 쿼리는 에러 없이 그럴듯한 답을 내놓는다. 신입이 5년 근속자로 보이고, 퇴사자의 저성과 평가가 신입 이력에 섞인다. 보상·승진 논의에 쓰이는 데이터라면 실제 피해로 직결된다.

### (d) 감사·거버넌스 관점

식별자가 바뀌면 "이 평가가 정말 이 사람의 것인가"를 증명할 수 없다. HR 데이터는 보상·승진·법적 분쟁의 근거가 되므로 참조 추적 가능성(traceability)이 필수다. 원문 Key takeaways의 마지막 항목 "Keep identifiers stable and statuses controlled via enum values"가 governance-ready 구조를 언급하는 이유가 여기 있다.

정리하면 이렇다. **식별자의 안정성은 그 엔티티 하나의 문제가 아니라, 그 엔티티를 참조하는 모든 관계의 안정성이다.** Employee의 키가 흔들리면 Assignment와 PerformanceReview가 함께 흔들리고, 이 경로에서 배운 모든 그래프 질문이 답을 낼 수 없게 된다. 참조되는 쪽일수록 키를 보수적으로 골라야 한다.

## 4. natural key vs surrogate key

식별자 선택 논의의 표준 어휘를 함께 정리해 둔다.

| | natural key (자연 키) | surrogate key (대리 키) |
|---|---|---|
| 정의 | 도메인에 이미 존재하는, 의미 있는 값 | 식별 목적만으로 시스템이 생성한 무의미한 값 |
| 예 | `employeeId`(사번), 주민번호, ISBN, email | auto-increment ID, UUID/GUID |
| 장점 | 사람이 읽고 대조 가능, 외부 시스템과 소통 가능 | 절대 안 바뀜, 도메인 규칙 변경에 면역 |
| 약점 | 도메인 규칙이 바뀌면 값도 바뀔 수 있음 | 의미가 없어 사람이 대조 불가, 외부와 공유 어려움 |

`employeeId`는 natural key지만 **"좋은" natural key**다. 조직이 직접 발급하고, 불변·재사용 금지라는 규칙을 조직 스스로 통제할 수 있기 때문이다. email은 같은 natural key 후보지만 **"나쁜" natural key**다. 값이 사람 이름·회사 도메인·재직 상태라는 변하는 것들로부터 파생되기 때문이다.

여기서 나오는 일반 원칙: **식별자는 다른 무언가로부터 파생되어서는 안 된다.** 파생된 값은 원본이 바뀌면 함께 바뀐다. 이름에서 파생된 email이 정확히 그 경우다. 반대로 사번은 어떤 속성으로부터도 파생되지 않은, 그저 발급된 값이다.

## 5. 실무 관행: business identifier와 내부 surrogate key를 함께 둔다

성숙한 시스템은 둘 중 하나를 고르지 않고 **양쪽을 다 둔다.**

```
Employee
  internalId  : UUID          <- 시스템 내부 조인·FK 전용, 절대 노출·변경 없음
  employeeId  : "E-10482"     <- business identifier, 사람이 쓰고 외부 시스템과 맞추는 키
  email       : "..."         <- 그냥 속성. 조회 편의를 위해 unique 제약은 걸 수 있음
  name, hireDate, employmentStatus, jobLevel
```

역할 분담은 이렇다.

- **surrogate key(내부)**: Assignment·PerformanceReview의 참조가 실제로 물리는 대상. 여기가 절대 안 바뀌므로, 설령 사번 체계가 개편되는 최악의 경우에도 참조 그래프는 온전하다.
- **business identifier(`employeeId`)**: 화면·보고서·타 시스템 연동에서 쓰는 키. 사람이 "E-10482"라고 말하고 대조할 수 있다.
- **email**: 일반 속성. 로그인 식별용으로 unique 제약을 걸 수는 있지만, 그것은 "현재 시점의 유일성"일 뿐 식별자 자격과는 다르다. 값 변경 이력은 별도로 관리한다.

이 경로의 온톨로지처럼 개념 모델 층에서는 `employeeId` 하나만 identifier로 선언하는 것이 옳고 충분하다. 내부 surrogate key는 구현 층의 관심사이므로, 개념 모델을 굳이 복잡하게 만들지 않는다. 다만 실제 시스템으로 내려갈 때 이 이중 구조가 표준이라는 점은 알아 둘 만하다.

## 6. 같은 원칙이 다른 엔티티에도 그대로 적용된다

이 경로의 5개 엔티티가 전부 `~Id` 패턴을 쓰는 것은 우연이 아니다.

| 엔티티 | 식별자 | 식별자로 쓰면 안 되는 mutable 후보 | 이유 |
|---|---|---|---|
| Employee | `employeeId` | email, name | 개명·도메인 변경·재할당 |
| Department | `departmentId` | name | 조직 개편 시 부서명 변경("R&D" → "Product Engineering") |
| Position | `positionId` | title | 직급 체계 개편 시 직함 변경 |
| Assignment | `assignmentId` | (employeeId+startDate 조합) | 복합 자연 키는 구성 요소가 정정되면 함께 깨짐 |
| PerformanceReview | `reviewId` | (employeeId+reviewPeriod 조합) | 동일 사이클 재평가·정정 시 충돌 |

특히 Department의 `name`이 좋은 대조 사례다. 조직 개편은 email 변경보다 훨씬 자주 일어난다. 부서명을 키로 썼다면 개편 한 번에 그 부서를 가리키던 모든 Assignment가 끊기고, 예산·코스트센터 분석의 시계열이 단절된다. `departmentId`를 두면 이름은 그냥 바꾸면 되고 이력은 그대로 이어진다.

## 7. 한 줄 정리

`employeeId`는 조직이 발급·통제하는 불변·비재사용 키(stable business identifier)이므로 Assignment와 PerformanceReview가 안심하고 매달릴 수 있는 축이 된다. email은 개명·도메인 변경·정책 변경·퇴사 후 재할당으로 언제든 변하는 mutable attribute이므로, 식별자로 쓰면 참조가 끊기거나(dangling reference) 한 사람이 둘로 쪼개지거나(이력 단절) 서로 다른 두 사람이 하나로 합쳐진다(잘못된 병합). email은 속성으로 두고, 식별은 사번에 맡긴다.
