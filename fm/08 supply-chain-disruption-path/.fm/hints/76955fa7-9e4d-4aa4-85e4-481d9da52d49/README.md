# 자연어 질의의 '그라운딩(grounding)'이란?

> **Q.** 자연어 질의가 온톨로지에 '그라운딩(grounding)'된다는 것은 무슨 의미인가?
>
> **A.** 에이전트가 자유 텍스트를 추측으로 답하지 않고, 온톨로지의 엔터티·속성·관계에 대응시켜 실제 데이터를 탐색해 답을 만든다는 뜻이다. enum과 식별자가 명확할수록 그라운딩 정확도가 올라간다.

---

## 1. 한 줄 정의

**그라운딩 = 사람의 말 → 스키마의 좌표로 옮기는 번역 작업.**

사용자가 던진 문장은 형식이 없는 자유 텍스트다. 그라운딩은 그 문장의 각 조각을
- 어떤 **엔터티(entity)** 를 조회할 것인가
- 어떤 **속성(property)** 으로 필터/계산할 것인가
- 어떤 **관계(relationship)** 를 따라 이동할 것인가

로 확정하는 과정이다. 확정이 끝나면 답은 LLM의 "기억"에서 나오지 않고, **온톨로지 위의 실제 레코드 탐색 결과**에서 나온다. asset이 "Fabric IQ compatibility **for data agent grounding**"이라고 표현한 것이 바로 이 능력이다.

핵심은 방향이다. 그라운딩은 "그럴듯한 문장을 생성"하는 게 아니라 **"실행 가능한 탐색 계획을 생성"** 하는 것이다.

---

## 2. 예시 1 — "What's our supply chain risk exposure right now?"

asset의 원문 흐름:

```
User: "What's our supply chain risk exposure right now?"
  ↓
Data Agent grounds query against your ontology:
  1. Find all Supplier records with singleSourced=true
  2. For each, find Components they supply
  3. Trace to ProductLines using those components
  4. Calculate revenueAtRisk for each ProductLine
  5. Return ranked list by revenueAtRisk
```

### 자연어 조각 → 온톨로지 요소 매핑

| 자연어 조각 | 해석된 의도 | 매핑된 온톨로지 요소 | 종류 |
|---|---|---|---|
| "our supply chain" | 우리가 관리하는 공급망 네트워크 = Tier 1 엔터티들 | `Supplier`, `Component`, `ProductLine` | 엔터티 |
| "risk **exposure**" | 리스크 증폭기 = 대체 공급원이 없는 공급사 | `Supplier.singleSourced = true` (boolean) | 속성 필터 |
| "supply chain" (연결성) | 공급사가 무엇을 공급하는지 | `Supplier —supplies→ Component` (1:N) | 관계 탐색 |
| "supply chain" (하류 영향) | 그 부품이 어떤 제품군에 쓰이는지 | `Component —usedIn→ ProductLine` (M:N) | 관계 탐색 |
| "exposure"의 정량화 | 얼마를 잃는가 | `ProductLine.annualRevenue`, `Component.daysOfSupplyOnHand` → `revenueAtRisk` | 속성 계산 |
| "**right now**" | 가정된 시나리오가 아니라 현재 재고·상태 스냅샷 | `daysOfSupplyOnHand`, `productionStatus`, `assessedDate`(datetime) | 시점 기준 |
| (암묵적) "무엇부터 봐야 하나" | 우선순위 정렬 | `revenueAtRisk` 기준 rank | 정렬 키 |

**주목할 점**: 사용자 문장에는 `singleSourced`라는 단어가 단 한 번도 등장하지 않는다. 그런데도 에이전트가 그 속성을 고른다. "risk exposure"라는 비즈니스 표현이 온톨로지에서 `singleSourced=true`라는 **검증 가능한 술어**로 착지(ground)했기 때문이다. 이것이 그라운딩의 본질 — 모호한 비즈니스 언어를 스키마가 정의한 정확한 술어로 고정하는 것.

