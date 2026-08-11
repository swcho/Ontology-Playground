# `reviewPeriod`와 `reviewDate`를 함께 두는 이유

## 카드 내용

- **Question**: `reviewPeriod`와 `reviewDate`를 함께 두는 이유는?
- **Answer**: `reviewPeriod`는 평가 대상 주기(예: 2024 H1)를, `reviewDate`는 평가가 이뤄진 실제 날짜를 나타낸다. 주기별 집계와 시점 질의를 각각 지원한다.

## 출발점: PerformanceReview의 속성 표

학습 자료의 Complete HR Model에서 `PerformanceReview`는 다음 네 속성을 갖는다.

| Property | Type | Identifier? |
|---|---|---|
| `reviewId` | string | ✓ |
| `reviewPeriod` | string | |
| `rating` | enum | |
| `reviewDate` | date | |

여기서 시간과 관련된 속성이 **두 개** 들어 있다는 점이 이 카드의 전부다. 처음 보면 중복처럼 느껴진다. "2024 H1"이라는 주기는 날짜 범위로 표현할 수 있고, 날짜만 있으면 그 날짜가 속한 반기를 계산할 수 있으니 하나로 충분해 보인다.

그렇지 않다. 두 속성은 **서로 다른 시간축**을 가리키기 때문이다.

## 핵심: 두 개의 시간축

| 속성 | 가리키는 것 | 시간 모델링 용어 | 예시 |
|---|---|---|---|
| `reviewPeriod` | 평가가 **대상으로 삼는 성과 기간** | valid time / business time (유효 시간) | `"2024 H1"` |
| `reviewDate` | 평가 **행위가 기록된 시점** | transaction time / record time (기록 시간) | `2024-07-18` |

- `reviewPeriod`는 **"무엇에 대한 평가인가"**를 말한다. 즉 직원의 성과가 실제로 발생한 세계의 기간이다.
- `reviewDate`는 **"언제 그 평가가 만들어졌는가"**를 말한다. 즉 조직의 프로세스가 실행된 시점이다.

이 둘은 논리적으로 독립이다. 하나의 값으로 다른 하나를 유도할 수 없다. 왜 유도가 불가능한지가 다음 절의 내용이다.

## `reviewDate`만으로는 왜 안 되는가 — 지연 평가

가장 흔한 실무 상황이다. 리뷰는 대상 기간이 끝난 **뒤에** 작성된다. 그리고 얼마나 뒤에 작성되는지는 일정하지 않다.

| reviewId | 직원 | `reviewPeriod` | `reviewDate` | 상황 |
|---|---|---|---|---|
| R-101 | 김 | `2024 H1` | 2024-07-05 | 정상 진행 |
| R-102 | 이 | `2024 H1` | 2024-07-12 | 정상 진행 |
| R-103 | 박 | `2024 H1` | **2025-03-20** | 매니저 공석으로 지연 작성 |
| R-104 | 최 | `2024 H2` | 2025-01-09 | 정상 진행 |

`reviewDate`만 가지고 "2024년 상반기 성과 평가"를 뽑으면 어떻게 되는가.

- `reviewDate BETWEEN 2024-01-01 AND 2024-06-30`으로 필터하면 → **한 건도 안 나온다.** 상반기 리뷰는 전부 7월 이후에 작성됐다.
- `reviewDate BETWEEN 2024-07-01 AND 2024-12-31`로 범위를 미루면 → R-101, R-102는 잡히지만 **R-103(박)이 빠진다.** 박의 2024 H1 평가는 존재하는데 집계에서 사라진다.
- 반대로 2025년 1~3월을 잡으면 R-103과 **R-104(2024 H2 평가)** 가 같은 버킷에 섞인다. 서로 다른 성과 기간의 평가가 한 덩어리로 집계된다.

즉 `reviewDate` 기준 구간 필터는 **어떤 구간을 잡아도 정답이 되지 않는다.** 작성 지연의 분포가 사람마다 다르기 때문에 "작성 시점 구간 → 성과 기간"의 매핑이 함수가 아니다.

