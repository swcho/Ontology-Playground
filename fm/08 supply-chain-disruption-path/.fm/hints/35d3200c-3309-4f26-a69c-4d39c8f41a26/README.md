# `enum` 타입 속성이 자동화에서 특히 중요한 이유

## 질문

`enum` 타입 속성이 자동화에서 특히 중요한 이유는?

## 정답

공급업체 tier, 교란 type, severity처럼 **값 집합이 고정되어 있어 분류와 의사결정 트리(decision tree)를 신뢰성 있게 구성**할 수 있기 때문이다.

---

## 1. 속성 타입 표에서 `enum`의 자리

원문의 "Property types and validations" 표는 각 타입이 **에이전트에서 어떻게 쓰이는지**를 기준으로 정리되어 있다.

| Type | Example | Use in agents (에이전트 활용) |
|------|---------|------------------------------|
| `string` | 공급업체 이름 | 검색, 필터링, 리포팅 |
| `integer` | 재고일수, capacity, 수량 | 임계값 기반 알림 |
| `decimal` | 매출, 가격 프리미엄, 신뢰도 점수 | 비용-편익 계산 |
| `date` | 교란 시작일 | 타임라인 비교 |
| `datetime` | 리스크 평가 시각 | 감사 추적(audit trail), 추세 분석 |
| **`enum`** | **공급업체 tier, 교란 type, severity** | **분류(classification), 의사결정 트리(decision trees)** |
| `boolean` | 단일 소싱 플래그 | 리스크 플래깅 |

핵심은 `string`의 용도가 "검색·필터링·리포팅"에서 끝나는 반면, `enum`만 유일하게 **"의사결정 트리"** 를 담당한다는 점이다. 자유 텍스트는 사람이 읽을 수는 있지만 기계가 **분기(branch)** 를 만들 근거가 되지 못한다. 값의 도메인이 닫혀 있어야만 "이 값이면 A, 저 값이면 B" 라는 규칙을 **빠짐없이(exhaustive)**, 그리고 **겹치지 않게(mutually exclusive)** 쓸 수 있다.

## 2. 이 온톨로지의 모든 `enum` 속성

7개 엔티티 중 6개가 enum을 갖는다. RiskAssessment까지 포함하면 자동화 파이프라인의 모든 단계(감지 → 분류 → 평가 → 실행)에 최소 하나씩 enum이 배치되어 있다.

| # | 엔티티 | enum 속성 | 허용 값 집합 (도메인) | 값 개수 | 자동화 역할 |
|---|--------|-----------|----------------------|:---:|------------|
| 1 | Supplier | `tier` | Tier 1 / Tier 2 / Tier 3 | 3 | 공급망 깊이별 그룹핑, 리스크 가중치 |
| 2 | Component | `category` | Electronic / Mechanical / Chemical / Packaging / Raw Material | 5 | 부품군별 대체 전략 라우팅 |
| 3 | Component | `criticalityLevel` | Critical / High / Medium / Low | 4 | 대응 우선순위 결정 |
| 4 | ProductLine | `productionStatus` | Active / At Risk / Halted / Discontinued | 4 | 생산 상태 머신, 영향 집계 대상 판별 |
| 5 | DisruptionEvent | `type` | Natural Disaster / Geopolitical / Financial / Logistics / Quality Recall / Pandemic / Cyber Attack | 7 | 교란 유형별 플레이북 선택 |
| 6 | DisruptionEvent | `severity` | Critical / High / Medium / Low | 4 | 에스컬레이션 등급, 대응 타임라인 |
| 7 | RiskAssessment | `confidenceLevel` | High / Medium / Low | 3 | 자동 실행 vs. 사람 승인 게이트 |
| 8 | MitigationAction | `type` | Activate Alternative Supplier / Increase Safety Stock / Redesign Component / Reduce Production / Expedite Shipment / Customer Communication | 6 | 실행할 워크플로 종류 결정 |
| 9 | MitigationAction | `status` | Proposed / Approved / In Progress / Completed / Cancelled | 5 | **상태 머신**(진행 추적, SLA 감시) |
| 10 | AlternativeSupplier | `qualificationStatus` | Pre-qualified / Approved / Pending Audit / Not Qualified | 4 | 활성화 가능 후보 게이트 필터 |

