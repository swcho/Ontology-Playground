# 부서별 outstanding 리뷰 질문이 가장 긴 경로를 갖는 이유

**Question**: 부서별 outstanding 리뷰 질문이 가장 긴 경로를 갖는 이유는?

**Answer**: 부서 정보는 Assignment를 통해서만, 평가 정보는 PerformanceReview를 통해서만 얻을 수 있어 Employee를 중심으로 양쪽으로 뻗어야 하기 때문이다.

---

## 1. HR 온톨로지의 관계 구조 복습

먼저 5개 엔티티가 어떤 변(edge)으로만 연결되어 있는지 정확히 확인해야 한다. 아티클이 정의한 관계는 다음 3개뿐이다.

| 관계 | 카디널리티 | 출처 |
|---|---|---|
| `Employee` -> `Assignment` | one-to-many | Assignments 문서 |
| `Assignment` -> `Department` | many-to-one | Assignments 문서 |
| `Assignment` -> `Position` | many-to-one | Assignments 문서 |
| `Employee` -> `PerformanceReview` | one-to-many | Complete HR Model 문서 |

그래프로 그리면 이런 모양이다.

```
Department          Position
     ^                 ^
     |                 |
     +--- Assignment ---+
              ^
              |
          Employee
              |
              v
     PerformanceReview
```

여기서 결정적인 사실 두 가지:

- **Department와 PerformanceReview를 직접 잇는 변이 없다.** 즉 "부서의 리뷰"라는 개념은 그래프에 1차적으로 존재하지 않는다.
- **Employee가 두 갈래의 유일한 접점이다.** 조직 축(Assignment -> Department/Position)과 평가 축(PerformanceReview)은 오직 Employee에서만 만난다.

## 2. 4개 예시 질의를 홉(hop) 수로 비교

아티클의 "Example graph questions" 표를 경로 길이 기준으로 정렬하면 왜 마지막 질문이 가장 무거운지 한눈에 보인다. 여기서 홉은 **경로에 등장하는 관계(변)의 개수**로 센다.

| # | 질문 | 그래프 경로 | 홉 수 | 경유 엔티티 수 | 성격 |
|---|---|---|---|---|---|
| 1 | 더 이상 활성 상태가 아닌 배정은? | `Assignment` (`endDate` 설정 or `isPrimary=false`) | **0 hop** | 1 | 단일 엔티티 속성 필터. 관계 순회 없음 |
| 2 | 시니어 직원이 가장 많은 부서는? | `Department <- Assignment <- Employee` (`jobLevel=senior`) | **2 hop** | 3 | 한 방향 선형 경로 (조직 축만) |
| 3 | 최근 1년간 역할이 바뀐 직원은? | `Employee -> Assignment -> Position` | **2 hop** | 3 | 한 방향 선형 경로 + 시계열 비교 |
| 4 | outstanding 리뷰가 많은 팀은? | `Department <- Assignment <- Employee -> PerformanceReview` (`rating=outstanding`) | **3 hop** | 4 | Employee를 꼭짓점으로 **양방향 분기** |

### 홉 수를 하나씩 뜯어보기

**질문 1 (0 hop)** — `endDate`와 `isPrimary`는 Assignment 자신의 속성이다. 관계를 타고 나갈 필요가 전혀 없다. Assignment를 별도 엔티티로 승격시킨 덕분에 "관계에 대한 질문"이 "속성 필터"로 축소된 사례다.

**질문 2 (2 hop)** — `jobLevel`은 Employee의 속성, 집계 축은 Department다. 두 엔티티 사이에는 직접 변이 없고 Assignment가 다리 역할을 하므로 `Employee -> Assignment`, `Assignment -> Department` 두 홉이 필요하다.

**질문 3 (2 hop)** — 마찬가지로 Employee와 Position 사이에도 직접 변이 없다. Assignment를 경유해 2홉. 추가로 "여러 Assignment 레코드를 날짜순으로 비교"하는 시계열 로직이 붙지만, 경로 길이 자체는 2홉이다.

