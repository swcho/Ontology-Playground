# Supplier 엔터티의 대표적 활용(use case)

## 질문과 정답

**Q.** Supplier 엔터티의 대표적 활용(use case)은?

**A.** 리스크를 증폭시키는 **단일 소싱(single-source) 핵심 공급업체를 식별**하는 것이다. `singleSourced=true`인 공급업체는 대체 경로가 없어 교란 시 영향이 그대로 전이된다.

원문 표현은 다음과 같다.

> **Supplier**
> - Represents external companies providing raw materials or components
> - Key properties: `supplierId` (unique), `name`, `country`, `tier` (Tier 1/2/3), `reliabilityScore` (0-100), `singleSourced` (boolean)
> - **Use case: Identify critical single-source suppliers that are risk amplifiers**

---

## 왜 "단일 소싱 식별"이 대표 활용인가

Supply Chain Disruption 온톨로지는 7개 엔터티(Supplier, Component, ProductLine, DisruptionEvent, RiskAssessment, MitigationAction, AlternativeSupplier)로 구성되며, Supplier는 그중 **Tier 1: The network**(공급망 그 자체)에 속한다. 즉 Supplier는 교란(disruption)이 **처음 꽂히는 지점**이다.

리스크 전파는 다음 경로를 따른다.

```
DisruptionEvent --affects--> Supplier --supplies--> Component --usedIn--> ProductLine
                                                         └--triggers--> RiskAssessment
```

여기서 Supplier가 여러 대안 중 하나라면 교란의 영향은 다른 공급업체로 흡수·분산된다. 그러나 그 Component를 공급하는 곳이 **오직 한 곳뿐(single-sourced)**이라면 영향은 감쇠 없이 Component → ProductLine → 매출로 100% 전이된다. 이 때문에 단일 소싱 공급업체를 "**risk amplifier**(리스크 증폭기)"라고 부른다. Supplier 엔터티를 모델링하는 첫 번째 실익은 바로 이 증폭기들을 목록으로 뽑아내는 것이다.

자산의 cascade 예시가 정확히 그 상황이다.

```
Taiwan Power Outage (2024-05-01, Critical severity)
  └─ Supplier "ChipX Corp" (singleSourced=true)
     └─ Component "GPU Module" (daysOfSupplyOnHand=3)
        ├─ ProductLine "Gaming Laptop 2024" ($50M)
        ├─ ProductLine "Workstation Pro"    ($30M)
        └─ RiskAssessment: revenueAtRisk=$80M, timeToImpactDays=3
```

`singleSourced=true` 하나 때문에 단일 공급업체 장애가 곧바로 8천만 달러 노출로 환산된다.

---

## 세 가지 속성이 리스크 판단에 쓰이는 방식

Supplier의 핵심 속성 세 개는 각각 다른 판단 질문에 답한다.

| 속성 | 타입 | 값 | 답하는 질문 | 리스크 판단에서의 역할 |
|---|---|---|---|---|
| `singleSourced` | `boolean` | true/false | "대체 경로가 있는가?" | **리스크 플래깅(risk flagging)** — 전파를 감쇠시킬 우회로가 있는지 여부. true면 영향이 그대로 하류로 전이 |
| `tier` | `enum` | Tier 1 / 2 / 3 | "우리와 얼마나 가까운가 / 얼마나 보이는가?" | **분류·의사결정 트리(classification, decision trees)** — 에스컬레이션 대상과 가시성 수준 결정 |
| `reliabilityScore` | `decimal` | 0-100 | "평상시 얼마나 자주 문제를 일으키는가?" | **비용-편익 계산(cost-benefit calculations)** — 사전 발생확률 가중치이자 대안 스코어링 입력값 |

### 1. `singleSourced` (boolean) — 전파 경로의 유무를 켜고 끄는 스위치

자산의 property 타입 표는 `boolean`의 용도를 "Single-sourced flag → **Risk flagging**"이라고 명시한다. boolean은 임계값 비교도, 금액 계산도 하지 않는다. 오직 **"이 노드는 감쇠 없는 전파 노드다"**를 표시한다. 실무적 의미는 두 가지다.