> 참고: 원문 타입 표에서는 `Component category`를 `string` 예시로도 들고 있다. 그러나 값 집합이 5개로 명시적으로 고정되어 있으므로 실무에서는 enum으로 모델링하는 것이 맞다. "실제 값이 유한 목록인가?"가 string/enum을 가르는 판단 기준이며, 이름·설명처럼 무한한 텍스트만 `string`으로 남긴다.

### enum 값의 의미론적 구조

enum은 단순 목록이 아니라 세 종류의 구조를 갖는다. 자동화 방식이 구조에 따라 달라진다.

- **순서형(ordinal)** — `severity`, `criticalityLevel`, `confidenceLevel`, `tier`: Critical > High > Medium > Low 라는 순서가 있어 **임계값 비교**(`severity >= High`)와 정렬이 가능하다.
- **명목형(nominal)** — `type`(교란/조치), `category`: 순서가 없고 **분기 대상**이다. `switch (type)` 형태의 플레이북 매핑에 쓰인다.
- **상태형(state)** — `status`, `productionStatus`, `qualificationStatus`: 값 사이에 **허용된 전이(transition)** 가 정의되며 상태 머신으로 다뤄진다.

---

## 3. enum이 없으면 무엇이 망가지는가

### 3-1. 질의 매칭(query matching)이 조용히 실패한다

Phase 1 감지 단계의 질의는 **문자열 동등 비교** 위에 서 있다.

```
Data Agent Query:
  "Which suppliers are affected by the Taiwan earthquake?"
  ↓
  Matches: Supplier.country="Taiwan"
           + DisruptionEvent.region="Taiwan"
           + DisruptionEvent.type="Natural Disaster"
  ↓
  Result: 3 critical suppliers identified
```

`type`이 자유 텍스트였다면 현장 담당자들이 입력한 값은 이렇게 흩어진다.

| 실제 입력된 값 | `type="Natural Disaster"` 매칭 | 결과 |
|---|:---:|---|
| `Natural Disaster` | ✅ | 정상 감지 |
| `natural disaster` | ❌ | 누락 (대소문자) |
| `Natural disaster ` | ❌ | 누락 (trailing space) |
| `Earthquake` | ❌ | 누락 (하위 개념을 직접 기입) |
| `자연재해` | ❌ | 누락 (언어 혼용) |
| `NatDisaster` / `ND` | ❌ | 누락 (약어) |
| `Taiwan quake 6.8 - power out` | ❌ | 누락 (서술형 기입) |

여기서 진짜 위험한 것은 에러가 나지 않는다는 점이다. 질의는 성공적으로 실행되고 `Result: 0 suppliers`를 반환한다. **"교란이 없다"와 "값 표기가 달라서 못 찾았다"가 구분되지 않는다.** 실제로는 47개 부품, 12개 제품 라인, $127M이 위험에 노출된 상태인데 대시보드는 초록색으로 남는다. 3일 뒤 생산이 멈출 때까지 아무도 모른다.

Phase 4의 후보 필터는 이 문제가 가장 치명적으로 나타나는 지점이다.

```
Find AlternativeSupplier records where:
  - qualificationStatus="Approved"
  - capacityAvailable >= demand
  - country NOT IN earthquake_region
```

`qualificationStatus`가 자유 텍스트라면 이 필터는 **양방향으로** 깨진다.

- **거짓 부정(false negative)** — `"approved"`, `"Approved (2024 audit)"`, `"승인 완료"`, `"Approved - conditional"` 로 기록된 진짜 승인 업체들이 필터에서 탈락한다. ChipX Europe(capacity 50K/월, +12%)이 후보 목록에서 사라지고, 에이전트는 "승인된 대체 공급업체가 없습니다"라고 답한다. $2M로 막을 수 있었던 $80M 손실을 그대로 맞는다.
- **거짓 긍정(false positive)** — 더 나쁘다. `"Not Approved"`, `"Pending approval"`, `"Approved pending audit"` 같은 값에 부분 문자열 매칭(`LIKE '%Approved%'`)을 쓰면 **자격 미달 업체에 자동으로 발주(PO)가 나간다.** Phase 5는 사람의 확인 없이 `Create PurchaseOrder`를 실행하므로, 감사를 통과하지 못한 업체의 부품이 라인에 들어오는 품질 사고로 이어진다.

