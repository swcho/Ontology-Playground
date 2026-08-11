# 완화 모델의 효과를 측정하는 6가지 지표

## 정답 한 줄 요약

**Detection speed · Trace accuracy · Impact estimate accuracy · Time to mitigation · Cost efficiency · Revenue protection rate** — 6개 각각에 목표치(goal)가 정의되어 있다.

원문(Mitigation Execution & Automation → *Continuous improvement*)의 표를 그대로 옮기면:

| # | Metric | Calculation | Goal |
|---|---|---|---|
| 1 | Detection speed | Hours from disruption to RiskAssessment | **< 1 hour** |
| 2 | Trace accuracy | % of actual affected components identified | **> 95%** |
| 3 | Impact estimate accuracy | Estimated vs. actual revenue at risk | **±10%** |
| 4 | Time to mitigation | Hours from assessment to MitigationAction execution | **< 2 hours** |
| 5 | Cost efficiency | Actual cost vs. estimated cost of actions | **±5%** |
| 6 | Revenue protection rate | % of at-risk revenue protected by actions | **> 80%** |

핵심 관점: 이 6개는 온톨로지가 있어야만 **자동 계산이 가능한** 지표다. 각 지표의 분자·분모가 모두 특정 엔터티의 속성값이나 타임스탬프이기 때문이다. 그래서 "지표 6개 암기"는 곧 "어떤 속성이 어떤 지표를 지탱하는가"를 아는 것과 같다.

---

## 1. 계산식 · 목표치 · 필요한 온톨로지 속성

$D$ = DisruptionEvent, $RA$ = RiskAssessment, $MA$ = MitigationAction으로 표기한다.

| # | 지표 | 수식 | 목표 | 측정에 필요한 속성 / 데이터 |
|---|---|---|---|---|
| 1 | Detection speed | $T_{detect} = t(RA.\text{assessedDate}) - t(D.\text{startDate})$ | $< 1\,\text{h}$ | `DisruptionEvent.startDate`(교란 발생), `RiskAssessment.assessedDate`(datetime) |
| 2 | Trace accuracy | $A_{trace} = \dfrac{\lvert C_{found} \cap C_{actual}\rvert}{\lvert C_{actual}\rvert}$ | $> 95\%$ | `Supplier → supplies → Component` 순회 결과의 `componentId` 집합 vs 사후 확인된 실제 영향 부품 집합 |
| 3 | Impact estimate accuracy | $\varepsilon_{impact} = \dfrac{R_{est} - R_{actual}}{R_{actual}}$ | $\lvert\varepsilon\rvert \le 10\%$ | `RiskAssessment.revenueAtRisk`(추정), 입력값 `ProductLine.annualRevenue` · `Component.daysOfSupplyOnHand`, 사후 실측 노출액 |
| 4 | Time to mitigation | $T_{mitigate} = t(MA.\text{status} \rightarrow \textit{In Progress}) - t(RA.\text{assessedDate})$ | $< 2\,\text{h}$ | `RiskAssessment.assessedDate`, `MitigationAction.status` 전이 타임스탬프(Proposed→Approved→In Progress) |
| 5 | Cost efficiency | $\varepsilon_{cost} = \dfrac{C_{actual} - C_{est}}{C_{est}}$ | $\lvert\varepsilon\rvert \le 5\%$ | `MitigationAction.estimatedCost` vs 실제 비용(`actualCost`), 참고 `AlternativeSupplier.pricePremiumPercent` |
| 6 | Revenue protection rate | $P = \dfrac{R_{protected}}{R_{atRisk}}$ | $> 80\%$ | `RiskAssessment.revenueAtRisk`(분모), 보호 금액 = 노출액 − 실손실(→ `ProductLine.productionStatus` 회복 이력, 실제 출하 매출) |

### 온톨로지 속성만으로 부족한 지점 (설계 갭)