그리고 5단계 중 2·3단계는 **관계를 따라 걷는(traversal)** 단계다. 순수 텍스트 검색으로는 절대 나올 수 없는 답이 여기서 나온다. "$180M / 4-9일"이라는 숫자는 문서에 쓰여 있던 문장이 아니라, 그래프를 걸어가며 집계한 결과다.

---

## 3. 예시 2 — "Which alternatives are approved for ChipX?"

asset의 원문 흐름:

```
User: "Which alternatives are approved for ChipX?"
  ↓
Agent Query:
  AlternativeSupplier WHERE:
    canReplace.Supplier.name = "ChipX Corp"
    AND qualificationStatus = "Approved"
```

### 자연어 조각 → 온톨로지 요소 매핑

| 자연어 조각 | 해석된 의도 | 매핑된 온톨로지 요소 | 종류 |
|---|---|---|---|
| "alternatives" | 백업 공급사 레코드 | `AlternativeSupplier` (Tier 4 엔터티) | 엔터티 = 조회 대상 |
| "**approved**" | 승인 완료 상태 (Pre-qualified / Pending Audit / Not Qualified 아님) | `qualificationStatus = "Approved"` | enum 값 필터 |
| "**for** ChipX" | "ChipX를 대신할 수 있는" 방향성 | `canReplace` 관계 (M:1) | 관계 조인 |
| "ChipX" | 엔터티 인스턴스 해소(entity resolution) | `Supplier.name = "ChipX Corp"` (내부적으로 `supplierId="SUPP-00456"`) | 식별자 해소 |
| (반환 필드) 의사결정 근거 | 쓸 수 있는가 / 얼마나 비싼가 | `capacityAvailable`, `pricePremiumPercent` | 속성 투영 |

여기서 세 종류의 그라운딩이 한 문장 안에 동시에 일어난다.

1. **엔터티 그라운딩** — "alternatives"라는 일상어를 `AlternativeSupplier` 타입으로.
2. **속성/enum 그라운딩** — "approved"를 자유 텍스트 매칭이 아니라 `qualificationStatus` enum의 정확히 한 값으로. `qualificationStatus`는 Pre-qualified/Approved/Pending Audit/Not Qualified 4값 enum이므로, "approved"는 오직 하나에만 착지한다. 만약 이 속성이 자유 텍스트였다면 "approved", "Approved", "OK", "승인됨", "approved (conditional)"이 뒤섞여 필터가 무너진다.
3. **관계 그라운딩** — "for"라는 전치사를 `canReplace`라는 방향성 있는 관계로. 방향이 중요하다. `canReplace`는 `AlternativeSupplier → Supplier` (M:1)이므로 "ChipX를 대체할 후보들"이 맞게 나온다. 방향을 뒤집으면 무의미한 결과가 된다.
4. **인스턴스 그라운딩** — "ChipX"(별칭/약칭)를 실제 레코드 `"ChipX Corp"` / `SUPP-00456`으로 해소. 사용자는 절대 `SUPP-00456`이라고 타이핑하지 않는다.

---

## 4. 그라운딩이 없으면 어떻게 되는가

같은 질문에 세 가지 답이 나온다.

| | (A) 순수 LLM 추측 | (B) RAG(텍스트 검색) | (C) 온톨로지 그라운딩 |
|---|---|---|---|
| 답의 출처 | 학습된 사전 지식 / 통계적 그럴듯함 | 문서 청크의 문장 | 실제 엔터티 레코드 |
| "risk exposure" 처리 | 공급망 리스크 일반론을 서술 | "risk"가 포함된 문단 검색 | `singleSourced=true` 필터로 실행 |
| "ChipX 승인 대체사" | 존재하지 않는 공급사를 만들어낼 수 있음(환각) | ChipX가 언급된 문단은 찾아도 승인 상태 최신값은 보장 못 함 | `canReplace` + `qualificationStatus="Approved"`로 정확한 3건 |
| 관계 다단 추적 | 불가 (공급사→부품→제품군 실제 연결 모름) | 불가 (문서에 그 경로가 문장으로 적혀 있어야만) | 가능 (그래프 traversal) |
| 집계·계산 | 숫자를 지어냄 | 문서에 있는 숫자만 인용 | `annualRevenue / 365 * daysOfSupplyOnHand` 실시간 계산 |
| 최신성 | 학습 시점 | 색인 시점 | 데이터 시점 ("right now") |
| 검증 가능성 | 없음 | 출처 문단 | 질의 + 레코드 ID (`SUPP-00456`, `ALTSUPP-00789`) 단위 감사 가능 |
| 누락 여부 | 알 수 없음 | 알 수 없음 (검색 recall에 의존) | 완결적 — 조건을 만족하는 전체 집합 |

