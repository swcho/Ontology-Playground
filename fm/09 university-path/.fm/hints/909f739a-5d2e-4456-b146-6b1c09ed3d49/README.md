# "소속 외 강의 교수" 판별 — 두 경로 비교 패턴

## 질문

"자기 학과 강좌 밖에서 가르치는 교수는?"은 어떻게 판별하는가?

## 답

**`Professor → Department`(소속)와 `Professor → Course → Department`(개설 학과)를 비교한다.** 두 결과가 다르면 소속 외 강의를 하는 교수다.

---

## 1. 원문에서의 위치

University System 온톨로지 3단계(Department 추가)의 "완성된 모델이 가능하게 하는 질문" 표에 그대로 등장한다.

| Question | Graph path |
|---|---|
| Which departments have the highest average student GPA? | Department → Course ← Enrollment ← Student (avg GPA) |
| **Which professors teach outside their department's courses?** | **Professor → Department vs Professor → Course → Department** |
| What is the enrollment rate for each department? | Department → Course ← Enrollment (count) / Course.maxEnrollment |
| Which departments have the most tenured faculty? | Department ← Professor (tenured=true, count) |

다른 세 질문은 **하나의 경로를 따라가서 집계**하는 형태다. 그런데 이 질문만 유독 `vs`라는 기호가 들어가 있다. 경로가 하나가 아니라 **둘**이고, 답은 집계값이 아니라 **두 경로 결과의 비교**에서 나오기 때문이다.

---

## 2. 사용되는 관계 3개

| 관계 | 방향 | 카디널리티 | 의미 |
|---|---|---|---|
| `belongs_to` | `Professor` → `Department` | **many-to-one** | 교수가 어느 학과 소속인가 |
| `teaches` | `Professor` → `Course` | **one-to-many** | 교수가 어떤 강좌를 가르치는가 |
| `offers` | `Department` → `Course` | **one-to-many** | 학과가 어떤 강좌를 개설하는가 |

주의할 점은 `offers`의 **방향**이다. 온톨로지에 정의된 화살표는 `Department → Course`인데, 우리가 필요한 건 "이 강좌를 개설한 학과"이므로 **역방향으로 거슬러 올라간다**. 그래서 답의 표기 `Professor → Course → Department`는 엄밀히는 이렇다.

```
Professor -[:teaches]-> Course <-[:offers]- Department
```

그래프 탐색에서 화살표 방향은 "정의된 방향"일 뿐, 질의는 양방향으로 자유롭게 통과할 수 있다. 이 점을 놓치면 "`Course → Department` 관계가 없는데요?"라고 막히게 된다.

---

## 3. 두 경로를 그림으로

```
                    ┌──────────────────────────────┐
                    │  경로 A : 소속 (home)         │
                    │  Professor -[belongs_to]->    │──▶ Department  (정확히 1개)
                    └──────────────────────────────┘
   Professor ●
                    ┌──────────────────────────────┐
                    │  경로 B : 개설 학과 (owner)   │
                    │  Professor -[teaches]->Course │──▶ Department  (0..N개)
                    │            <-[offers]-        │
                    └──────────────────────────────┘

   판정:  경로B의 결과 집합 ⊆ {경로A의 결과}   →  자기 학과 안에서만 강의
          경로B에 경로A 밖의 원소가 존재       →  ★ 소속 외 강의 교수
```

핵심은 **두 경로가 같은 종착 타입(Department)에 도달한다**는 것이다. 종착 타입이 같기 때문에 두 결과를 같은 축 위에 놓고 비교할 수 있다. 타입이 다르면 애초에 비교 자체가 성립하지 않는다.

---

## 4. 일반화: "동일 종착 타입 두 경로 비교" 패턴

이 문제는 University 온톨로지만의 특수 상황이 아니다. 온톨로지 설계에서 반복적으로 등장하는 하나의 **패턴**이다.

> **패턴 정의**
> 하나의 시작 노드 `X`에서 출발하는 서로 다른 두 경로 `P1`, `P2`가 **같은 타입 `T`** 에 도달할 때,
> `P1(X)`와 `P2(X)`의 **일치 / 불일치**가 그 자체로 의미 있는 사실이 된다.
> - 일치 → 정합적인 상태(normal case)
> - 불일치 → 예외, 교차, 위반, 혹은 발견해야 할 인사이트

