# RiskAssessment 엔터티의 핵심 활용 목적

## 질문

RiskAssessment 엔터티의 핵심 활용 목적은?

## 정답

영향을 **돈과 시간이라는 비즈니스 용어로 정량화**해 대응 우선순위를 정하는 것이다. `revenueAtRisk`와 `timeToImpactDays`가 그 두 축이다.

---

## 1. 왜 "정량화"가 목적인가

원문의 정의를 그대로 보면 목적이 명시되어 있다.

> **RiskAssessment** — An analysis of business impact when a disruption affects the supply chain
> Use case: **Quantify impact in business terms (money and time) to prioritize response**

여기서 중요한 건 RiskAssessment가 **Tier 3: The analysis** 계층에 속한다는 점이다. 온톨로지의 7개 엔터티는 역할별로 층이 갈린다.

| Tier | 엔터티 | 역할 |
|---|---|---|
| 1 (네트워크) | Supplier / Component / ProductLine | 공급망의 **구조**(누가 무엇을 어디에 공급하는가) |
| 2 (교란) | DisruptionEvent | **사건**(무슨 일이 터졌는가) |
| 3 (분석) | **RiskAssessment** / MitigationAction | **판단**(그래서 얼마나 손해이고, 무엇을 할 것인가) |
| 4 (백업) | AlternativeSupplier | **대안**(누가 대신할 수 있는가) |

Tier 1·2는 사실(fact)만 담는다. "ChipX Corp이 GPU Module을 공급한다", "GPU Module의 `daysOfSupplyOnHand`가 3이다", "대만에 정전이 났다" — 이 자체로는 임원이 결재할 수 있는 정보가 아니다. 재고 일수가 3일이라는 사실은 **엔지니어의 언어**이고, "3일 뒤 8천만 달러가 날아간다"는 **경영진의 언어**다.

RiskAssessment는 Tier 1·2의 그래프를 순회해 얻은 기술적 사실을 **비즈니스 언어로 번역해 물화(materialize)한 노드**다. 그래서 그 다음 관계인 `RiskAssessment recommends MitigationAction` (1:N)이 성립한다. 정량화 없이는 "우선순위"라는 개념 자체가 정의되지 않고, 우선순위가 없으면 추천도 자동화도 불가능하다.

## 2. 두 축: 금액(`revenueAtRisk`)과 시간(`timeToImpactDays`)

RiskAssessment의 속성은 다음과 같다.

| 속성 | 타입 | 역할 |
|---|---|---|
| `assessmentId` | string(식별자) | 예: `RA-20240501-SEM-001` |
| `assessedDate` | **datetime** | 감사 추적·트렌딩 기준점 |
| `revenueAtRisk` | decimal (USD) | **금액 축** — 얼마나 큰 문제인가 |
| `timeToImpactDays` | integer | **시간 축** — 얼마나 급한 문제인가 |
| `confidenceLevel` | enum (High/Medium/Low) | 추정치의 신뢰도 |
| `recommendedAction` | string | 권고 요약 |

두 축이 **직교(orthogonal)한다**는 게 핵심이다. 하나만으로는 우선순위가 정해지지 않는다.

- 금액만 크고 시간이 넉넉하면(90일) → 중기 조달 협상으로 충분하다.
- 시간만 급하고 금액이 작으면(2일, 30만 달러) → 특송 한 건으로 끝난다.
- **둘 다 나쁘면** → 즉시 에스컬레이션 대상이다.

즉 `revenueAtRisk`는 **규모(severity of loss)**, `timeToImpactDays`는 **긴급도(urgency)**를 담는다. 이 2차원 좌표계 위에서만 "무엇을 먼저 할지"가 정의된다.

## 3. Phase 3 — 두 축이 어떻게 계산되는가

자동화 워크플로의 Phase 3(Quantify impact, 사건 발생 후 15분)에서 계산 엔진이 노출된 각 ProductLine에 대해 다음을 계산한다.

노출된 제품 라인 $p$에 대해:

$$
\text{revenueAtRisk}(p) = \frac{\text{annualRevenue}(p)}{365} \times \text{daysOfSupplyOnHand}(c)
$$

$$
\text{urgency}(p) = 100 - \bigl(\text{daysOfSupplyOnHand}(c) \times 10\bigr)
$$

그리고 집계한다.