`reviewPeriod = "2024 H1"`이라는 명시적 라벨이 있으면 이 문제가 사라진다. 지연 작성 여부와 무관하게 R-101, R-102, R-103이 정확히 한 코호트로 묶인다.

### 소급 수정(retroactive correction)

같은 논리가 재평가·이의제기 반영에도 적용된다. 박의 2024 H1 평가가 이의제기로 2025년 5월에 수정되면, 수정된 레코드의 `reviewDate`는 2025-05-xx가 되지만 `reviewPeriod`는 여전히 `"2024 H1"`이다. 성과 기간 라벨이 고정되어 있으므로 **과거 주기의 집계 결과가 나중에 조용히 바뀌지 않는다** — 어느 주기에 귀속되는지가 `reviewDate` 이동에 흔들리지 않기 때문이다.

## `reviewPeriod`만으로는 왜 안 되는가 — 시점·경과 질의

역방향도 성립한다. 주기 라벨만 있으면 답할 수 없는 질문들이 있다.

- **최근 평가 이후 경과 일수**: "마지막 평가를 받은 지 180일이 넘은 직원" → `MAX(reviewDate)`가 필요하다. `"2024 H1"`이라는 문자열로는 며칠이 지났는지 계산할 수 없다.
- **평가 누락/지연 탐지**: "대상 기간 종료 후 60일 안에 리뷰가 작성되지 않은 건" → 이건 `reviewPeriod`의 종료 시점과 `reviewDate`를 **함께** 봐야 나온다. 두 시간축의 차이 자체가 프로세스 준수 지표(compliance metric)가 된다.
- **특정 날짜 기준 스냅샷**: "2024년 9월 1일 시점에 우리가 알고 있던 평가 결과는 무엇인가" → 그 날짜 이전에 기록된 레코드만 봐야 하므로 `reviewDate <= 2024-09-01`. 감사(audit)와 재현 가능한 리포트에 필요하다.
- **평가 활동량**: "이번 달에 매니저들이 작성한 리뷰 건수" → 프로세스 부하 측정은 순수하게 `reviewDate` 기준이다.

정리하면 역할 분담은 이렇다.

| 질의 유형 | 사용 속성 | 예 |
|---|---|---|
| 주기 간 비교, 동일 주기 코호트 집계 | `reviewPeriod` | "2024 H1 vs 2024 H2 부서별 outstanding 비율" |
| "last review cycle" 정의 | `reviewPeriod` | 직전 주기 라벨로 필터 |
| 경과 시간 / 시점 스냅샷 / 누락 탐지 | `reviewDate` | "마지막 평가 후 경과 일수" |
| 프로세스 지연 측정 | 둘의 차이 | "기간 종료 → 작성"까지의 리드타임 |

## 학습 경로의 대표 질문에 적용하기

Scenario Overview가 내세운 질문은 이것이다.

> **"Which departments have the highest number of senior employees rated outstanding in the last review cycle?"**

여기서 **"in the last review cycle"** 은 `reviewDate`가 아니라 `reviewPeriod` 기준으로 해석되어야 한다. 이유는 앞의 지연 평가 예시 그대로다.

- "cycle(주기)"은 조직이 정의한 **평가 사이클**을 가리키는 비즈니스 개념이다. 작성 날짜의 구간이 아니다.
- `reviewDate` 기준으로 "최근 6개월"을 잡으면 박(R-103)의 2024 H1 평가와 최(R-104)의 2024 H2 평가가 섞여, "지난 사이클의 outstanding 수"라는 부서별 비교가 **주기가 뒤섞인 수치**가 된다.
- 부서 간 비교가 공정하려면 모든 직원이 **동일한 성과 기간**을 놓고 평가받은 결과를 세야 한다. 코호트의 동질성을 보장하는 것이 `reviewPeriod`다.

따라서 올바른 필터는 `reviewPeriod = '2024 H2'`(직전 주기 라벨)이고, `reviewDate`는 이 질문에 쓰이지 않는다. 반면 "지난 사이클 리뷰 중 아직 작성되지 않은 건은?"이라는 후속 질문은 `reviewPeriod`로 대상을 좁히고 `reviewDate`의 부재/지연을 보는 식으로 **둘을 조합**한다.