**질문 4 (3 hop)** — 여기서 처음으로 두 개의 서로 다른 축이 동시에 필요해진다.

- 집계 기준(부서)을 얻으려면: `Employee -> Assignment -> Department` (2홉)
- 필터 조건(`rating=outstanding`)을 얻으려면: `Employee -> PerformanceReview` (1홉)

두 요구가 Employee라는 하나의 노드에서 갈라져 나가므로 총 3홉이 된다. 형태도 앞의 질문들과 다르다. 질문 2, 3은 일직선 경로였지만 질문 4는 Employee를 꺾이는 지점으로 하는 **V자(분기) 경로**다.

```
Department <--- Assignment <--- Employee ---> PerformanceReview
                                   ^                (rating=outstanding)
                                   |
                             여기서 꺾인다
```

## 3. 왜 이 경로를 줄일 수 없는가 — 구조적 이유

경로가 길어진 것은 질의를 잘못 짰기 때문이 아니라 **그래프 구조가 그것을 강제하기 때문이다.** 이유는 두 층으로 나뉜다.

### (1) Employee가 두 축을 잇는 유일한 절단점(cut vertex)

그래프 이론에서 어떤 정점을 제거했을 때 그래프가 두 개 이상의 연결 요소로 쪼개지는 정점을 **절단점(cut vertex)** 또는 **관절점(articulation point)** 이라고 부른다.

HR 온톨로지에서 Employee를 지우면 PerformanceReview는 나머지 그래프(Assignment, Department, Position)와 완전히 단절된다. 즉 **Employee는 절단점**이고, 조직 축과 평가 축 사이의 유일한 통로다.

이 사실이 곧 "부서별 평가 집계" 질의의 하한을 결정한다. 최단 경로 알고리즘이 어떤 전략을 쓰더라도, Department에서 PerformanceReview로 가는 모든 경로는 반드시 Employee를 지나야 한다. 이건 최적화로 우회할 수 있는 문제가 아니라 위상(topology) 자체의 제약이다.

역으로 말하면, 질문 4가 3홉인 것은 온톨로지가 "평가는 사람에게 달린 것이고, 부서 소속도 사람에게 달린 것이다"라는 **도메인 의미를 정직하게 반영한 결과**다. 조직도에서도 평가는 부서가 받는 게 아니라 사람이 받는다.

### (2) 부서 소속이 Employee에 직접 달려 있지 않고 Assignment를 한 번 더 거친다

여기서 홉이 하나 더 추가된다. 만약 Employee에 `departmentId` 속성이 직접 있었다면 경로는 `Employee -> PerformanceReview` 1홉이면 충분했고, 부서는 Employee의 속성으로 바로 그룹핑할 수 있었다.

그런데 아티클은 의도적으로 그렇게 하지 않았다. Assignment를 정션 엔티티(junction entity)로 끼워 넣은 이유는:

- 한 직원이 시간에 따라 부서/직무를 옮길 수 있다 (one-to-many)
- 한 부서는 여러 직원을 수용한다
- 한 포지션은 시간에 따라 다른 사람이 채울 수 있다
- `startDate`/`endDate`/`isPrimary`처럼 **관계 자신에게 속하는 속성**이 존재한다

즉 **한 홉의 추가는 이력 표현력을 얻기 위해 지불한 대가**다. Employee에 `departmentId`를 박아 넣는 순간 "Q2에 Finance 소속이었던 사람"이나 "올해 부서를 옮긴 사람" 같은 질문에 답할 수 없게 된다. 아티클이 강조한 "collapse하면 historical staffing changes, role transitions, open positions를 잃는다"가 바로 이 트레이드오프다.

정리하면 3홉은 다음 두 설계 결정의 합이다.