핵심 차이는 **"그럴듯함"과 "완결성"** 이다. RAG는 관련 있어 보이는 텍스트를 가져오지만, "조건을 만족하는 모든 항목"을 보장하지 못한다. 47개 부품 중 45개만 찾아도 RAG는 자신 있게 답한다. 그라운딩된 질의는 조건이 곧 집합의 정의라서, 결과가 전체 집합이다. 리스크 대응처럼 **하나를 놓치면 생산라인이 멈추는** 도메인에서 이 차이는 결정적이다.

또 하나: (A)/(B)는 실행으로 이어질 수 없다. 그라운딩된 답은 `MitigationAction` 생성, 조달 알림 발송, 생산 일정 갱신 같은 **쓰기 동작**의 입력으로 바로 쓸 수 있다. 대상이 ID로 특정되기 때문이다.

---

## 5. 온톨로지 품질이 그라운딩 정확도를 좌우한다

그라운딩은 에이전트 혼자 잘해서 되는 일이 아니다. **착지할 활주로(스키마)가 잘 깔려 있어야** 한다.

### (1) enum — 어휘를 유한하게 닫아준다

asset은 속성 타입 표에서 `enum`의 용도를 "Classification, decision trees"로 명시한다. enum이 있으면 자연어의 형용사가 유한 집합 중 하나로 결정적으로 매핑된다.

| enum 속성 | 값 | 그라운딩되는 자연어 표현 |
|---|---|---|
| `qualificationStatus` | Pre-qualified / **Approved** / Pending Audit / Not Qualified | "approved", "쓸 수 있는", "검증된" |
| `severity` | Critical / High / Medium / Low | "심각한", "급한", "critical" |
| `DisruptionEvent.type` | Natural Disaster / Geopolitical / Financial / Logistics / Quality Recall / Pandemic / Cyber Attack | "지진", "관세", "리콜", "해킹" |
| `criticalityLevel` | Critical / High / Medium / Low | "핵심 부품", "중요한" |
| `productionStatus` | Active / At Risk / Halted / Discontinued | "멈춘 라인", "위험한 제품군" |
| `MitigationAction.status` | Proposed / Approved / In Progress / Completed / Cancelled | "아직 안 끝난 조치" |

주의: `MitigationAction.status`와 `AlternativeSupplier.qualificationStatus`는 **둘 다 "Approved" 값을 가진다.** 그래서 "approved된 것 보여줘"라는 질의는 어느 엔터티를 묻는지에 따라 다르게 그라운딩되어야 한다. 예시 2에서 "alternatives"라는 단어가 엔터티를 먼저 확정해 준 덕분에 `qualificationStatus`가 올바르게 선택됐다. **enum 값이 겹칠 때는 엔터티 그라운딩이 먼저 확정되어야 한다**는 교훈.

반대로 이 속성이 자유 텍스트라면 — 같은 뜻의 표기가 흩어지고, 에이전트는 `LIKE '%approv%'` 같은 추측성 매칭으로 후퇴하며, 그 순간 완결성 보장이 깨진다.

### (2) 식별자 — 인스턴스를 유일하게 지목한다

asset은 7개 엔터티 전부에 ID를 부여하고 "These IDs are how you and your agents refer to specific instances in queries and reports"라고 못 박는다.

