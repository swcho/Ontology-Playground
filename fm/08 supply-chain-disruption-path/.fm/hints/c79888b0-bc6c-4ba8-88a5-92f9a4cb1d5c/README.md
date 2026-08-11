# 온톨로지가 있으면 AI 에이전트가 수행할 수 있는 5가지 작업

## 질문 / 정답

**Q.** 온톨로지가 있으면 AI 에이전트가 수행할 수 있는 5가지 작업은?

**A.**
1. 영향받은 모든 부품을 수 분 내 식별
2. 모든 제품 라인·생산 일정으로 추적
3. 대체 공급업체와 안전 재고 수량 추천
4. 각 완화 조치의 비용·편익 계산
5. 자동 알림과 조달 워크플로 트리거

---

## 왜 이 5가지인가 — 대비 구조를 먼저 기억하라

이 목록은 원문 **Scenario Overview**의 대비 문장에서 나온다.

> **온톨로지가 없으면** 이 분석은 며칠이 걸리고 수동 스프레드시트에 의존한다.
> **온톨로지가 있으면** AI 에이전트가 위 5가지를 할 수 있다.

즉 5가지는 "에이전트의 기능 목록"이 아니라 **대만 반도체 공급업체 48시간 정전** 같은 하나의 시나리오를 처리하는 **순차적 파이프라인**이다. 원문의 시나리오 흐름과 1:1로 맞춰서 외우면 순서가 헷갈리지 않는다.

```
Disruption(대만 정전) → Affects(ChipX 부품) → Impacts(3개 제품 라인)
→ Cascades(2주 후 생산 중단) → Result($12M 매출 위험) → Mitigation(대체 공급업체 + 안전 재고)
```

암기용 5단계 라벨: **식별 → 추적 → 추천 → 계산 → 실행** (Identify → Trace → Recommend → Calculate → Trigger).

원문의 Risk Propagation Model 절에는 같은 흐름이 6단계 동사형(**Detect → Trace → Quantify → Recommend → Act → Learn**)으로도 나오고, Mitigation Execution 절에는 시간축이 붙은 **Phase 1~5**로 나온다. 세 표현이 사실상 같은 것이며, 5가지 작업 문제는 Scenario Overview 판본을 묻는 것이다.

| 5가지 작업 | Risk Propagation 6단계 | Mitigation Phase (경과 시간) |
|---|---|---|
| ① 부품 식별 | Detect + Trace | Phase 1 Detection (0분) → Phase 2 앞부분 (5분) |
| ② 제품 라인·생산 일정 추적 | Trace | Phase 2 Trace impact (5분) |
| ③ 대체 공급업체·안전 재고 추천 | Recommend | Phase 4 Recommend actions (20분) |
| ④ 비용·편익 계산 | Quantify + Recommend | Phase 3 Quantify (15분) + Phase 4 스코어링 |
| ⑤ 자동 알림·조달 워크플로 | Act | Phase 5 Execute (25분) |

(Learn 단계 — 실제 효과 추적 — 는 5가지 목록 밖에 있다. 원문의 Continuous improvement 절과 연결된다.)

---

## 각 작업이 의존하는 엔터티·속성·관계

핵심은 **각 작업이 온톨로지의 특정 구조 없이는 불가능하다**는 점이다. 7 엔터티 / 40 속성 / 7 관계가 각각 어느 작업을 떠받치는지 아래에서 확인하라.

### ① 영향받은 모든 부품을 수 분 내 식별

- **필요 엔터티**: `DisruptionEvent`, `Supplier`, `Component`
- **필요 속성**: `DisruptionEvent.region`, `DisruptionEvent.type`(enum: Natural Disaster 등), `DisruptionEvent.severity`, `Supplier.country`, `Supplier.tier`, `Supplier.singleSourced`, `Component.criticalityLevel`
- **필요 관계**: **③ DisruptionEvent affects Supplier** (M:N) → **① Supplier supplies Component** (1:N)

Phase 1에서 에이전트는 `Supplier.country="Taiwan"` + `DisruptionEvent.region="Taiwan"` + `DisruptionEvent.type="Natural Disaster"` 를 매칭해 **3개 핵심 공급업체**를 찾고, Phase 2 앞부분에서 `supplies` 관계를 따라 **47개 부품**을 얻는다.

왜 온톨로지가 필요한가: `country`/`region`이 자유 텍스트가 아닌 표준화된 속성이고, `affects`·`supplies`가 **명시적 관계**로 저장돼 있어야 조인 없이 그래프 순회 한 번으로 끝난다. `singleSourced=true` 불리언은 "위험 증폭기"인 단일 소싱 공급업체를 즉시 플래그하는 데 쓰인다. 스프레드시트에서는 이 단계 자체가 며칠 걸린다.

### ② 모든 제품 라인·생산 일정으로 추적