두 경로는 보통 이런 대비를 이룬다.

| 경로 A | 경로 B |
|---|---|
| **선언된 것** (declared) — 명부, 소속, 계약 | **실제로 일어난 것** (observed) — 활동, 실적, 배정 |
| 짧은 경로 (1홉) | 긴 경로 (2홉 이상, 중간 엔티티 경유) |
| 단일 값 | 집합 |

University 사례에 대입하면, 경로 A는 "인사기록상 소속"(선언), 경로 B는 "실제 강의 활동에서 역산한 학과"(관측)이다. 불일치는 "선언과 실제가 어긋난 지점"을 정확히 짚어낸다.

### 같은 패턴의 다른 예

| 도메인 | 경로 A (선언) | 경로 B (실제) | 불일치의 의미 |
|---|---|---|---|
| University | Professor → Department | Professor → Course → Department | 소속 외 강의 |
| University | Student.major | Student → Enrollment → Course → Department | 전공 밖 수강 (부전공/교양) |
| HR | Employee → Team | Employee → Task → Project → Team | 타 팀 업무 지원 |
| 공급망 | Product → 담당부서 | Product → Plant → 관리부서 | 관리 주체 불일치 |
| 금융 | Account → Branch | Account → Transaction → Branch | 원거리 거래 = 이상 탐지 신호 |
| 의료 | Doctor → Department | Doctor → Procedure → Department | 진료과 외 시술 |

**이 패턴을 알아보는 신호**: 요구사항 문장에 "밖에서", "다른", "~와 달리", "불일치", "교차", "예상과 다른" 같은 표현이 들어 있으면 십중팔구 두 경로 비교 문제다.

---

## 5. 카디널리티 비대칭 — 이 문제의 진짜 함정

"두 결과를 비교한다"는 말은 쉽지만, **비교되는 두 값의 모양이 다르다**. 여기가 실수가 나오는 지점이다.

### 경로 A: 항상 값 하나 (스칼라)

```
Professor -[:belongs_to]-> Department      # many-to-one
```

`belongs_to`는 **many-to-one**이다. "여러 교수 → 하나의 학과". 교수 한 명 입장에서 보면 학과는 **정확히 1개**다. 그래서 경로 A의 결과는 항상 단일 값이다.

```
Prof.Kim ──belongs_to──▶ 컴퓨터공학과      # 끝. 더 없음.
```

### 경로 B: 값 여러 개 (집합)

```
Professor -[:teaches]-> Course             # one-to-many  → 강좌 N개
Course    <-[:offers]-  Department         # Course 입장에선 many-to-one → 강좌당 학과 1개
```

`teaches`는 **one-to-many**다. "한 교수 → 여러 강좌". 강좌마다 개설 학과를 되짚으면 학과가 나오고, 그 학과들은 **서로 다를 수 있다**. 그래서 경로 B의 결과는 **크기 0..N의 집합**이다.

```
Prof.Kim ──teaches──▶ CS101   ◀──offers── 컴퓨터공학과
         ──teaches──▶ CS340   ◀──offers── 컴퓨터공학과
         ──teaches──▶ MATH250 ◀──offers── 수학과        ★
         ──teaches──▶ STAT200 ◀──offers── 통계학과      ★

경로 B 결과 = {컴퓨터공학과, 수학과, 통계학과}   (중복 제거 후 3개)
```

### 그래서 비교는 "같다/다르다"가 아니라 집합 연산

| 잘못된 사고 | 올바른 사고 |
|---|---|
| A == B 인지 본다 | B의 각 원소가 A와 같은지 본다 (**포함 관계**) |
| 결과는 참/거짓 | 결과는 **정도(degree)** — 소속 외 강의가 몇 개인가 |

정확한 판정식은 이렇다.

```
소속외집합 = 경로B결과 \ { 경로A결과 }      # 집합 차집합

|소속외집합| = 0   →  자기 학과 안에서만 강의        (정상)
|소속외집합| > 0   →  ★ 소속 외 강의 교수
경로A결과 ∉ 경로B결과  →  자기 학과 강의를 하나도 안 함 (더 강한 신호)
```