```
Supplier            → supplierId       ("SUPP-00456")
Component           → componentId      ("COMP-SEM-0821")
ProductLine         → productLineId    ("PL-LAP-2024")
DisruptionEvent     → eventId          ("DISR-202405-TAIWAN-001")
RiskAssessment      → assessmentId     ("RA-20240501-SEM-001")
MitigationAction    → actionId         ("MA-20240501-ALT-SUPP")
AlternativeSupplier → altSupplierId    ("ALTSUPP-00789")
```

ID가 있으면 "ChipX" → `SUPP-00456`으로 한 번 해소한 뒤, 이후 모든 단계(부품 47개 → 제품군 12개 → 평가 → 조치)가 같은 앵커를 공유한다. 이름만으로 조인하면 "ChipX Corp" vs "ChipX Corporation" vs "ChipX Europe" 같은 표기 충돌이 다단 추적 중간에서 경로를 끊는다. 특히 `ChipX Corp`(primary supplier)와 `ChipX Europe`(alternative supplier)는 이름이 겹치므로, 이름 매칭만 쓰면 예시 2가 자기 자신을 대체 후보로 반환하는 오류가 나기 쉽다.

ID 접두어의 의미도 크다. `DISR-202405-TAIWAN-001`처럼 날짜·지역이 인코딩된 ID는 "지난 5월 대만 사건"이라는 자연어를 훨씬 쉽게 착지시킨다.

### (3) 관계 명명 — 전치사를 방향성 있는 엣지로 바꾼다

`supplies`, `usedIn`, `affects`, `triggers`, `recommends`, `activates`, `canReplace` — 모두 **동사구**로 읽힌다. 이 명명 덕분에 자연어의 동사·전치사가 그대로 엣지에 대응한다.

| 자연어 | 관계 | 카디널리티 |
|---|---|---|
| "~가 공급하는" | `supplies` | 1:N |
| "~에 들어가는 / 쓰이는" | `usedIn` | M:N |
| "~가 타격을 준" | `affects` | M:N |
| "~때문에 나온 평가" | `triggers` | 1:N |
| "~가 권고한 조치" | `recommends` | 1:N |
| "~를 가동시킨" | `activates` | M:N |
| "~를 대신할 수 있는" | `canReplace` | M:1 |

만약 이것들이 `rel_1`, `link_a`, `supplierComponentMapping` 같은 이름이었다면 에이전트는 어느 엣지를 타야 하는지 스키마 설명문을 추론해야 하고, 그만큼 오탐이 늘어난다. **카디널리티 선언(M:1, 1:N, M:N)** 도 그라운딩 재료다. `canReplace`가 M:1임을 알기 때문에 에이전트는 "ChipX의 대체 후보는 여럿일 수 있다"는 결과 형태(리스트)를 미리 알고 질의를 짠다.

### (4) 타입 — 연산 가능성을 알려준다

`integer`/`decimal`/`date`/`datetime`/`boolean` 타입 선언이 있어야 "지금(right now)"을 `datetime` 비교로, "가장 큰 손실"을 `decimal` 정렬로, "3일 남은"을 `integer` 임계값으로 처리할 수 있다. 타입이 전부 string이면 "3일 이하"가 문자열 비교로 망가진다.

**정리하면**: 그라운딩 정확도는 모델 크기보다 스키마 위생(schema hygiene)에 더 민감하다. enum·식별자·관계명·타입은 "문서 정리"가 아니라 **에이전트가 실제로 소비하는 인터페이스**다.

---

## 6. Trace accuracy(> 95%)와의 연결

asset의 Continuous improvement 지표표:

| Metric | Calculation | Goal |
|--------|-------------|------|
| Detection speed | Hours from disruption to RiskAssessment | < 1 hour |
| **Trace accuracy** | **% of actual affected components identified** | **> 95%** |
| Impact estimate accuracy | Estimated vs. actual revenue at risk | ±10% |
| Time to mitigation | Hours from assessment to MitigationAction execution | < 2 hours |
| Cost efficiency | Actual cost vs. estimated cost of actions | ±5% |
| Revenue protection rate | % of at-risk revenue protected by actions | > 80% |

**Trace accuracy는 그라운딩 품질의 직접 측정치다.**