enum이면 값이 `Pre-qualified / Approved / Pending Audit / Not Qualified` 4개뿐이므로 `= "Approved"` 한 줄이 정확히 의도한 집합만 골라낸다. `Pending Audit`와 `Approved`가 문자열로 헷갈릴 여지가 애초에 없다.

### 3-2. IF-THEN 규칙의 조건이 평가 불가능해진다

Phase 5의 자동 실행 규칙과, 그 위에 얹히는 등급별 분기를 보자.

```
IF RiskAssessment.revenueAtRisk > $50M AND
   RiskAssessment.timeToImpactDays < 5:
   THEN 1. PO 생성  2. 생산 일정 갱신  3. 조달/운영/재무/CEO 통보
        4. Activator 알림 생성  5. MitigationAction.status 모니터링 시작
```

이 규칙 자체는 숫자 비교지만, 실무에서는 반드시 `severity`·`criticalityLevel`·`confidenceLevel`로 감싸인다.

```
IF severity = "Critical" AND criticalityLevel IN ("Critical","High")
   → 즉시 자동 실행 + 임원 에스컬레이션
IF severity = "High"  AND confidenceLevel = "High"
   → 자동 실행, 통보는 조달팀까지
IF confidenceLevel = "Low"
   → 자동 실행 금지, 사람 승인 대기
```

자유 텍스트에서 이 규칙들이 무너지는 방식은 세 가지다.

1. **순서 비교가 불가능** — `severity >= "High"` 같은 임계값 비교를 하려면 값에 서열이 있어야 한다. `"Very bad"`, `"심각"`, `"P1"`, `"매우 높음(추정)"`이 섞인 컬럼에서는 `>=` 가 정의되지 않는다. 문자열 사전순으로 비교하면 `"Critical" < "Low" < "Medium"`이 되어 **가장 심각한 값이 가장 낮은 등급으로 취급된다.**
2. **분기 누락(silent fallthrough)** — 값 집합이 열려 있으면 `ELSE` 절로 떨어지는 미지의 값이 계속 생긴다. Critical 교란이 "해당 없음" 경로로 흘러가 알림이 발송되지 않는다. enum이면 4개 값 전부에 대응하는 분기가 있는지 **정적으로 검증**할 수 있다(exhaustiveness check).
3. **규칙 테스트가 불가능** — enum이면 `4개 severity × 4개 criticality × 3개 confidence = 48개` 조합으로 전수 테스트를 짤 수 있다. 자유 텍스트는 입력 공간이 무한해서 커버리지를 정의조차 못 한다.

`MitigationAction.type`도 같다. 값이 6개로 닫혀 있어 `type → 실행 워크플로` 매핑 테이블이 완결된다.

| `type` | 트리거되는 자동 워크플로 |
|---|---|
| Activate Alternative Supplier | PO 생성 → 조달팀 알림 |
| Increase Safety Stock | 재고 발주 → 창고 시스템 갱신 |
| Expedite Shipment | 물류사 API 호출 |
| Reduce Production | 생산 일정(ProductionSchedule) 조정 |
| Redesign Component | 엔지니어링 티켓 발행 (리드타임 미정 → 자동 실행 제외) |
| Customer Communication | 고객 통보 템플릿 발송 |

`type = "알아서 빨리 보내달라고 요청"` 같은 값이 들어오면 매핑되는 워크플로가 없어 조치가 생성만 되고 아무 일도 일어나지 않는다.

### 3-3. 상태 머신(state machine)이 성립하지 않는다

`MitigationAction.status`는 이 온톨로지에서 enum의 가치를 가장 선명하게 보여준다. Phase 5의 마지막 단계가 `Start monitoring MitigationAction.status`이고, Day 2-4 루프가 4시간마다 이 값을 읽는다. 즉 **status는 자동화 루프의 종료 조건이자 진행률 지표**다.

허용 전이:

