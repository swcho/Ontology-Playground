# 2M 달러 조치 비용을 정당화하는 근거

## 질문

2M 달러의 조치 비용을 정당화하는 근거는?

## 정답

80M 달러 규모의 매출 손실을 막기 위해 2M 달러를 쓰고 리드타임 2일을 절약하는 것이므로, 비용 대비 편익이 압도적이다. 온톨로지가 두 숫자를 같은 그래프에서 제공하기 때문에 이 비교가 가능하다.

---

## 1. 어떤 숫자가 어디에서 나오는가

정당화의 핵심은 "돈"과 "시간"을 각각 **위험 쪽**과 **조치 쪽**에서 짝지어 비교하는 것이다. 두 짝 모두 서로 다른 엔티티의 속성이다.

| 축 | 위험 쪽 (RiskAssessment) | 조치 쪽 (MitigationAction) |
|---|---|---|
| 돈 | `revenueAtRisk` = **$80M** | `estimatedCost` = **$2M** |
| 시간 | `timeToImpactDays` = **3일** | `leadTimeSavedDays` = **2일** |

- `revenueAtRisk`, `timeToImpactDays`, `confidenceLevel`, `recommendedAction` → **RiskAssessment** 엔티티 속성
- `estimatedCost`, `leadTimeSavedDays`, `type`, `status` → **MitigationAction** 엔티티 속성
- `pricePremiumPercent`, `capacityAvailable`, `qualificationStatus` → **AlternativeSupplier** 엔티티 속성

즉 비교에 필요한 네 숫자는 **세 개의 서로 다른 엔티티**에 흩어져 있다. 이것이 뒤에 나오는 "같은 그래프" 논점의 전제다.

시나리오상 $80M의 출처는 노출된 두 제품 라인의 연매출 합이다.

$$
\text{revenueAtRisk} = \underbrace{\$50\text{M}}_{\text{Gaming Laptop 2024}} + \underbrace{\$30\text{M}}_{\text{Workstation Pro}} = \$80\text{M}
$$

그리고 `timeToImpactDays` = 3일은 `Component "GPU Module"`의 `daysOfSupplyOnHand=3`에서 곧바로 유도된다. 재고 3일치가 소진되면 생산이 멈춘다.

## 2. 왜 2M이 정당한가 — 두 가지 계산 방식

### (a) 노출 기준 (asset가 실제로 쓰는 방식)

$$
\text{ROI ratio} = \frac{\text{revenueAtRisk}}{\text{estimatedCost}} = \frac{80{,}000{,}000}{2{,}000{,}000} = 40
$$

$$
\text{Net benefit} = \$80\text{M} - \$2\text{M} = \$78\text{M}
$$

조치 비용이 방어 대상 매출의 $2.5\%$에 불과하다.

$$
\frac{\$2\text{M}}{\$80\text{M}} = 0.025 = 2.5\%
$$

"$2M vs. $80M loss"라는 표현이 asset 4장(Phase 4 / 자동화 요약)에서 반복되는 이유가 이것이다. 의사결정 규칙 자체도 노출 금액 기준으로 쓰여 있다.

```
IF RiskAssessment.revenueAtRisk > $50M AND
   RiskAssessment.timeToImpactDays < 5:
   THEN 자동 실행 (PO 발행, 스케줄 갱신, 알림, Activator)
```

$80\text{M} > 50\text{M}$ 이고 $3 < 5$ 이므로 두 조건이 모두 참 → 사람의 승인 대기 없이 조치가 자동 기동된다. 즉 2M의 정당화는 애드혹 판단이 아니라 **온톨로지 속성 위에 선언된 임계값 규칙**의 결과다.

### (b) 시간 절감 기준 (한계 편익 관점)

`leadTimeSavedDays`를 일 단위 매출로 환산하면 더 보수적인 하한이 나온다.

$$
\text{daily revenue} = \frac{\$80\text{M}}{365} \approx \$219\text{K/day}
$$

$$
\text{benefit}_{\text{time}} = 219\text{K} \times 2\ \text{days} \approx \$438\text{K}
$$

이 계산만 보면 $438\text{K} < \$2\text{M}$ 이라 조치가 정당화되지 않는다. **여기서 두 방식의 차이를 이해하는 것이 이 카드의 진짜 학습 포인트다.**