정의를 그대로 읽으면 "실제로 영향받은 부품 중 몇 %를 찾아냈는가"다. Phase 2에서 에이전트는 `Supplier → supplies → Component`로 **47개 부품**, 이어서 `Component → usedIn → ProductLine`으로 **12개 제품군**을 도출했다. 만약 실제 영향 부품이 50개였다면 trace accuracy는 94% — 목표 미달이다. 놓친 3개는 어디서 새는가? 거의 항상 그라운딩 계층이다.

| 누락 원인 | 어느 그라운딩이 실패했나 | 증상 |
|---|---|---|
| 공급사 이름 표기 불일치로 조인 실패 | 식별자 그라운딩 | 공급사 1곳이 아예 후보에서 빠짐 |
| `country="Taiwan"` vs `"TW"` vs `"Taiwan, ROC"` | enum/정규화 부재 | Phase 1에서 3곳 중 2곳만 잡힘 |
| `supplies` 엣지가 누락된 부품 레코드 | 관계 데이터 완결성 | 부품이 추적 그래프에 없음 |
| 2차·3차 공급사 경로(`tier` Tier 2/3) 미고려 | 관계 탐색 깊이 | 간접 의존 부품 누락 |
| M:N 관계를 1:N으로 잘못 걸음 | 카디널리티 오해 | 제품군 일부 누락 |
| "affected"를 텍스트 유사도로 판단 | 그라운딩 자체가 없음 | 정확도가 통제 불가로 요동 |

그리고 이 지표들은 **연쇄한다.**

```
그라운딩 실패
  → Trace accuracy 하락 (부품 누락)
  → Impact estimate accuracy 하락 (누락 부품의 revenueAtRisk 미집계 → ±10% 초과)
  → 잘못된 MitigationAction 우선순위
  → Revenue protection rate 하락 (< 80%)
```

즉 Trace accuracy는 파이프라인의 **상류 게이트**다. 여기서 95%를 못 지키면 하류의 금액·비용·보호율 지표는 애초에 의미가 없다. asset이 "Revenue protected: ~$100M of $127M exposure"라고 자랑할 수 있는 근거는, 그 $127M이 그라운딩된 탐색으로 **빠짐없이** 집계됐다는 가정이다.

역으로, Trace accuracy를 측정할 수 있다는 사실 자체가 그라운딩의 부산물이다. 에이전트가 "부품 47개, ID 목록 이러함"이라고 특정했기 때문에 사후에 실제값과 대조가 가능하다. 순수 LLM이 산문으로 답했다면 무엇을 놓쳤는지 세는 것조차 불가능하다. **그라운딩은 정확도를 높이는 동시에, 정확도를 측정 가능하게 만든다.**

---

## 7. 요약 카드

- **그라운딩** = 자유 텍스트를 온톨로지의 엔터티·속성·관계 좌표로 고정한 뒤, 실제 데이터를 탐색해 답을 만드는 것. 추측이 아니라 실행.
- **예시 1**: "risk exposure right now" → `Supplier.singleSourced=true` → `supplies` → `usedIn` → `revenueAtRisk` 계산 → 정렬. 5단계 모두 스키마 요소로 착지.
- **예시 2**: "approved alternatives for ChipX" → `AlternativeSupplier` + `canReplace.Supplier.name="ChipX Corp"` + `qualificationStatus="Approved"`. 엔터티·관계·enum·인스턴스 그라운딩이 한 문장에서 동시 발생.
- **없을 때와의 차이**: LLM 추측은 환각, RAG는 문장 인용 — 둘 다 관계 다단 추적·실시간 집계·완결성 보장이 불가.
- **품질 레버**: enum(어휘 폐쇄) · 식별자(인스턴스 유일성) · 관계 명명과 카디널리티(경로·방향) · 타입(연산 가능성).
- **지표 연결**: Trace accuracy > 95%가 그라운딩 품질의 직접 측정치이며, 실패하면 Impact estimate accuracy(±10%)·Revenue protection rate(>80%)까지 연쇄로 무너진다.