```
Proposed ──approve──▶ Approved ──execute──▶ In Progress ──deliver──▶ Completed
    │                    │                       │
    └──────────────── Cancelled ◀────────────────┘
                    (어느 단계에서든 취소 가능)

Completed / Cancelled = 종료 상태(terminal), 이후 전이 없음
```

원문 워크플로에 실제로 나타나는 전이:

| 시각 | status | 전이 계기 | 자동화 동작 |
|---|---|---|---|
| Day 1 10:48 | `Proposed` | RiskAssessment가 조치 추천 | 승인 요청 발송 |
| Day 1 10:48 | `Approved` | 규칙이 임계값 충족 판정 후 자동 승인 | PO 발행 (ChipX Europe) |
| Day 1 11:30 | `In Progress` | 조달팀 접수 확인, 48시간 배송 확약 | 4시간 주기 모니터링 시작, 지연 감시 |
| Day 3 | `Completed` | 입고 완료 | 모니터링 종료, 실적 기록(실제 $2.1M vs 추정 $2M) |

enum이 이 구조에 제공하는 것:

- **유효한 다음 상태의 집합이 정의된다** — `Completed`에서 `In Progress`로 되돌아가거나, `Proposed`에서 `Completed`로 건너뛰는 잘못된 전이를 시스템이 거부할 수 있다. 자유 텍스트에서는 어떤 값에서 어떤 값으로 가도 되는지 판단할 근거가 없다.
- **종료 조건이 명확하다** — 4시간 루프는 `status NOT IN ("Completed","Cancelled")` 인 조치만 조회한다. `"거의 다 됨"`, `"완료(일부)"`, `"Done!"`, `"입고 대기중 → 완료"` 같은 값이 섞이면 완료된 조치를 계속 폴링하거나, 반대로 미완료 조치를 완료로 오인해 감시를 끊는다. 후자는 대체 공급업체가 배송을 지연시켜도 `leadTimeSavedDays` 이탈 알림이 발송되지 않는 상황을 만든다.
- **집계와 KPI가 계산된다** — "Time to mitigation = 평가부터 조치 실행까지의 시간" 지표는 `Approved → In Progress` 전이 시각의 차이로 정의된다. 상태 값이 정규화되어 있지 않으면 이 전이 시점을 특정할 수 없고, "Revenue protection rate > 80%", "Cost efficiency ±5%" 같은 지표도 `Completed` 집합을 정확히 셀 수 없어 무의미해진다.
- **대시보드가 안정적이다** — 값이 5개로 고정되어 있으므로 상태별 카운트 차트의 축, 색상, 순서가 데이터에 따라 흔들리지 않는다. 자유 텍스트면 새 표기가 등장할 때마다 없던 범주가 생긴다.

`ProductLine.productionStatus`(Active → At Risk → Halted)와 `AlternativeSupplier.qualificationStatus`(Not Qualified → Pending Audit → Pre-qualified → Approved)도 같은 상태 머신 구조를 가지며, 각각 "영향 집계 대상 판별"과 "활성화 가능 후보 게이트" 역할을 한다.

---

## 4. 정리

원문 요약이 자동화 준비 조건으로 꼽은 것은 `enum classifications and timestamps` 두 가지다. timestamp가 **언제** 를 기계가 계산할 수 있게 만든다면, enum은 **무엇으로 분류되며 그래서 어떻게 대응할지** 를 기계가 판단할 수 있게 만든다.

`enum`이 자동화에서 특별한 이유를 한 줄로 요약하면:

> 값 집합이 닫혀 있다는 것은 곧 **분기의 개수가 유한하고 알려져 있다**는 뜻이고, 그래야 질의가 정확히 매칭되고, IF-THEN 규칙이 모든 경우를 빠짐없이 덮으며, 상태 전이의 유효성을 검증할 수 있다.

반대로 자유 텍스트의 근본 문제는 **실패가 조용하다**는 점이다. 오타 하나, 대소문자 하나 때문에 필터가 0건을 반환해도 시스템은 정상 동작으로 보고한다. 공급망 교란처럼 3일 안에 결정해야 하는 도메인에서 조용한 실패는 곧 놓친 $127M이다.