- **필요 엔터티**: `Component`, `ProductLine`
- **필요 속성**: `Component.daysOfSupplyOnHand`(생산 일정이 언제 끊기는지 결정), `ProductLine.productionStatus`(enum: Active/At Risk/Halted/Discontinued), `ProductLine.annualRevenue`, `ProductLine.marketSegment`
- **필요 관계**: **② Component used in ProductLine** (M:N)

Phase 2 후반: "47개 부품을 쓰는 제품 라인은?" → `usedIn`을 따라 **12개 제품 라인 노출** 확인.

왜 M:N이 결정적인가: 부품은 여러 제품에 재사용되고 제품은 여러 부품을 공유한다. 이 다대다 관계가 모델링돼 있어야 **부품 하나의 실패가 여러 제품 라인을 동시에 세운다**는 사실이 자동으로 드러난다. "생산 일정"의 시간축은 `daysOfSupplyOnHand`(예: GPU Module = 3일)에서 나온다 — 재고가 소진되는 시점이 곧 생산 중단 시점이다. 추적 결과는 `productionStatus`를 Active → At Risk로 갱신하는 근거가 된다.

### ③ 대체 공급업체와 안전 재고 수량 추천

- **필요 엔터티**: `RiskAssessment`, `MitigationAction`, `AlternativeSupplier`
- **필요 속성**: `AlternativeSupplier.qualificationStatus`(enum: Pre-qualified/Approved/Pending Audit/Not Qualified), `capacityAvailable`(units/month), `pricePremiumPercent`, `AlternativeSupplier.country`, `Supplier.reliabilityScore`, `MitigationAction.type`(Activate Alternative Supplier / Increase Safety Stock / …), `MitigationAction.leadTimeSavedDays`
- **필요 관계**: **④ DisruptionEvent triggers RiskAssessment** (1:N) → **⑤ RiskAssessment recommends MitigationAction** (1:N) → **⑥ MitigationAction activates AlternativeSupplier** (M:N) → **⑦ AlternativeSupplier canReplace Supplier** (M:1)

Phase 4의 추천 엔진 로직:

```
1) AlternativeSupplier 필터: qualificationStatus="Approved"
                             AND capacityAvailable >= demand
                             AND country NOT IN earthquake_region
2) 스코어링: leadTimeSavedDays, pricePremiumPercent, reliabilityScore
3) 상위 3개 액션 제시
```

왜 온톨로지가 필요한가: **⑦ canReplace (M:1)** 관계가 "이 공급업체를 대신할 수 있는 사전 검증된 백업이 누구인가"를 사전에 저장해 둔다. 이 관계가 없으면 재난 순간에 자격 심사를 처음부터 해야 한다. `country NOT IN` 필터는 대체 업체가 **같은 재난 지역에 있지 않은지** 확인하는 것으로, `AlternativeSupplier.country`와 `DisruptionEvent.region`이 같은 어휘를 쓸 때만 가능하다. "안전 재고 수량" 쪽은 `MitigationAction.type="Increase Safety Stock"` + `Component.daysOfSupplyOnHand` 조합으로 산출된다(예: $500K로 2주 커버).

### ④ 각 완화 조치의 비용·편익 계산

- **필요 엔터티**: `RiskAssessment`, `MitigationAction`, `ProductLine`, `AlternativeSupplier`
- **필요 속성**: `RiskAssessment.revenueAtRisk`(USD, decimal), `timeToImpactDays`, `confidenceLevel`, `assessedDate`(datetime), `recommendedAction`, `MitigationAction.estimatedCost`(USD), `leadTimeSavedDays`, `ProductLine.annualRevenue`, `Component.daysOfSupplyOnHand`, `AlternativeSupplier.pricePremiumPercent`
- **필요 관계**: **④ triggers** + **⑤ recommends** (둘 다 1:N — 하나의 사건이 제품 라인별 평가를 낳고, 각 평가가 여러 액션을 낳으므로 액션끼리 **비교**가 가능해진다)

Phase 3 계산식:

```
revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand
urgency         = 100 - (daysOfSupplyOnHand * 10)
total_revenue_at_risk = SUM(revenue_at_risk)
critical_product_lines = WHERE urgency > 70
```

편익 판단의 본질은 대비다: 캐스케이드 예시에서 `revenueAtRisk=$80M` 대 `estimatedCost=$2M`(리드타임 2일 절감) → 즉시 승인 근거. 다른 선택지 "안전 재고 증대"는 $500K. 이 비교가 성립하려면 **손실과 비용이 같은 단위(USD decimal)로, 같은 그래프 위에** 있어야 한다.

왜 데이터 타입이 중요한가: 원문의 속성 타입 표가 이 작업을 정당화한다 — `decimal`은 비용·편익 계산, `integer`(daysOfSupply, capacity)는 임계값 알림, `date`/`datetime`은 타임라인 비교와 감사 추적, `enum`은 의사결정 트리, `boolean`(singleSourced)은 위험 플래깅에 쓰인다.

### ⑤ 자동 알림과 조달 워크플로 트리거