| 홉 | 근거 | 잃게 되는 것(이 홉을 없앤다면) |
|---|---|---|
| `Employee -> PerformanceReview` (1) | 평가는 사람에게 귀속된다 | 평가 이력의 주체가 모호해진다 |
| `Employee -> Assignment` (2) | 소속은 기간을 갖는 사실이다 | 시점별 소속, 부서 이동 이력, 겸직 |
| `Assignment -> Department` (3) | 부서는 재사용되는 조직 단위다 | 부서 단위 예산/코스트센터 분석 |

## 4. 긴 경로가 실무에서 치르는 대가

경로가 길어진 데는 정당한 이유가 있지만, 비용이 없다는 뜻은 아니다.

**질의 복잡도** — SQL로 내리면 조인이 3단으로 늘어난다. Department, Assignment, Employee, PerformanceReview 4개 테이블을 엮고 그 위에 집계를 올려야 한다. 그래프 질의 언어(Cypher, GraphQL 등)에서는 문법상 짧게 표현되지만 실행 계획상 카디널리티 폭발 지점이 늘어나는 것은 동일하다.

**시점 정합을 맞춰야 하는 지점의 증가** — 이게 가장 까다롭다. "outstanding 리뷰가 많은 팀"에서 *어느 시점의* 팀인지가 자동으로 결정되지 않는다.

- 리뷰를 받았던 당시(`reviewDate`)의 소속 부서인가?
- 지금(`endDate is null` 또는 `isPrimary=true`) 소속된 부서인가?

두 답이 다를 수 있다. 예를 들어 2025 H2에 Engineering에서 outstanding을 받고 2026년에 Product로 옮긴 직원은, 첫 번째 해석에서는 Engineering의 성과로, 두 번째 해석에서는 Product의 성과로 계상된다. 올바른 이력 기준 집계라면 `Assignment.startDate <= PerformanceReview.reviewDate <= coalesce(Assignment.endDate, 무한)` 같은 **시간 구간 조건**을 조인 술어에 명시해야 한다. 홉이 늘어난다는 것은 곧 이런 시점 정렬을 맞춰야 하는 접합부가 늘어난다는 뜻이다.

**겸직 시 중복 계상** — Assignment가 one-to-many이므로 한 직원이 동시에 두 부서에 배정될 수 있다(그래서 `isPrimary`가 존재한다). 이때 Department로 그룹핑해 리뷰 수를 세면 **같은 리뷰가 두 부서에 각각 카운트**된다. 전사 합계가 실제 리뷰 수보다 커지는 전형적인 팬아웃(fan-out) 오류다. 대응 방법은 목적에 따라 갈린다.

- `isPrimary=true`로 제한해 단일 소속만 인정 (합계 보존, 겸직 기여 누락)
- 부서별로 1/n 분수 배분 (합계 보존, 해석 복잡)
- 중복을 허용하되 "부서 관점 지표"임을 명시 (합계 미보존)

어느 쪽이든 **집계 전에 결정해야 하는 정책**이며, 온톨로지가 자동으로 답해주지 않는 부분이다.

## 5. 그렇다면 비정규화해야 할까 — 신중하게

경로를 짧게 만드는 두 가지 흔한 유혹이 있다. 둘의 성격은 전혀 다르다.

### (a) Employee에 `departmentId` 캐싱 — 신중히

"현재 소속 부서"를 Employee에 중복 저장하면 질문 4가 2홉으로 줄고 질문 2도 1홉이 된다. 성능상 매력적이지만 대가가 크다.

- **진실의 출처가 둘로 갈라진다.** Assignment가 바뀔 때마다 Employee를 동기화해야 하고, 동기화가 깨지면 두 값이 불일치한다. 어느 쪽이 정답인지 판단할 근거가 사라진다.
- **"현재"만 표현할 수 있다.** 과거 시점 질의는 여전히 Assignment를 타야 하므로, 같은 질문이 시점에 따라 다른 경로를 쓰는 이원 구조가 생긴다.
- **겸직을 표현할 수 없다.** 단일 스칼라 필드는 다중 배정을 담지 못한다.