지표 6개를 실제로 계산해 보면 원문 속성 목록에 **구멍 3개**가 드러난다. 이 갭을 아는 것이 이 카드의 실전 가치다.

| 갭 | 문제 | 해결 |
|---|---|---|
| `DisruptionEvent.startDate`가 `date` 타입 | 지표 1은 **시간 단위**인데, 날짜만 있으면 "10:30 → 10:47 = 17분"을 계산할 수 없다 | `datetime`으로 승격하거나 `detectedAt` 속성 추가 |
| `MitigationAction.status`는 enum(현재 상태)뿐 | 지표 4는 **상태 전이 시각**이 필요한데, 현재 상태만 저장하면 언제 In Progress가 되었는지 모른다 | 상태 변경 이력(status history) 또는 `approvedAt` / `startedAt` / `completedAt` |
| 사후 실측값(actual) 부재 | 지표 2·3·6은 모두 "actual"이 분모 또는 비교 대상이다. 온톨로지는 추정치만 갖고 있다 | 사후 검증 필드(`actualCost`, `actualRevenueAtRisk`, 확정 영향 부품 목록) — 원문의 "actual vs. estimated effectiveness" 추적이 여기에 해당 |

> 즉 6개 지표 중 **1·4는 타임스탬프 문제**, **2·3·6은 ground truth(실측) 문제**, **5만 온톨로지가 이미 추정·실제 쌍을 갖고 있는 지표**다.

---

## 2. Day 1~3 사례로 실제 채점하기

원문 *Real-world workflow*의 로그를 원천 데이터로 삼는다.

```
Day 1  10:30 AM  대만 지진 M6.8 발생                    → D.startDate
       10:45 AM  DisruptionEvent 생성 (탐지)
       10:46 AM  Data Agent 추적: 공급사 3 / 부품 47 / 제품라인 12 / $127M / 3일
       10:47 AM  RiskAssessment 생성                    → RA.assessedDate
       10:48 AM  MitigationAction 자동 생성 (PO 발행)
       10:50 AM  Activator 발동 (대시보드·에스컬레이션)
       11:30 AM  MA.status = "In Progress"
Day 3            ChipX Europe 입고 → MA.status = "Completed"
                 부품 47개 재고 회복, 생산 재개 (7일 → 3일 지연)
                 실제 비용 $2.1M (추정 $2M)
                 보호된 매출 ~$100M / 노출 $127M
```

### 지표 1 — Detection speed: **통과 (여유 큼)**

$$
T_{detect} = 10{:}47 - 10{:}30 = 17\ \text{min} = 0.283\ \text{h} \;<\; 1\ \text{h}
$$

목표 대비 여유는 $1 - 0.283 = 0.717\,\text{h}$(약 43분). 참고로 중간 마일스톤도 모두 1시간 안에 들어온다: 탐지 15분, 추적 16분, 평가 17분, 조치 생성 18분, Activator 20분. **"1시간 목표에 대해 20분에 전 파이프라인 종료"** 가 이 사례의 성적이다.

$$
\text{여유율} = 1 - \frac{0.283}{1} \approx 71.7\%
$$

### 지표 2 — Trace accuracy: **통과 (단, 검증 조건부)**

에이전트가 찾은 부품은 47개이고, Day 3에 "부품 47개 재고 회복"으로 동일한 47이 확인된다. 사후 실제 집합이 47이었다고 보면

$$
A_{trace} = \frac{47}{47} = 100\% \;>\; 95\%
$$

다만 원문은 **독립적인 ground truth를 제시하지 않는다**(찾은 47을 그대로 복구했을 뿐). 그래서 실무에서는 경계값을 함께 계산해 두어야 한다. 놓친 부품이 있어도 목표를 지키려면

$$
\frac{47}{\lvert C_{actual}\rvert} > 0.95 \;\Longrightarrow\; \lvert C_{actual}\rvert < \frac{47}{0.95} = 49.47 \;\Longrightarrow\; \lvert C_{actual}\rvert \le 49
$$