$$
\text{totalRevenueAtRisk} = \sum_{p \in P_{\text{exposed}}} \text{revenueAtRisk}(p)
\qquad
P_{\text{critical}} = \{\, p \in P_{\text{exposed}} \mid \text{urgency}(p) > 70 \,\}
$$

원문의 실행 결과는 다음이었다.

```
Total at risk: $127M
Critical timeline: 3 days
Affected customers: 450,000+
```

각 식을 읽는 법:

- **금액 축**: 일 매출 $\frac{\text{annualRevenue}}{365}$ 에 노출 일수를 곱한 것. 즉 "재고가 버티는 창(window) 동안 걸려 있는 매출"을 화폐 단위로 환산한다. Tier 1의 `annualRevenue`(ProductLine)와 `daysOfSupplyOnHand`(Component)라는 **서로 다른 엔터티의 속성이 관계를 타고 하나의 수식에서 만난다** — `Component --usedIn--> ProductLine` (M:N) 관계가 없으면 이 곱셈 자체가 불가능하다. 여기서 M:N이라는 점이 곧 "부품 하나가 여러 제품 라인을 동시에 세운다"는 증폭 효과이고, $\sum$ 이 그 증폭을 금액으로 합산한다.
- **시간 축**: `urgency`는 `daysOfSupplyOnHand`의 선형 감소 함수다. $\text{urgency} > 70 \iff \text{daysOfSupplyOnHand} < 3$. 즉 재고 3일 미만이면 critical로 분류된다. 그리고 이 "가장 짧은 노출 일수"가 assessment의 `timeToImpactDays`로 굳어진다 — 캐스케이드 예시에서 `daysOfSupplyOnHand=3`인 GPU Module이 그대로 `timeToImpactDays=3`이 된 것이 그 예다.

> **참고 (모델링상의 거친 지점)**: 캐스케이드 예시에서는 Gaming Laptop($50M) + Workstation Pro($30M) = `revenueAtRisk=$80M`으로, 연매출을 그대로 더했다. Phase 3의 일할 계산식과는 산식이 다르다. 학습 자료가 "제품 라인 단위 일할 노출액"과 "연매출 전체 노출액"이라는 두 가지 해석을 섞어 쓴 것인데, 실무에서는 `revenueAtRisk`의 산식을 온톨로지 문서에 명시해 고정해야 한다. 이 모호함이 남아 있으면 뒤에 나오는 임계값(50M) 트리거가 산식에 따라 다르게 발화한다. — 바로 이 지점이 `confidenceLevel`이 필요한 이유와 직결된다.

## 4. Phase 5 — 두 축이 자동화 트리거가 된다

정량화의 최종 보상은 Phase 5(Execute, 25분)에서 나온다. 두 축이 **AND로 묶인 하나의 부울 조건**이 되어 사람 개입 없이 실행 워크플로를 발화시킨다.

$$
(\text{revenueAtRisk} > 50{,}000{,}000\ \text{USD}) \;\wedge\; (\text{timeToImpactDays} < 5)
$$

```
IF RiskAssessment.revenueAtRisk > $50M AND
   RiskAssessment.timeToImpactDays < 5:

   THEN:
     1. Create PurchaseOrder for recommended AlternativeSupplier
     2. Update ProductionSchedule with new timeline
     3. Send email to:
        - Procurement team (execute purchase)
        - Operations (adjust schedules)
        - Finance (forecast $2M additional cost)
        - CEO/Board (update on exposure)
     4. Create Activator alerts with escalation policy
     5. Start monitoring MitigationAction.status
```

여기서 확인할 점들.

- **왜 AND인가**: 금액만 크면 "큰돈이지만 아직 시간 있음"이므로 자동 발주까지 갈 필요가 없다. 시간만 급하면 "급하지만 소액"이므로 CEO에게 보고할 사안이 아니다. 두 축이 동시에 위험 영역에 들어왔을 때만 **자동 구매·자동 에스컬레이션이라는 비가역적이고 비용이 드는 행동**을 정당화한다. AND는 오탐(false positive)으로 인한 불필요한 프리미엄 지출과 임원 알람 피로를 막는 게이트다.
- **왜 이런 조건문이 가능한가**: `revenueAtRisk`가 decimal(USD), `timeToImpactDays`가 integer라는 **비교 가능한 수치 타입**이기 때문이다. 원문의 타입 표에도 `integer`는 "Threshold-based alerts", `decimal`은 "Cost-benefit calculations"이 용도로 적혀 있다. 만약 영향도가 "심각함/보통" 같은 서술형이었다면 임계값 비교식을 쓸 수 없고, 사람이 매번 읽고 판단해야 한다. 정량화는 곧 **기계 판독 가능성(machine-actionability)** 이다.
- **비용 대비 편익이 같은 단위로 비교된다**: MitigationAction의 `estimatedCost`(USD)와 `leadTimeSavedDays`도 정확히 같은 두 축(돈·시간)을 쓴다. 그래서 "8천만 달러 손실 대비 200만 달러 비용으로 2일 단축"이라는 비교가 성립한다.