## `reviewPeriod`가 왜 string인가, 그리고 그 대가

속성 표에서 `reviewPeriod`의 타입은 `date`가 아니라 **string**이다. 이유가 있다.

- 주기는 **단일 시점이 아니라 구간**이다. `date` 하나로는 담을 수 없다.
- 주기는 **조직이 정의한 라벨**이다. `"2024 H1"`, `"FY25 Q3"`, `"2024 Annual"` 처럼 회사의 회계연도·주기 정책에 따라 형태가 다르고, 반기·분기·연간이 섞이기도 한다. 달력 날짜로 환원하면 이 정책적 의미가 사라진다.
- 학습 단계의 모델에서는 **사람이 읽을 수 있는 안정된 그룹 키**로 충분하다. 같은 라벨을 가진 리뷰들이 한 코호트라는 것만 보장되면 집계가 된다.

대가도 분명하다.

1. **정렬이 안 된다.** 문자열 사전순 정렬은 `"2024 H1"` < `"2024 H2"`는 맞게 나오지만, `"FY25 Q3"`와 `"2024 Annual"`이 섞이면 무의미하다. "직전 주기"를 코드로 계산하기 어렵다.
2. **구간 연산이 안 된다.** "2024 H1과 겹치는 Assignment" 같은 질의를 `reviewPeriod`로는 직접 못 한다. 문자열을 날짜 범위로 해석하는 로직이 애플리케이션 쪽에 숨는다.
3. **표기 규약(convention)이 필수다.** 누군가 `"2024 H1"`, 다른 누군가 `"2024-H1"`, `"H1 2024"`, `"2024년 상반기"`를 쓰면 코호트가 쪼개진다. 자유 문자열이므로 DB가 막아주지 않는다. 그래서 실무에서는 표기 규약을 문서화하거나 **enum / 별도 ReviewCycle 엔티티**로 승격시킨다.

### 대안: 구간으로 분해하거나 엔티티로 승격

모델이 성숙하면 다음 중 하나로 진화하는 게 자연스럽다.

- **분해**: `periodStart: date`, `periodEnd: date`를 추가한다. 그러면 정렬·구간 겹침 연산이 가능해지고, Assignment의 `startDate`/`endDate`와 직접 비교할 수 있다. `reviewPeriod` 라벨은 표시용으로 남긴다.
- **엔티티 승격**: `ReviewCycle` 엔티티(`cycleId`, `label`, `periodStart`, `periodEnd`, `status`)를 만들고 `PerformanceReview -> ReviewCycle` (many-to-one) 관계를 둔다. 라벨 표기가 한 곳에서 통제되고(자유 문자열 오염 방지), 주기 자체에 속성(제출 마감일, 사이클 상태)을 붙일 수 있다. 이는 학습 경로가 Assignment에서 쓴 것과 같은 사고 — **자기 속성을 가져야 하는 개념은 독립 엔티티로 꺼낸다** — 의 반복이다.

## bitemporal 모델링과의 연결

`reviewPeriod` / `reviewDate` 쌍은 데이터 모델링에서 오래된 패턴인 **bitemporal(이중 시간) 모델링**의 축소판이다.

| 시간축 | 의미 | HR 모델 대응 |
|---|---|---|
| valid time (유효 시간) | 사실이 현실 세계에서 참인 기간 | `reviewPeriod`, Assignment의 `startDate`/`endDate` |
| transaction time (기록 시간) | 시스템이 그 사실을 알게 된 시점 | `reviewDate` |

두 축을 모두 보관하면 두 종류의 질문에 각각 답할 수 있다.

- **"실제로 어땠는가"** (valid time 기준): 2024 H1의 성과는 어땠는가.
- **"우리가 그때 무엇을 알고 있었는가"** (transaction time 기준): 2024년 8월 승진 심사를 할 때 손에 있던 평가 데이터는 무엇이었나.

두 번째가 감사·재현성·의사결정 사후 검토에서 결정적이다. 8월 승진 심사 결정을 나중에 검토할 때, 3월에 소급 작성된 박의 리뷰(R-103)를 근거로 삼아 "왜 이 사람을 빠뜨렸나"라고 따지면 부당하다. `reviewDate`가 있으면 "그 시점에는 없던 데이터"임을 증명할 수 있다.