- **필터의 시작점**: 리스크 스캔은 `WHERE singleSourced = true`로 후보 집합을 좁힌 뒤 그래프를 따라 내려간다.
- **완화(mitigation) 대상 지정**: 단일 소싱 상태 자체가 해소해야 할 문제이므로 사전 대안 확보(pre-qualifying AlternativeSupplier)라는 액션으로 직결된다.

### 2. `tier` (enum) — 에스컬레이션 레벨과 가시성

`tier`는 Tier 1/2/3이라는 enum이며, 자산은 enum의 용도를 "Supplier tier, disruption type, severity → **Classification, decision trees**"로 분류한다.

- **Tier 1**: 우리에게 직접 납품. 계약·품질 데이터가 있어 감지가 빠르고, 문제 발생 시 즉시 조달 조직이 움직인다.
- **Tier 2/3**: 우리 공급업체의 공급업체. 직접 계약이 없어 **가시성이 낮고 감지가 늦다**. 따라서 같은 severity라도 대응 리드타임 여유가 적고, Tier 2/3의 단일 소싱은 "보이지 않는 증폭기"로서 더 위험하다.

결과적으로 `tier`는 "누구에게 알릴지, 어느 속도로 에스컬레이션할지"를 결정하는 라우팅 키다. `singleSourced=true` AND `tier`가 깊을수록 우선순위가 올라간다.

### 3. `reliabilityScore` (0-100, decimal) — 확률 가중치이자 대안 비교 기준

`decimal`은 "Revenue, price premium, **reliability score** → **Cost-benefit calculations**"에 쓰인다. 두 국면에서 등장한다.

- **사전(prior) 리스크 산정**: 노출 금액(revenueAtRisk)이 "얼마나 아픈가"라면 `reliabilityScore`는 "얼마나 자주 아플까"에 대한 근사치다. 낮은 점수 + `singleSourced=true` 조합이 최악의 사분면이다.
- **대안 스코어링**: Phase 4(Recommend actions)의 대안 평가 기준 세 가지가 lead time saved(`leadTimeSavedDays`), cost impact(`pricePremiumPercent`), 그리고 **reliability(`reliabilityScore`)**다. 즉 신뢰도 점수는 원 공급업체 평가뿐 아니라 "누구로 갈아탈 것인가"의 순위 결정에도 재사용된다.

### 세 속성의 결합: 우선순위 매트릭스

```
singleSourced=true  AND reliabilityScore 낮음  AND tier 깊음(2/3)
  → 최우선. 발생확률 높고, 감지 늦고, 감쇠 경로 없음 → 즉시 대안 사전 승인
singleSourced=true  AND reliabilityScore 높음
  → 확률은 낮지만 사고 시 손실 100% 전이 → 사전 qualification 대상(테일 리스크)
singleSourced=false
  → 우회로 존재. 모니터링 수준으로 관리
```

---

## Fabric IQ 질의 예시와의 연결

이 세 속성이 어떻게 하나의 자연어 답변으로 합쳐지는지가 자산의 Fabric IQ 예시에 나온다.

```
User: "What's our supply chain risk exposure right now?"
  ↓
Data Agent grounds query against your ontology:
  1. Find all Supplier records with singleSourced=true
  2. For each, find Components they supply
  3. Trace to ProductLines using those components
  4. Calculate revenueAtRisk for each ProductLine
  5. Return ranked list by revenueAtRisk

Agent Response:
  "You have 3 critical single-source suppliers.
   If any are disrupted, you lose ~$180M in
   4-9 days. We recommend pre-qualifying
   8 alternative suppliers (list attached)."
```

응답 문장을 속성별로 분해하면 use case가 그대로 보인다.