즉 실제 영향 부품이 **49개까지면 통과, 50개면 실패**($47/50 = 94\%$). 미탐지 허용치가 단 2개라는 뜻이고, 지표 2가 왜 47개짜리 추적에서도 빡빡한 목표인지 보여준다.

### 지표 3 — Impact estimate accuracy: **채점 불가 (실측 부재) + 허용 구간 계산**

추정치는 $R_{est} = \$127\text{M}$이다. 원문에는 사후 확정 노출액이 없으므로 이 지표만은 **점수를 매길 수 없다**. 대신 통과 조건을 역산한다.

$$
\left\lvert \frac{127 - R_{actual}}{R_{actual}} \right\rvert \le 0.10
\;\Longrightarrow\;
R_{actual} \in \left[\frac{127}{1.1},\; \frac{127}{0.9}\right] = [\,115.5\text{M},\; 141.1\text{M}\,]
$$

실제 노출이 $115.5M~$141.1M 안이면 통과다. 흔한 오답: **보호 금액 $100M을 "actual"로 착각**해서

$$
\frac{127 - 100}{100} = +27\% \;\gg\; 10\%
$$

로 실패 판정하는 것. $100M은 "지켜낸 금액"이지 "실제 위험 노출액"이 아니다. 지표 3의 비교쌍은 (추정 노출 vs 실제 노출)이고, $100M이 들어가는 곳은 지표 6이다.

> **추정 로직 자체의 함정**: 원문 Phase 3의 공식은 $R = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$ 인데, 캐스케이드 예시의 $80M은 두 제품라인 연매출($50M + $30M)의 **단순 합**이다. 공식대로면
> $$\frac{80\text{M}}{365}\times 3 \approx 0.66\text{M}$$
> 로 **약 121배 차이**가 난다. 즉 $127M은 "연매출 기준 노출"이고 공식은 "재고 소진 기간 동안의 일할(pro-rated) 노출"이다. 지표 3이 ±10%를 지키느냐는, 계산 이전에 **어느 정의를 쓰는지 합의했는가**에 달려 있다.

### 지표 4 — Time to mitigation: **통과 (정의에 따라 뒤집힘)**

"MitigationAction execution"을 어느 `status` 전이로 볼지에 따라 세 가지 답이 나온다.

| 기준 시각 | 해당 status | $T_{mitigate}$ | 판정 |
|---|---|---|---|
| 10:48 AM (조치 자동 생성, PO 발행) | Proposed / Approved | $1\ \text{min} = 0.017\,\text{h}$ | 통과 |
| **11:30 AM (실행 착수)** | **In Progress** | $43\ \text{min} = 0.717\,\text{h}$ | **통과** |
| Day 3 (입고 완료) | Completed | $\approx 48\text{--}50\,\text{h}$ | 실패 |

$$
T_{mitigate} = 11{:}30 - 10{:}47 = 43\ \text{min} = 0.717\ \text{h} \;<\; 2\ \text{h}
$$

원문 문구가 "assessment to MitigationAction **execution**"이므로 **In Progress 기준 0.72시간**이 정답 채점값이다(목표의 36%만 사용, 여유 1.28시간). Completed까지 재는 순간 모든 물리적 배송이 지표를 파괴하므로, 이 지표는 **의사결정·착수 속도**를 재는 것이고 리드타임은 `leadTimeSavedDays`가 따로 담당한다.

### 지표 5 — Cost efficiency: **경계 통과 (여유 0)**

$$
\varepsilon_{cost} = \frac{2.1 - 2.0}{2.0} = 0.05 = +5.0\%
$$

허용 구간은 $\lvert\varepsilon\rvert \le 5\%$, 금액으로는

$$
C_{actual} \in [\,2.0 \times 0.95,\; 2.0 \times 1.05\,] = [\,1.9\text{M},\; 2.1\text{M}\,]
$$