## Assignment의 `startDate`/`endDate`와의 관계

여기서 세 번째 시간 정보가 등장한다. 학습 자료의 Assignment는 `startDate`, `endDate`, `isPrimary`를 갖고, 대표 질문의 그래프 경로는 이렇다.

```
Department <- Assignment <- Employee -> PerformanceReview (rating=outstanding)
```

Employee와 Department가 **직접** 연결되지 않고 Assignment를 경유한다는 점이 중요하다. 부서 소속은 영구적 사실이 아니라 **기간을 가진 사실**이기 때문이다. 그리고 여기서 까다로운 귀속(attribution) 문제가 생긴다.

**시나리오**: 정 씨는 2024-01-01부터 Finance에 있었고, 2024-05-01에 Marketing으로 이동했다. 2024 H1 평가에서 outstanding을 받았고, `reviewDate`는 2024-07-10이다.

> "2024 H1에 outstanding을 받은 직원이 가장 많은 부서"에서 정 씨는 **Finance인가 Marketing인가?**

세 가지 해석이 모두 그럴듯하다.

| 해석 | 판단 기준 | 결과 | 성격 |
|---|---|---|---|
| 성과 기여 기준 | `reviewPeriod`와 겹치는 Assignment | Finance 4개월 + Marketing 2개월 → 안분 또는 최다 기간 부서 | valid time 정합 |
| 평가 시점 소속 기준 | `reviewDate`를 포함하는 Assignment | Marketing (7월 기준 소속) | transaction time 정합 |
| 현재 소속 기준 | `endDate IS NULL`인 Assignment | Marketing (또는 그 이후 부서) | 가장 단순, 가장 왜곡 |

정답은 하나가 아니고 **비즈니스가 정해야 하는 규칙**이다. 다만 세 가지 중 어느 것을 고르든, 고르는 행위 자체가 `reviewPeriod`와 `reviewDate`가 **분리되어 있어야** 가능하다. 시간 속성이 하나뿐이면 이 선택지가 아예 표현되지 않고, 구현자가 무의식적으로 "현재 소속" 같은 최악의 기본값을 쓰게 된다.

또한 이 문제는 `reviewPeriod`를 `periodStart`/`periodEnd`로 분해할 실질적 동기이기도 하다. "성과 기여 기준"을 구현하려면 `reviewPeriod`의 구간과 Assignment의 `[startDate, endDate)` 구간을 겹쳐봐야 하는데, `"2024 H1"`이라는 문자열과는 구간 연산을 할 수 없다.

## 정리

1. `reviewPeriod` = **평가 대상 성과 기간**(valid time), `reviewDate` = **평가 기록 시점**(transaction time). 서로 다른 시간축이므로 한쪽에서 다른 쪽을 유도할 수 없다.
2. 지연 평가와 소급 수정이 존재하는 순간, `reviewDate` 구간으로는 주기별 코호트를 정확히 만들 수 없다. → 주기별 집계는 `reviewPeriod`.
3. 경과 일수, 평가 누락 탐지, 특정 날짜 스냅샷은 실제 날짜가 필요하다. → 시점 질의는 `reviewDate`. 둘의 **차이**는 프로세스 지연 지표가 된다.
4. 대표 질문의 "in the last review cycle"은 `reviewPeriod` 기준 해석이 맞다. 그래야 부서 간 비교가 동일 성과 기간의 공정한 비교가 된다.
5. `reviewPeriod`가 string인 것은 조직 정의 라벨을 담기 위한 실용적 선택이지만, 정렬·구간 연산 불가라는 대가가 있다. 필요하면 `periodStart`/`periodEnd` 분해 또는 `ReviewCycle` 엔티티 승격으로 갚는다.
6. Assignment의 `startDate`/`endDate`와 만나면 "평가 기간 중 부서를 옮긴 직원을 어느 부서에 귀속시킬 것인가"라는 규칙 결정이 필요해진다. 두 시간축이 분리되어 있을 때만 이 선택을 명시적으로 다룰 수 있다.