| 응답 조각 | 근거 |
|---|---|
| "3 **single-source** suppliers" | 1단계 `singleSourced=true` 필터. 이 boolean이 없으면 후보 집합 자체를 만들 수 없다 |
| "**critical**" | `tier`(Tier 1/2/3)와 하류 Component의 `criticalityLevel`로 판정한 중요도 분류 |
| "you lose **~$180M**" | 3~4단계, ProductLine의 `annualRevenue` 기반 `revenueAtRisk` 집계 |
| "in **4-9 days**" | Component의 `daysOfSupplyOnHand` → `timeToImpactDays` |
| "**pre-qualifying 8 alternative suppliers**" | 단일 소싱 해소 액션. 후보 순위는 `reliabilityScore` + `pricePremiumPercent` + `leadTimeSavedDays`로 스코어링 |

핵심은 이것이 **교란이 실제로 일어나기 전에도** 답할 수 있는 질의라는 점이다. DisruptionEvent가 하나도 없어도 `singleSourced` 플래그만으로 "지금 우리 취약점은 어디인가"를 상시 계산할 수 있다. 자산 첫 문단의 "react after the damage is done"에서 "**anticipate and act before customers are affected**"로 넘어가는 전환이 여기서 일어난다. Supplier 엔터티의 use case가 "공급업체 명단 관리"가 아니라 "**리스크 증폭기 식별**"인 이유다.

`revenueAtRisk` 계산식과 스케일 감각을 위해:

```
revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand
urgency         = 100 - (daysOfSupplyOnHand * 10)
```

`daysOfSupplyOnHand`가 작을수록 urgency가 커진다. 단일 소싱 공급업체가 안전재고가 얕은 Component를 공급하면 `singleSourced=true` × 얕은 재고 = 즉시 폭발하는 조합이 된다(ChipX Corp: `daysOfSupplyOnHand=3` → `timeToImpactDays=3`).

---

## 자주 헷갈리는 지점

- **Supplier vs. AlternativeSupplier**: Supplier는 현재 실제로 납품 중인 주 공급업체다. AlternativeSupplier는 `qualificationStatus`(Pre-qualified/Approved/Pending Audit/Not Qualified), `capacityAvailable`, `pricePremiumPercent`를 갖는 별개 엔터티이며 `canReplace`(M:1)로 Supplier를 가리킨다. "대안이 있는지"는 AlternativeSupplier 관계로 표현되고, "대안이 없다"는 사실이 Supplier의 `singleSourced=true`로 요약된다.
- **`tier`는 중요도 등급이 아니다**: Tier 1/2/3은 공급망 상의 **거리(depth)** 분류이며 "1등급이라 더 중요"라는 뜻이 아니다. 중요도는 Component의 `criticalityLevel`과 ProductLine의 `annualRevenue`에서 나온다.
- **`reliabilityScore`는 영향 크기가 아니다**: 손실 규모는 하류 ProductLine에서 계산된다. `reliabilityScore`는 발생 가능성 쪽 축이다. 리스크 = 확률(reliabilityScore) × 영향(revenueAtRisk)에서 각각 다른 항을 담당한다.
- **다른 엔터티의 use case와 구분**: Component는 "안전재고 기반으로 어떤 부품이 버틸 수 있는지 추적", ProductLine은 "매출 노출과 생산 일정 영향 계산", DisruptionEvent는 "분류·심각도로 에스컬레이션 레벨 결정"이다. Supplier만이 "단일 소싱 핵심 공급업체 식별"이다.

---

## 한 줄 요약

Supplier 엔터티는 `singleSourced`(감쇠 없는 전파 경로 플래그) · `tier`(에스컬레이션·가시성 분류) · `reliabilityScore`(발생확률 가중치 및 대안 스코어링 입력)를 결합해, 교란이 발생하기 전에 **"대체 불가 = 리스크 증폭기"인 핵심 공급업체를 식별**하는 데 쓰인다. Fabric IQ 에이전트가 "3개의 핵심 단일 소싱 공급업체, 4~9일 내 약 1억 8천만 달러 손실 노출"이라고 답할 수 있는 출발점이 바로 이 use case다.