따라서 이건 도입한다면 "파생 캐시임을 명시하고 Assignment로부터 자동 재계산되는 읽기 전용 뷰"로 다루는 것이 옳다. 온톨로지의 개념 모델을 바꾸는 게 아니라, 물리 계층의 최적화(구체화 뷰, materialized view)로 국한하는 접근이다.

### (b) PerformanceReview에 `departmentId` 스냅샷 저장 — 오히려 유용할 수 있다

같은 비정규화처럼 보이지만 성격이 다르다. "이 리뷰가 작성된 시점에 이 직원이 소속했던 부서"를 리뷰 레코드에 박아두는 것은 **캐시가 아니라 사실의 기록**이다.

- 리뷰는 특정 시점에 확정되는 이벤트이므로, 그 시점의 맥락(부서, 직급, 매니저)은 나중에 바뀌지 않아야 하는 정보다. 회계 문서에 당시 환율을 기록해 두는 것과 같은 논리다.
- 앞서 본 시점 정합 문제가 사라진다. "리뷰 당시 부서 기준" 집계가 조인 없이, 해석의 모호함 없이 가능해진다.
- 조직 개편으로 부서가 통폐합되거나 `status`가 비활성으로 바뀌어도 과거 집계가 재현 가능하다. Assignment를 타고 역추적하는 방식은 조직 개편 이력이 온전히 남아 있어야만 동작한다.
- 겸직이었다면 스냅샷 시점에 이미 "어느 부서 소속으로 평가받았는지"를 결정해 기록하게 되므로, 중복 계상 문제도 데이터 생성 시점에 해소된다.

이런 패턴을 데이터 웨어하우스에서는 팩트 테이블에 차원 값을 고정 기록하는 방식으로 다루고, 차원 쪽 이력 관리는 SCD Type 2(변경 이력을 새 행으로 쌓는 기법)에 대응한다. Assignment의 `startDate`/`endDate` 구조가 이미 SCD Type 2와 같은 발상이다.

**핵심 구분**: (a)는 *현재 상태의 중복*이라 시간이 지나면 틀려질 수 있어 위험하고, (b)는 *과거 시점의 확정 사실*이라 시간이 지나도 틀려지지 않으며 오히려 이력 보존에 기여한다. 비정규화를 일괄적으로 금기시하거나 일괄적으로 허용하는 대신, "중복하는 값이 변할 수 있는 값인가"를 기준으로 판단해야 한다.

## 6. 한 줄 정리

Department와 PerformanceReview 사이에는 직접 변이 없고 Employee만이 두 축의 유일한 접점(절단점)이므로 경로는 반드시 Employee를 경유해야 하며, 여기에 부서 소속이 이력 표현을 위해 Assignment를 한 번 더 거치는 구조가 겹쳐 3홉이 된다. 이 길이는 비효율이 아니라 "사람이 평가받고, 소속은 기간을 갖는다"는 도메인 사실을 정직하게 표현한 대가다.

## 관련 개념

- **정션 엔티티(junction entity)**: 관계 자신이 속성을 가질 때 관계를 엔티티로 승격시키는 패턴. Student-Course via Enrollment, Customer-Product via Order line item과 동일한 구조.
- **절단점 / 관절점(cut vertex / articulation point)**: 제거하면 그래프가 분리되는 정점. 온톨로지에서는 서로 다른 관심 축을 잇는 허브 엔티티가 대개 이 역할을 한다.
- **팬아웃(fan-out) 중복 집계**: one-to-many 관계를 타고 조인한 뒤 상위 차원으로 집계할 때 하위 사실이 여러 번 계상되는 현상.
- **시점 정합(temporal alignment)**: 서로 다른 시점 축을 가진 엔티티를 조인할 때 구간 조건으로 시점을 맞추는 문제.