- **필요 엔터티**: `RiskAssessment`, `MitigationAction`, `AlternativeSupplier` (+ 외부 시스템의 PurchaseOrder, ProductionSchedule)
- **필요 속성**: `RiskAssessment.revenueAtRisk`, `timeToImpactDays` (규칙의 조건절), `MitigationAction.status`(enum: Proposed/Approved/In Progress/Completed/Cancelled — 모니터링 대상), `estimatedCost`, `DisruptionEvent.severity`·`estimatedDurationDays`
- **필요 관계**: **⑤ recommends** → **⑥ activates** → **⑦ canReplace** (액션에서 실제 발주 대상 업체까지 자동으로 도달)

Phase 5 규칙:

```
IF RiskAssessment.revenueAtRisk > $50M AND RiskAssessment.timeToImpactDays < 5:
THEN
  1. 추천된 AlternativeSupplier에게 PurchaseOrder 생성
  2. ProductionSchedule을 새 타임라인으로 갱신
  3. 이메일 발송 — 조달(구매 실행) / 운영(일정 조정) / 재무($2M 추가 비용 예측) / CEO·이사회(노출 보고)
  4. 에스컬레이션 정책이 붙은 Activator 알림 생성
  5. MitigationAction.status 모니터링 시작
```

왜 온톨로지가 필요한가: 임계값 자동화는 `revenueAtRisk`·`timeToImpactDays`가 **문서 안의 문장이 아니라 조회 가능한 타입 있는 속성**일 때만 작동한다. enum으로 표준화된 `severity`/`status`가 에스컬레이션 레벨과 워크플로 상태 기계를 결정한다. 그리고 `status`를 계속 추적하기 때문에 ⑥번째 단계인 **Learn**(추정 대 실제: 실제 $2.1M vs 추정 $2M)이 가능해진다.

---

## 실제 타임라인으로 확인 (Day 1)

원문 워크플로가 5가지 작업이 실제로 몇 분 단위임을 보여준다.

| 시각 | 일어난 일 | 해당 작업 |
|---|---|---|
| 10:30 | 대만 지진 M6.8 발생 | — |
| 10:45 | `DisruptionEvent` 생성 (type=Natural Disaster, severity=Critical, region=Taiwan, estimatedDurationDays=7) | ① 준비 |
| 10:46 | 3개 공급업체 / 47개 부품 / 12개 제품 라인 / $127M / 3일 | ①②④ |
| 10:47 | `RiskAssessment` 생성, ROI 순으로 액션 랭킹 | ③④ |
| 10:48 | `MitigationAction` 자동 생성 — ChipX Europe에 PO, 안전 재고 발주, 조달·운영·재무 알림 | ③⑤ |
| 10:50 | Activator 발동 — 대시보드, 리더십 에스컬레이션, 조달팀 확인 | ⑤ |
| 11:30 | `MitigationAction.status="In Progress"`, 생산 영향 7일 → 3일 | ⑤ + Learn |

**결과**: Day 3에 $127M 노출 중 약 $100M 매출 방어, 실제 비용 $2.1M(추정 $2M). "며칠 → 1시간 이내"라는 원문 목표(Detection speed < 1 hour, Time to mitigation < 2 hours)가 이렇게 달성된다.

---

## 자주 틀리는 지점

- **"수 분 내"는 ①에 붙은 수식어다.** 목록 첫 항목의 핵심은 속도(minutes)이며, 온톨로지 없는 대안이 "며칠 + 수동 스프레드시트"라는 대비가 핵심이다. 5가지를 나열할 때 "수 분 내"를 빠뜨리면 문제 의도를 절반 놓친다.
- **③과 ④를 합치지 말 것.** ③은 *무엇을 할 수 있는가*(대체 업체 후보, 안전 재고 수량)의 생성이고, ④는 *그 중 무엇이 이득인가*의 평가다. 온톨로지 관점에서도 ③은 `canReplace`/`qualificationStatus`/`capacityAvailable`에, ④는 `revenueAtRisk`/`estimatedCost`/`leadTimeSavedDays`에 각각 의존한다.
- **②는 "제품 라인"만이 아니라 "제품 라인 **및 생산 일정**"이다.** 일정 축은 `daysOfSupplyOnHand`에서 나온다.
- **⑤는 알림만이 아니라 조달 워크플로까지다.** 이메일 발송(알림) + PurchaseOrder 생성·생산 일정 갱신(워크플로) 둘 다 포함한다.
- **Learn(효과 추적)은 5가지에 포함되지 않는다.** Risk Propagation 절의 6단계 목록과 혼동하기 쉬운 지점이다.

## 한 줄 요약

7개 엔터티와 7개 관계(`supplies` → `usedIn` → `affects` → `triggers` → `recommends` → `activates` → `canReplace`)가 그래프로 연결돼 있고 40개 속성이 타입을 가지고 있기 때문에, AI 에이전트는 **식별 → 추적 → 추천 → 계산 → 실행**을 사람 개입 없이 수 분 안에 완주할 수 있다.