즉 결과는 이진값이 아니라 **세 가지 상태**로 갈린다.

| 상태 | 조건 | 해석 |
|---|---|---|
| 완전 내부 | 경로B ⊆ {경로A} | 전형적인 전임 교수 |
| **부분 외부** | 경로B ∩ {경로A} ≠ ∅ 이고 경로B ⊄ {경로A} | 자기 학과 + 타 학과 강의 병행 |
| **완전 외부** | 경로A ∉ 경로B | 소속 학과 강의를 전혀 안 함 — 가장 의심스러운 케이스 |

이 카디널리티 비대칭 때문에 "소속 외 강의 비율"(`|소속외집합| / |경로B전체|`) 같은 파생 지표가 자연스럽게 나온다. 스칼라 vs 스칼라 비교였다면 나올 수 없는 지표다.

---

## 6. GQL 질의

### 6-1. 기본형 — 소속 외 강좌 하나하나 나열

```gql
MATCH (p:Professor)-[:belongs_to]->(home:Department),
      (p)-[:teaches]->(c:Course)<-[:offers]-(owner:Department)
WHERE owner.departmentId <> home.departmentId
RETURN p.name           AS professor,
       home.name        AS 소속학과,
       owner.name       AS 개설학과,
       c.courseId, c.title
ORDER BY p.name
```

두 경로를 콤마로 나란히 MATCH해서 같은 `p`에 묶는 것이 전부다. 마지막 `WHERE`가 곧 "두 결과가 다르면"이다.

> **`name`이 아니라 `departmentId`로 비교할 것.** `name`은 식별자가 아니다("전산학과"/"컴퓨터공학과"처럼 표기가 갈릴 수 있고 동명 학과도 가능하다). Department의 identifier는 `departmentId`이므로 비교의 기준도 그것이어야 한다. 두 경로 비교 패턴은 **종착 타입에 안정적인 식별자가 있을 때만** 신뢰할 수 있다.

### 6-2. 교수 단위 집계 — 비율까지

```gql
MATCH (p:Professor)-[:belongs_to]->(home:Department)
OPTIONAL MATCH (p)-[:teaches]->(c:Course)<-[:offers]-(owner:Department)
WITH p, home,
     COUNT(c) AS total_courses,
     SUM(CASE WHEN owner.departmentId <> home.departmentId THEN 1 ELSE 0 END) AS outside_courses
WHERE outside_courses > 0
RETURN p.name, p.rank, p.tenured,
       home.name AS 소속학과,
       outside_courses, total_courses,
       outside_courses * 1.0 / total_courses AS 소속외비율
ORDER BY 소속외비율 DESC, outside_courses DESC
```

두 번째 MATCH를 **`OPTIONAL MATCH`** 로 둔 이유가 중요하다. 일반 MATCH를 쓰면 **강좌를 하나도 안 가르치는 교수(연구년, 보직, 신임)가 결과에서 통째로 사라진다**. 경로 B의 하한이 0이라는 카디널리티 사실이 그대로 질의 작성 규칙이 된다.

### 6-3. "완전 외부" 교수만 — 소속 학과 강의를 전혀 안 하는 경우

```gql
MATCH (p:Professor)-[:belongs_to]->(home:Department)
MATCH (p)-[:teaches]->(:Course)<-[:offers]-(owner:Department)
WITH p, home, COLLECT(DISTINCT owner.departmentId) AS teaching_depts
WHERE NOT home.departmentId IN teaching_depts
RETURN p.name, home.name AS 소속학과, teaching_depts
```

`COLLECT`로 경로 B를 명시적인 **집합**으로 만든 뒤, 경로 A의 스칼라가 그 집합에 들어 있는지 본다. 5절의 카디널리티 비대칭을 코드로 옮기면 정확히 이 모양이 된다.

### 6-4. 학과 단위로 뒤집기 — "외부 인력에 의존하는 학과"