- (b)는 "생산이 2일 덜 멈춘다"는 **선형적 지연 손실**만 센다.
- (a)는 "생산이 멈추면 해당 제품 라인의 주문 이행·고객·채널 자체가 위험해진다"는 **단절 손실**을 센다. `ProductLine.productionStatus`가 `Halted`로 넘어가면 잃는 것은 2일치 매출이 아니라 라인 전체의 매출 실현 가능성이다.

asset의 Phase 3 계산식은 (b)에 가까운 프로레이팅 식이다.

$$
\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}
$$

$$
\text{urgency} = 100 - (\text{daysOfSupplyOnHand} \times 10)
$$

$$
\text{urgency} = 100 - (3 \times 10) = 70
$$

반면 캐스케이드 예시의 `revenueAtRisk=$80M`은 노출 라인의 연매출 총액이다. **동일 문서 안에 두 관례가 공존한다**는 점을 알아두면 좋다. 실제 온톨로지를 구축할 때는 `revenueAtRisk`의 정의(연매출 노출액인가, 중단 기간 프로레이팅액인가)를 한 가지로 고정하고 `confidenceLevel`로 불확실성을 표시해야 한다. 이 카드/시나리오가 채택한 관례는 (a) 노출 기준이며, `> $50M` 임계값도 그 관례에 맞춰 조정된 값이다.

## 3. 대안 조치 A / B / C의 ROI 비교

Phase 4의 추천 엔진은 상위 3개 액션을 ROI와 함께 제시한다.

| 액션 | `type` | `estimatedCost` | `leadTimeSavedDays` | 커버 범위 | 판정 |
|---|---|---|---|---|---|
| **A** ChipX Europe 가동 | Activate Alternative Supplier | **$2M** | **2일** | 공급 자체를 복구 (50K units/month) | 채택 |
| **B** 안전 재고 증대 | Increase Safety Stock | **$500K** | 미정 | 약 2주간 시간 벌기 | 보완 병행 |
| **C** 부품 재설계 | Redesign Component | 미정 | **미정(unknown)** | 구조적 해결 | 이번 사이클 제외 |

### A — 채택 이유

$$
\text{ROI}_A = \frac{80\text{M}}{2\text{M}} = 40\times
$$

`AlternativeSupplier "ChipX Europe"`가 `qualificationStatus=Approved`, `capacityAvailable=50,000 units/month`라서 **즉시 발주 가능**하다. `timeToImpactDays=3` 안에 실행 가능한 유일한 "공급 복구" 액션이다. 실제로 Day 1 11:30에 48시간 출하 확약을 받아 생산 영향이 7일 → 3일로 줄었다.

### B — 비율은 더 높지만 단독으로는 부족

$$
\text{ROI}_B^{\text{nominal}} = \frac{80\text{M}}{0.5\text{M}} = 160\times
$$

명목 배수는 A의 4배다. 그런데도 A가 1순위인 이유:

1. **`leadTimeSavedDays`가 정의되지 않는다.** 안전 재고는 리드타임을 줄이는 게 아니라 소진 시점을 미루는 것이다. 즉 B는 `timeToImpactDays`를 3일 → 약 14일로 늘리지만, 공급 재개 자체를 만들지 못한다.
2. **커버 범위에 만료가 있다.** `estimatedDurationDays=7`(초기 추정)보다는 14일 커버가 길지만, 추정치가 늘어나면 방어선이 무너진다. Day 2–4 모니터링 루프가 `estimatedDurationDays`를 4시간마다 재확인하는 이유다.
3. 따라서 B는 A의 **대체재가 아니라 시간 완충재**다. 실제 워크플로에서도 A(PO 발행)와 B(안전 재고 발주)가 10:48에 함께 생성된다.

### C — ROI 계산 자체가 불가능

$$
\text{ROI}_C = \frac{80\text{M}}{\text{cost}_C},\quad \text{cost}_C = \text{unknown},\ \text{leadTimeSaved}_C = \text{unknown}
$$