$$
\text{ROI} \;\approx\; \frac{\text{revenueAtRisk} - \text{estimatedCost}}{\text{estimatedCost}}
\;=\; \frac{80\text{M} - 2\text{M}}{2\text{M}} = 39
$$

Phase 4의 추천 엔진이 "top 3 actions with ROI"를 순위화할 수 있는 이유가 여기 있다. **assessment의 축과 action의 축이 같은 단위계로 맞춰져 있어야** 순위 비교가 가능하다.

## 5. `confidenceLevel`은 왜 필요한가

`revenueAtRisk`와 `timeToImpactDays`는 **사실이 아니라 추정치**다. 근거 데이터가 모두 불확실하다.

- `estimatedDurationDays` — 정전/지진 복구가 며칠 걸릴지는 추정이다.
- `daysOfSupplyOnHand` — 재고 시스템의 최신성에 좌우된다.
- 대체 공급사의 실제 리드타임 — 확정 전이다.

따라서 `confidenceLevel`(High/Medium/Low)은 두 축의 숫자에 붙는 **품질 라벨**로서 다음 역할을 한다.

1. **의사결정 게이팅**: 같은 "$80M / 3일"이라도 Low confidence라면 즉시 200만 달러를 지출하기보다 먼저 재고 실사·공급사 확인 같은 검증 단계를 넣어야 한다. 임계값 트리거를 실무에 올릴 때 흔히 조건을 이렇게 강화한다.

$$
(\text{revenueAtRisk} > 50\text{M}) \wedge (\text{timeToImpactDays} < 5) \wedge (\text{confidenceLevel} \in \{\text{High}, \text{Medium}\})
$$

2. **가짜 정밀도(false precision) 방어**: "$127M"이라는 숫자는 소수점까지 정확해 보인다. 숫자만 있으면 받는 사람은 그것을 확정 사실로 오해한다. `confidenceLevel`은 정량화의 부작용인 과신을 명시적으로 상쇄한다.
3. **enum이라 결정 트리에 태울 수 있다**: 원문 타입 표에서 `enum`의 용도는 "Classification, decision trees"다. 자유 서술문("데이터가 좀 불확실함")이면 자동화가 읽을 수 없다.
4. **정확도 개선 루프의 입력**: 지속 개선 지표 중 "Impact estimate accuracy — Estimated vs. actual revenue at risk, 목표 ±10%"를 측정할 때, confidence 등급별로 실제 오차를 집계하면 "우리 High confidence 추정은 실제로 High인가"를 검증할 수 있다.

## 6. `assessedDate`(datetime)는 왜 필요한가

원문 타입 표는 `datetime`의 용도를 **"Audit trails, trending"**으로 못 박는다. DisruptionEvent의 `startDate`가 `date`인 것과 대비된다 — 사건 발생일은 날짜 단위로 충분하지만, **평가 시점은 분 단위로 필요하다**. 실제 워크플로가 분 단위로 흘러가기 때문이다(10:45 감지 → 10:46 추적 → 10:47 assessment 생성 → 10:48 action 생성).

### (1) 재계산 — assessment는 스냅샷이다

Day 2~4 모니터링 절차를 보면 명시적이다.

```
Every 4 hours:
  - Check DisruptionEvent.estimatedDurationDays (update if recovery changes)
  - Monitor MitigationAction progress
  - Recalculate RiskAssessment with latest inventory data
  - Alert if leadTimeSavedDays slips
```

즉 RiskAssessment는 **한 번 쓰고 끝나는 결론이 아니라 4시간마다 갱신되는 시계열 관측치**다. `assessedDate`가 있어야:

- **신선도 판정**: 지금이 $t$이고 평가 시각이 $t_a$일 때, 경과 시간 $\Delta t = t - t_a$ 가 재계산 주기(4시간)를 넘겼는지 판정한다. $\Delta t > 4\text{h}$ 이면 그 숫자로 발주를 걸어선 안 된다. 특히 `timeToImpactDays`는 **시간이 지나면 저절로 줄어드는(부패하는) 값**이다. 3일 전에 계산된 "3일 남음"은 사실상 "이미 늦음"이다. 엄밀히는 잔여 시간을 이렇게 봐야 한다.

$$
\text{timeRemaining}(t) = \text{timeToImpactDays} - \frac{t - t_a}{24\text{h}}
$$

  `assessedDate` 없이는 이 보정이 불가능하고, Phase 5의 `< 5` 비교는 어느 시점 기준인지 알 수 없는 무의미한 비교가 된다.

- **최신 판 선택**: 같은 DisruptionEvent가 여러 RiskAssessment를 만들고(1:N) 재계산으로 판본이 쌓인다. 대시보드와 에이전트는 $\arg\max_{a} \text{assessedDate}(a)$ 로 최신 평가를 골라야 한다.
- **트렌딩**: `revenueAtRisk`를 시간축에 놓으면 노출액이 줄고 있는지(완화가 먹히는지) 늘고 있는지가 보인다. 원문의 "Production impact reduced from 7 days → 3 days", "Revenue protected: ~$100M of $127M exposure" 같은 서술은 서로 다른 `assessedDate`를 가진 평가들을 비교해야 나오는 문장이다.

### (2) 감사 추적 — 왜 그때 그 결정을 했는가

Phase 5는 사람 승인 없이 발주서를 만들고 CEO/이사회에 통지하며 실제로 200만 달러를 쓴다. 사후에 반드시 이런 질문이 온다. "왜 12% 프리미엄을 주고 유럽에서 샀나?", "왜 더 일찍 안 움직였나?"

답은 "**그 시각에 우리가 알고 있던 데이터로는 $80M / 3일 / High confidence였다**"여야 한다. 이를 위해 필요한 것이:

- `assessmentId` — 어떤 평가인지 지목
- `assessedDate` — **언제 기준의 판단인지** 고정
- `confidenceLevel` — 그 판단이 얼마나 확실했는지 기록
- `recommendedAction` — 무엇을 권고했는지

즉 `assessedDate` + `confidenceLevel`은 **불변 기록(immutable record)의 좌표와 품질 태그**다. 재계산 결과를 기존 레코드에 덮어쓰지 않고 새 `assessmentId`로 append하면(append-only), 시점별 판단 이력이 그대로 감사 증적이 된다. 값을 갱신해버리면 트렌딩도 감사도 동시에 불가능해진다.

또한 "Detection speed — Hours from disruption to RiskAssessment, 목표 < 1시간"이라는 KPI는 문자 그대로

$$
\text{detectionSpeed} = \text{assessedDate} - \text{DisruptionEvent.startDate} < 1\text{h}
$$

로 계산된다. `assessedDate`가 없으면 이 KPI 자체를 측정할 수 없다. `startDate`가 `date`, `assessedDate`가 `datetime`인 조합이라 시간 단위 KPI를 재려면 사실 사건 시각도 datetime이어야 한다는 점은 실무 적용 시 보완할 부분이다.

## 7. 한 장 요약

```
Tier 1·2 (사실)                    Tier 3 (판단)                  자동 실행
────────────────────              ─────────────────────          ─────────────
annualRevenue      ┐
daysOfSupplyOnHand ├─ Phase 3 ─▶  revenueAtRisk    ($)  ┐
estimatedDuration  ┘   계산식      timeToImpactDays (일) ├─ AND ─▶ PO 발행
                                   confidenceLevel  (신뢰) │        스케줄 갱신
                                   assessedDate  (시점/감사)┘        임원 알림
                                          │
                                          └─ recommends ─▶ MitigationAction
                                                            (estimatedCost $,
                                                             leadTimeSavedDays 일)
                                                             → 같은 두 축으로 ROI 비교
```

- **핵심**: RiskAssessment = 기술적 사실을 **돈·시간**으로 번역해 우선순위를 만드는 엔터티.
- **두 축**: `revenueAtRisk`(규모) × `timeToImpactDays`(긴급도) → Phase 3에서 계산되고 Phase 5에서 `> $50M AND < 5일` 임계값으로 자동 실행을 발화.
- **두 축을 신뢰 가능하게 만드는 메타 속성**: `confidenceLevel`(추정치의 품질 게이팅), `assessedDate`(재계산 신선도 + 감사 추적).