$2.1M은 **상한과 정확히 일치** — 통과이지만 여유가 0인 borderline pass다. $0.1M만 더 썼다면($2.2M → +10%) 위반. 추정에 이미 `pricePremiumPercent = 12%`가 반영되어 있었으므로, 초과 $0.1M은 프리미엄이 아니라 **48시간 긴급 배송처럼 추정 모델에 없던 항목**에서 나왔다고 읽는 것이 자연스럽다.

### 지표 6 — Revenue protection rate: **목표 미달 (유일한 실패)**

$$
P = \frac{R_{protected}}{R_{atRisk}} = \frac{100}{127} = 0.7874 = 78.7\% \;\not>\; 80\%
$$

약 **1.3%p 미달**. 목표를 채우려면 필요한 보호 금액은

$$
R_{required} = 0.80 \times 127 = 101.6\text{M} \quad\Rightarrow\quad \Delta = 101.6 - 100 = 1.6\text{M}
$$

미보호 노출은 $127 - 100 = 27\text{M}\ (21.3\%)$이다. 그럼에도 투자 효율만 보면

$$
\text{ROI} = \frac{100\text{M}}{2.1\text{M}} \approx 47.6\times
$$

로 압도적이다. **"ROI 47배인데 지표는 실패"** 라는 조합이 이 지표의 존재 이유다 — 절대 이득이 아니라 **노출 대비 커버리지**를 강제한다.

### 종합 스코어카드

| # | 지표 | 사례 값 | 목표 | 판정 | 여유/부족 |
|---|---|---|---|---|---|
| 1 | Detection speed | 0.28 h (17분) | < 1 h | ✅ 통과 | +0.72 h |
| 2 | Trace accuracy | 47/47 = 100% | > 95% | ✅ 통과 | 미탐지 2개까지 허용 |
| 3 | Impact estimate accuracy | 추정 $127M, 실측 없음 | ±10% | ⚠️ 채점 불가 | 통과 구간 $115.5M~$141.1M |
| 4 | Time to mitigation | 0.72 h (43분) | < 2 h | ✅ 통과 | +1.28 h |
| 5 | Cost efficiency | +5.0% ($2.1M/$2.0M) | ±5% | 🟡 경계 통과 | 여유 0 |
| 6 | Revenue protection rate | 78.7% ($100M/$127M) | > 80% | ❌ 미달 | −1.3%p ($1.6M) |

읽어야 할 패턴: **속도 지표는 압승, 성과 지표는 아슬아슬하거나 실패.** 자동화가 잘 된 부분(탐지·추적·의사결정)과 아직 물리 세계에 묶여 있는 부분(비용·매출 보호)이 지표에 그대로 나타난다. 다음 사이클의 개선 우선순위는 지표 6 → 5 → 3 순이다.

---

## 3. 6개를 3계열 × 2개로 묶어 외우기

지표를 순서대로 외우면 잘 빠뜨린다. **계열 2개씩**으로 묶으면 "각 계열에 두 개"라는 구조가 회수(recall) 단서가 된다.

| 계열 | 지표 2개 | 단위 | 공통 질문 | 목표 형태 |
|---|---|---|---|---|
| ⏱ **속도계열** | Detection speed / Time to mitigation | 시간(h) | "얼마나 **빨리**?" | 상한 미만 ( < 1h, < 2h ) |
| 🎯 **정확도계열** | Trace accuracy / Impact estimate accuracy | %, 편차 | "얼마나 **맞게**?" | 하한 초과 / 밴드 ( > 95%, ±10% ) |
| 💰 **성과계열** | Cost efficiency / Revenue protection rate | 금액 비율 | "얼마나 **남겼나**?" | 밴드 / 하한 초과 ( ±5%, > 80% ) |

각 계열 안에서 두 지표는 **파이프라인의 앞/뒤 짝**을 이룬다.

```
        앞 단계               뒤 단계
속도 :  Detection speed  ──▶  Time to mitigation      (탐지 → 착수)
정확 :  Trace accuracy   ──▶  Impact estimate acc.    (무엇이 → 얼마나)
성과 :  Cost efficiency  ──▶  Revenue protection      (쓴 돈 → 지킨 돈)
```