분모가 미정이면 순위를 매길 수 없다. 게다가 부품 재설계 리드타임은 통상 주·월 단위이므로 `timeToImpactDays=3`이라는 제약을 구조적으로 만족할 수 없다. C는 **이번 사고 대응이 아니라 `singleSourced=true` 리스크를 제거하는 다음 분기 과제**로 분류되어야 한다. 여기서 배울 점: 값이 비어 있는 속성은 자동 랭킹에서 조용히 탈락하며, 그래서 `estimatedCost`/`leadTimeSavedDays`를 채워두는 데이터 품질이 곧 자동화 품질이다.

## 4. `pricePremiumPercent` = 12% — 잊기 쉬운 지속 비용

`estimatedCost=$2M`은 **일회성 전환·가동 비용**이다. 반면 `AlternativeSupplier.pricePremiumPercent=12%`는 ChipX Europe로부터 조달하는 **기간 내내 단가에 붙는 반복 비용**이다.

$$
\text{unit cost}_{\text{alt}} = \text{unit cost}_{\text{primary}} \times (1 + 0.12)
$$

따라서 총소유비용은 다음과 같이 확장된다.

$$
\text{TCO} = \underbrace{\$2\text{M}}_{\text{일회성 activation}} + \underbrace{0.12 \times S \times d}_{\text{프리미엄 누적}}
$$

여기서 $S$는 일평균 조달 지출, $d$는 대체 공급 유지 일수다. 예를 들어 해당 부품 조달 지출이 월 $\$10\text{M}$이고 2개월간 대체 공급을 유지하면

$$
0.12 \times \$10\text{M} \times 2 = \$2.4\text{M}
$$

프리미엄만으로 초기 $2M을 넘어선다. 그래도 결론은 바뀌지 않는다.

$$
\$2\text{M} + \$2.4\text{M} = \$4.4\text{M} \ll \$80\text{M}
\quad\Rightarrow\quad \text{ROI} \approx 18\times
$$

즉 12% 프리미엄은 **판단을 뒤집지는 않지만 반드시 재무에 통보되어야 하는 항목**이다. Phase 5의 자동 알림에 Finance가 포함되어 "$2M 추가 비용 예측"을 받는 것, 그리고 대안 후보들이 프리미엄과 함께 나열되는 것이 그 장치다.

| 대안 | capacity | pricePremiumPercent |
|---|---|---|
| ChipX Europe | 50K/month | **+12%** |
| SemiCorp Japan | 30K/month | +18% |
| Semiconductor Direct USA | 25K/month | +15% |

Phase 4의 스코어링이 `leadTimeSavedDays`(시간), `pricePremiumPercent`(비용), `reliabilityScore`(신뢰도) 세 축을 함께 쓰는 이유가 여기서 드러난다. ChipX Europe는 용량이 가장 크고 프리미엄이 가장 낮아 세 축에서 동시에 우세하다.

## 5. Day 3 검증 — 추정치를 사후에 채점하는 루프

추정으로 끝나면 그것은 정당화가 아니라 주장이다. Day 3에 실제값이 들어온다.

```
Day 3: ChipX Europe shipment received
  ├─ MitigationAction.status = "Completed"
  ├─ Actual cost: $2.1M (estimated $2M)
  ├─ Production resumes (3-day delay, not 7-day)
  ├─ Revenue protected: ~$100M of $127M exposure
```

**Cost efficiency** 지표(목표 $\pm5\%$)로 채점한다.

$$
\text{Cost efficiency} = \frac{|\,\text{actual} - \text{estimated}\,|}{\text{estimated}} = \frac{|2.1 - 2.0|}{2.0} = 0.05 = 5\%
$$

$5\% \le 5\%$ → **목표 경계에서 통과**. 여유가 전혀 없는 합격이므로, 다음 사이클에서 활성화 비용 추정 모델을 손볼 신호로 읽는 것이 맞다.

같은 방식으로 다른 지표도 검증된다.

$$
\text{Revenue protection rate} = \frac{\$100\text{M}}{\$127\text{M}} \approx 78.7\% \;(<80\%\ \text{목표, 미달})
$$

$$
\text{Detection speed} = \text{10:30} \rightarrow \text{10:47} = 17\ \text{min} \;(<1\text{h}, \text{통과})
$$

$$
\text{Time to mitigation} = \text{10:47} \rightarrow \text{10:48} = 1\ \text{min} \;(<2\text{h}, \text{통과})
$$