```gql
MATCH (owner:Department)-[:offers]->(c:Course)<-[:teaches]-(p:Professor)-[:belongs_to]->(home:Department)
WHERE owner.departmentId <> home.departmentId
RETURN owner.name AS 개설학과,
       COUNT(DISTINCT c) AS 외부강사_강좌수,
       COLLECT(DISTINCT home.name) AS 강사_소속학과들
ORDER BY 외부강사_강좌수 DESC
```

같은 두 경로인데 결과를 묶는 축(`p` → `owner`)만 바꾸면 질문의 주어가 "교수"에서 "학과"로 바뀐다. Department가 **hub entity**라서 가능한 회전이다.

---

## 7. 이 모델이 다루지 못하는 현실

두 경로 비교는 깔끔하지만, **불일치가 곧 이상(anomaly)은 아니다**. 이 온톨로지의 카디널리티 제약 때문에 정상적인 현실이 불일치로 잘못 잡히거나, 반대로 잡혀야 할 것이 안 잡힌다.

### (1) 겸임 · 공동임용 (joint appointment) — 가장 큰 구멍

`belongs_to`가 **many-to-one**이라서 교수는 학과를 **딱 하나만** 가질 수 있다. 그런데 현실에서는 흔하다.

- 컴퓨터공학과 + 인지과학과 공동임용 (50%/50%)
- 의대 교수의 생명공학과 겸임
- 경영대 교수의 데이터사이언스 대학원 겸직

모델은 이 중 하나를 **주 소속(primary)** 으로 강제 선택하게 만든다. 그러면 나머지 소속 학과에서 하는 지극히 정상적인 강의가 전부 **거짓 양성(false positive)** 으로 잡힌다. 5절의 `|소속외집합| > 0` 판정은 겸임 교수를 100% 오탐한다.

### (2) 교차 등재 강좌 (cross-listed course)

`offers`는 `Department → Course` one-to-many다. 뒤집어 보면 **강좌 하나의 개설 학과는 정확히 1개**다. 하지만 `CS/MATH 340 이산수학`처럼 두 학과가 공동 개설하고 학생이 어느 쪽으로든 수강 가능한 강좌는 대학에 널려 있다. 모델은 여기서도 학과 하나를 임의로 골라야 하고, 골라진 쪽이 아닌 학과 교수는 자기 강좌를 가르치면서도 "외부 강의"로 분류된다.

### (3) 팀 티칭 (co-teaching)

`teaches`는 `Professor → Course` one-to-many다. 즉 **강좌 하나에 교수 하나**다. 두 교수가 공동 강의하는 학제간 세미나는 표현 자체가 불가능하고, 등록되지 않은 쪽 교수의 강의 실적은 경로 B에서 통째로 누락된다 — **거짓 음성(false negative)**.

### (4) 시간 개념의 부재

`belongs_to`에도 `teaches`에도 유효기간이 없다. `semester`는 Enrollment에만 있다.

- 작년에 수학과에서 통계학과로 **이적한** 교수 → 과거 수학과 강의가 지금 기준으로 "외부 강의"로 뒤바뀐다
- 한 학기짜리 **초빙/객원** 강의와 상시 강의가 구분되지 않는다
- "지금" 소속 외 강의를 하는지, "예전에" 했는지 물어볼 수 없다

두 경로 비교는 **두 경로가 같은 시점을 가리킬 때만** 유효한데, 모델에 시점이 없으니 이 전제를 검증할 방법이 없다.

### (5) 불일치의 "이유"를 구분하지 못한다

불일치가 나와도 그게 무엇인지 모델은 말해주지 않는다.

| 실제 상황 | 모델의 출력 | 실제 의미 |
|---|---|---|
| 통계학과 교수가 전 학과 대상 기초통계 강의 | 소속 외 강의 | **정상** — service course |
| 학제간 프로그램(AI융합전공) 강의 | 소속 외 강의 | **정상** — 의도된 협력 |
| 교양/기초 과목 담당 | 소속 외 강의 | **정상** |
| 소속 학과 강의는 안 하고 남의 학과만 | 소속 외 강의 | **점검 필요** — 배정 오류 또는 데이터 오류 |
| 인사DB와 LMS 동기화 누락 | 소속 외 강의 | **데이터 품질 문제** |