### 암기 문구

> **빨리 보고 빨리 움직이고 · 넓게 맞히고 크게 맞히고 · 싸게 하고 많이 지키기**

- 빨리 보고 = Detection speed (< 1h) / 빨리 움직이고 = Time to mitigation (< 2h) → **1시간, 2시간**
- 넓게 맞히고 = Trace accuracy (> 95%, 부품 개수의 폭) / 크게 맞히고 = Impact estimate accuracy (±10%, 금액의 크기)
- 싸게 하고 = Cost efficiency (±5%) / 많이 지키기 = Revenue protection rate (> 80%)

### 목표치 숫자만 따로 외우는 법

$$
\underbrace{1\,\text{h},\ 2\,\text{h}}_{\text{속도}} \quad\Big|\quad \underbrace{95\%,\ \pm10\%}_{\text{정확도}} \quad\Big|\quad \underbrace{\pm5\%,\ 80\%}_{\text{성과}}
$$

- 속도는 **1 → 2** (탐지가 완화보다 빠듯하다. 탐지는 자동, 완화는 승인 절차가 끼기 때문)
- 밴드형(±) 지표는 정확도에 하나(±10%), 성과에 하나(±5%) — **돈 쓰는 쪽(±5%)이 더 엄격**하다
- 하한형(>) 지표는 **95% / 80%** — 부품을 놓치는 건 거의 용납 안 되지만(95%), 매출은 100% 방어가 불가능하므로 80%로 현실화

### 각 지표를 뒷받침하는 온톨로지 축 (교차 암기)

| 계열 | 의존하는 온톨로지 요소 |
|---|---|
| 속도 | **타임스탬프** — `startDate`, `assessedDate`, `status` 전이 시각 |
| 정확도 | **관계 순회 + 추정 공식** — `supplies` / `usedIn`, `revenueAtRisk` |
| 성과 | **추정·실제 쌍** — `estimatedCost` vs 실제비용, `revenueAtRisk` vs 보호액 |

원문이 이 지표들을 "Continuous improvement"에 배치한 이유도 여기 있다. 교란 이벤트마다 (추정, 실제) 쌍이 축적되고, 에이전트는 **어느 대체 공급사가 실제로 제 성능을 냈는지, 어느 리드타임이 지켜졌는지, 어느 제품라인이 회복력이 좋은지**를 학습한다. 지표 6개는 그 학습의 손실 함수 역할을 한다.

---

## 4. 암기 포인트

- **6개 = 속도 2 + 정확도 2 + 성과 2**: Detection speed / Time to mitigation · Trace accuracy / Impact estimate accuracy · Cost efficiency / Revenue protection rate.
- 목표치 세트: **< 1h · > 95% · ±10% · < 2h · ±5% · > 80%**. "1, 95, 10, 2, 5, 80".
- 지표 1의 종점은 **RiskAssessment 생성**(교란 인지가 아니라 정량 평가 완료 시점)이고, 지표 4의 시점은 **그 RiskAssessment**다. 두 지표가 `assessedDate`를 공유하며 이어 붙는다.
- 지표 4는 `MitigationAction`의 **실행 착수(In Progress)** 기준. Completed(Day 3 입고)로 재면 실패한다.
- Day 1~3 사례 성적: **1·2·4 통과 / 5 경계 통과(+5.0%, 여유 0) / 6 미달(78.7%) / 3은 실측 부재로 채점 불가.**
- 흔한 함정: 지표 개수를 5개나 7개로 세기 / 지표 3에 보호액 $100M을 대입해 −27%로 오채점 / Cost efficiency를 "절대 비용 절감"으로 오해(실제는 **추정 대비 편차**) / Revenue protection rate 분모를 연매출로 착각(분모는 `revenueAtRisk` = $127M).