여기서 `$127M`은 12개 제품 라인 전체 노출액이고 `$80M`은 GPU Module 경로의 두 라인 노출액이다. **범위가 다른 숫자를 섞어 쓰지 않도록 주의**해야 한다. 2M을 정당화하는 짝은 어디까지나 동일 `RiskAssessment` 노드에 달린 $80M이다.

$$
\text{추정} \rightarrow \text{실행} \rightarrow \text{실측} \rightarrow \text{지표 채점} \rightarrow \text{추정 모델 보정}
$$

이 되먹임이 있어야 `estimatedCost`가 다음 사고에서도 신뢰할 수 있는 의사결정 입력으로 남는다. asset이 "Each disruption event becomes a training opportunity"라고 말하는 지점이다.

## 6. "온톨로지가 두 숫자를 같은 그래프에서 제공한다"의 의미

$80M과 $2M은 원래 다른 시스템에 산다. ERP/재무에는 매출이, 조달 시스템에는 발주 비용이, 공급사 마스터에는 프리미엄이 있다. 스프레드시트로는 이 조인에 며칠이 걸린다("this analysis takes days and manual spreadsheets").

온톨로지에서는 관계 하나를 타면 두 값이 나란히 놓인다.

```
DisruptionEvent
  └─ affects → Supplier "ChipX Corp" (singleSourced=true)
       └─ supplies → Component "GPU Module" (daysOfSupplyOnHand=3)
            ├─ usedIn → ProductLine "Gaming Laptop 2024" ($50M)
            ├─ usedIn → ProductLine "Workstation Pro"   ($30M)
            └─ triggers → RiskAssessment
                 ├─ revenueAtRisk = $80M        ← 편익(방어 대상)
                 ├─ timeToImpactDays = 3        ← 제약(마감)
                 └─ recommends → MitigationAction "Activate ChipX Europe"
                      ├─ estimatedCost = $2M        ← 비용
                      ├─ leadTimeSavedDays = 2      ← 효과
                      └─ activates → AlternativeSupplier "ChipX Europe"
                           └─ pricePremiumPercent = 12%  ← 지속 비용
```

결정적인 간선은 **`RiskAssessment` --recommends(1:N)--> `MitigationAction`** 이다. 이 간선 하나 덕분에 "위험을 정량화한 노드"와 "그 위험을 줄이는 비용 노드"가 직접 이웃이 되고, 비용·편익이 **동일 트래버설 안에서** 동시에 읽힌다. 이어지는 `MitigationAction` --activates(M:N)--> `AlternativeSupplier` 간선이 12% 프리미엄까지 같은 경로에 붙여 준다.

그 결과:

- 데이터 에이전트가 조인 로직 없이 자연어 질문("What's the best action to minimize disruption impact?")에 ROI 순위로 답할 수 있다.
- `revenueAtRisk > $50M AND timeToImpactDays < 5` 같은 규칙을 **속성 이름으로** 선언할 수 있다.
- 추정치와 실측치를 같은 노드(`MitigationAction`)에 남겨 사후 채점이 가능하다.

## 핵심 요약

1. 비교 짝은 `estimatedCost`($2M) ↔ `revenueAtRisk`($80M), `leadTimeSavedDays`(2일) ↔ `timeToImpactDays`(3일)다.
2. $80\text{M}/2\text{M} = 40\times$, 순편익 $78M, 비용 비중 2.5% → 자동화 임계값($>\$50M$, $<5$일)도 함께 충족.
3. A(2M, 2일 절감, 즉시 가동) 채택 / B(500K, 2주 완충, 리드타임 절감 없음)는 병행 보완 / C(재설계, 리드타임 미정)는 ROI 산정 불가로 이번 사이클 제외.
4. 12% `pricePremiumPercent`는 일회성 2M과 별도로 누적되는 지속 비용 — 결론은 유지되지만 재무 통보 필수.
5. Day 3 실제 2.1M(추정 2M, +5%)로 Cost efficiency $\pm5\%$ 경계 통과 → 추정 모델 보정 루프로 환류.
6. 이 모든 비교가 가능한 이유는 `RiskAssessment --recommends--> MitigationAction --activates--> AlternativeSupplier` 경로가 돈·시간·프리미엄을 하나의 그래프에 모아 두기 때문이다.