즉 이 질의의 출력은 **결론이 아니라 조사 대상 목록**이다. 두 경로 비교 패턴 전반에 해당하는 성질이다 — 패턴은 "여기가 어긋났다"를 정확히 짚지만, "왜 어긋났는지"는 항상 도메인 지식이 필요하다.

### (6) 소속이 아예 없는 인력

`belongs_to`가 필수인지 선택인지 모델에 명시되어 있지 않다. 학과에 속하지 않은 겸임강사, 부설연구소/센터 소속 연구교수, 산학협력 실무자는 경로 A가 비어 있어서 `MATCH (p)-[:belongs_to]->(home)` 단계에서 조용히 탈락한다. **비교 자체가 불가능한 대상이 결과에서 사라지는 것**은 "위반 없음"과 다르다.

---

## 8. 모델을 고친다면 — junction entity로

재미있는 점은, 이 한계들의 해법이 이미 이 학습 경로 1단계에서 배운 **junction entity 패턴**이라는 것이다. Enrollment가 Student–Course many-to-many를 속성과 함께 풀어냈듯이.

```
현재:  Professor -[belongs_to]-> Department          (many-to-one, 겸임 불가)

개선:  Professor -[has]-> Appointment -[in]-> Department
       Appointment { appointmentId, fte(0.5), isPrimary(true/false),
                     startDate, endDate, appointmentType }
```

```
현재:  Department -[offers]-> Course <-[teaches]- Professor   (개설학과 1개, 담당교수 1명)

개선:  Department -[owns]-> CourseOffering <-[of]- Course
       CourseOffering -[taught_by]-> Professor
       CourseOffering { offeringId, semester, isPrimaryListing, crossListed }
```

이렇게 바꾸면 두 경로 비교의 성격 자체가 달라진다.

- 경로 A도 **집합**이 된다(겸임 학과 전부) → 판정이 `집합 vs 집합`의 차집합으로 대칭이 된다
- 두 경로 모두 `semester`로 **같은 시점에 정렬**할 수 있다 → (4)번 문제 해소
- `isPrimary` / `crossListed` 플래그로 **정상적 교차와 이상 교차를 구분**할 수 있다 → (5)번 문제 완화

```gql
-- 개선 모델에서: 2026 봄학기 기준, 어떤 소속으로도 설명되지 않는 강의
MATCH (p:Professor)-[:has]->(a:Appointment)-[:in]->(home:Department)
WHERE a.startDate <= date('2026-03-01') AND a.endDate >= date('2026-03-01')
WITH p, COLLECT(DISTINCT home.departmentId) AS home_depts
MATCH (p)<-[:taught_by]-(o:CourseOffering)<-[:owns]-(owner:Department)
WHERE o.semester = '2026-Spring'
  AND NOT owner.departmentId IN home_depts
RETURN p.name, home_depts, owner.name, o.offeringId
```

---

## 9. 한 줄 정리

| | |
|---|---|
| **패턴 이름** | 동일 종착 타입 두 경로 비교 (two-path divergence) |
| **경로 A** | `Professor -[belongs_to]-> Department` — 선언된 소속, **스칼라 1개** |
| **경로 B** | `Professor -[teaches]-> Course <-[offers]- Department` — 실제 강의로 역산한 학과, **집합 0..N개** |
| **판정** | 경로 B에서 경로 A를 뺀 차집합이 비어 있지 않으면 소속 외 강의 |
| **비교 키** | `name`이 아니라 식별자 `departmentId` |
| **질의 주의** | 경로 B는 비어 있을 수 있으므로 `OPTIONAL MATCH` |
| **한계** | 겸임(경로 A가 실제로는 복수), 교차 등재(경로 B의 소유 학과가 복수), 팀 티칭, 시점 부재 |
| **해법** | Appointment / CourseOffering junction entity로 reification |

> 기억할 문장: **"같은 곳에 도착하는 두 길을 놓고, 어긋난 지점을 찾는다."** 그리고 그 두 길의 **카디널리티가 다르면 비교는 등호가 아니라 포함 관계**로 해야 한다.
