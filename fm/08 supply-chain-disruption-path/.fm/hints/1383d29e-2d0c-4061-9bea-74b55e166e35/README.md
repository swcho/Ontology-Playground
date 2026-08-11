# Day 3 최종 결과 — 무엇이 기록되고, 어떤 지표로 검증되는가

## 질문 / 정답

**Q.** Day 3에 기록된 최종 결과는?

**A.** ChipX Europe 물량 입고로 `MitigationAction.status = "Completed"`, 47개 부품 재고 복구, 7일이 아닌 3일 지연으로 생산 재개, 실제 비용 2.1M 달러(추정 2M 달러), 127M 달러 노출 중 약 100M 달러 매출 보호.

원문(Mitigation Execution & Automation → "Real-world workflow: End-to-end")의 Day 3 블록:

```
Day 3: ChipX Europe shipment received
  ├─ MitigationAction.status = "Completed"
  ├─ Inventory restored for 47 components
  ├─ Production resumes (3-day delay, not 7-day)
  ├─ Actual cost: $2.1M (estimated $2M)
  ├─ Revenue protected: ~$100M of $127M exposure
```

이 5줄은 단순한 상황 종료 보고가 아니라, **"Continuous improvement" 표의 지표를 채점하기 위한 실측치(actuals)** 다. 각 줄이 어떤 지표의 입력인지 매핑하면 다음과 같다.

| Day 3 기록 | 대응 지표 | 목표 |
|---|---|---|
| `status = "Completed"` | Time to mitigation (사이클 종료 확정) | < 2 hours (착수) |
| 47개 부품 재고 복구 | Trace accuracy | > 95% |
| 3일 지연(7일 아님) | leadTimeSavedDays 실측 / `estimatedDurationDays` 보정 | — |
| 실제 2.1M vs 추정 2M | **Cost efficiency** | ±5% |
| 100M / 127M 보호 | **Revenue protection rate** | > 80% |
| 127M 추정 vs 실제 노출 | **Impact estimate accuracy** | ±10% |

---

## 1. Cost efficiency (±5%) — 경계선 통과

지표 정의는 "Actual cost vs. estimated cost of actions"이므로 상대 편차로 계산한다.

$$
\text{Cost deviation} = \frac{C_{actual} - C_{est}}{C_{est}} = \frac{2.1 - 2.0}{2.0} = 0.05 = +5.0\%
$$

허용 구간은 $|{\cdot}| \le 5\%$, 즉 절대 금액으로는

$$
C_{actual} \in [\,2.0 \times 0.95,\; 2.0 \times 1.05\,] = [\,1.9\text{M},\; 2.1\text{M}\,]
$$

2.1M은 **상한과 정확히 일치**한다. 즉 통과이지만 여유가 0인 경계 통과(borderline pass)이며, 100K 달러만 더 들었다면(2.2M → +10%) 지표 위반이다. 실무적으로는 "통과했지만 추정 모델이 초과 방향으로 편향(bias)되어 있다"는 신호로 읽어야 한다.

참고로 ChipX Europe의 `pricePremiumPercent = 12%`가 이미 추정 2M에 반영되어 있었다는 점을 감안하면, 초과분 0.1M은 프리미엄 자체가 아니라 **긴급 물류/48시간 배송 등 추정에 없던 항목**에서 발생했다고 해석하는 편이 자연스럽다. Learn 단계에서 이 항목을 별도 비용 요소로 승격시키는 것이 다음 사이클의 정확도를 올린다.

---

## 2. Revenue protection rate (>80%) — **목표 미달**

$$
\text{Protection rate} = \frac{R_{protected}}{R_{atRisk}} = \frac{100}{127} = 0.7874 = 78.7\%
$$

목표는 $> 80\%$ 이므로 **약 1.3%p 미달**이다. 목표를 채우기 위해 필요했던 보호 금액은

$$
R_{required} = 0.80 \times 127 = 101.6\text{M} \quad\Rightarrow\quad \Delta = 101.6 - 100 = 1.6\text{M}
$$

즉 **1.6M 달러어치 매출을 더 지켰어야** 지표를 만족했다. 미보호 노출은

$$
R_{unprotected} = 127 - 100 = 27\text{M} \quad (21.3\%)
$$

이 결과가 중요한 이유는, **비용 지표는 통과했는데 성과 지표는 실패**했다는 조합 때문이다. 투자 효율만 보면

$$
\text{ROI} = \frac{100\text{M}}{2.1\text{M}} \approx 47.6\times
$$

로 압도적이다. 47배 레버리지를 가진 액션이라면 **비용을 더 써서라도 보호율을 올리는 것이 합리적**이라는 뜻이다. 예컨대 2차 백업인 `SemiCorp Japan`(capacity 30K/month, +18%)을 병렬 활성화해 추가 비용 0.5M을 지출하고 3M을 더 지켰다면, 비용 편차는 $(2.6-2.0)/2.0 = +30\%$ 로 Cost efficiency는 위반하지만 보호율은 $103/127 = 81.1\%$ 로 목표를 넘긴다.

여기서 두 지표가 **구조적으로 상충(trade-off)** 함이 드러난다. Day 3 기록은 "±5% 비용 규율을 지키느라 80% 보호선을 놓친" 사례이고, 이는 임계값 자체를 재설계해야 한다는 피드백이다(예: `revenueAtRisk > 100M` 인 Critical 건에는 Cost efficiency 허용 범위를 ±5% → ±25%로 완화).

---

## 3. Impact estimate accuracy (±10%) — 해석에 주의

정의는 "Estimated vs. actual revenue at risk"다. 추정치 $E = 127\text{M}$(Phase 3에서 계산)이므로 허용 구간은

$$
A \in [\,127 \times 0.9,\; 127 \times 1.1\,] = [\,114.3\text{M},\; 139.7\text{M}\,]
$$

문제는 **Day 3에 남은 유일한 "실제" 매출 숫자가 미보호 노출 27M** 이라는 점이다. 이를 그대로 $A$ 로 쓰면

$$
\frac{|27 - 127|}{127} = 78.7\% \;\gg\; 10\%
$$

로 처참한 오차가 나오지만, 이는 **지표를 잘못 적용한 것**이다. 27M은 "완화 조치가 실행된 뒤 남은 손실(post-mitigation)"이고, 127M은 "조치가 없었을 때의 노출(counterfactual, no-mitigation baseline)"이다. 서로 다른 세계의 값을 비교하면 완화가 성공할수록 추정 정확도가 나빠지는 역설이 생긴다.

따라서 Impact estimate accuracy는 반드시 **동일 전제의 반사실 기준선**과 비교해야 한다.

$$
A_{counterfactual} = R_{protected} + R_{unprotected} = 100 + 27 = 127\text{M}
$$

$$
\frac{|127 - 127|}{127} = 0\% \;\le\; 10\% \quad \checkmark
$$

즉 **보호 + 미보호의 합이 추정 노출과 일치한다는 회계 항등식**이 성립할 때만 추정이 검증되며, Day 3 기록은 이 항등식을 정확히 만족한다(≈100M은 근사값이므로 실무에서는 반올림 오차 범위 내 일치로 본다).

또 하나의 함정: 기간 스케일링으로 검증하려는 시도다. `estimatedDurationDays = 7`, 실제 지연 3일이므로 노출이 기간에 선형이라 가정하면

$$
A_{scaled} = 127 \times \frac{3}{7} \approx 54.4\text{M}
$$

이고 실제 손실 27M과 비교하면 $|27 - 54.4|/54.4 \approx 50\%$ 오차다. 이 불일치는 **노출이 기간에 선형이 아님**을 뜻한다. Phase 3의 원식

$$
\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}
$$

은 `daysOfSupplyOnHand`(재고 소진까지의 일수)를 쓰지 지연 일수를 쓰지 않는다. 즉 127M은 "재고가 3일 뒤 소진되면 노출되는 매출 총량"이고, 지연 일수를 곱해 안분할 대상이 아니다. Learn 단계가 잡아내야 하는 모델링 이슈가 바로 이것이다.

### 부수 지표: 리드타임과 트레이스 정확도

- **leadTimeSavedDays**: 추정 2일, 실제로는 7일 → 3일이므로 4일 단축.
  $$\frac{4 - 2}{2} = +100\%$$
  즉 액션 효과를 **절반으로 과소평가**했다. 비용은 과소추정(+5%), 효과도 과소추정(+100%) → 다음 추정에서 ROI가 상향 조정되어야 한다.
- **지연 감소율**: $(7-3)/7 = 57.1\%$ 단축.
- **Trace accuracy (>95%)**: Phase 2에서 트레이싱된 47개 부품이 Day 3에 정확히 47개 복구되었으므로, 식별 집합과 실제 영향 집합이 일치 $\left(\frac{47}{47} = 100\%\right)$ → 목표 충족. 만약 복구 후 48번째 부품이 튀어나왔다면 $47/48 = 97.9\%$ 였을 것이고, 45개였다면 오탐(false positive)이 2개 있었다는 뜻이 된다.
- **Detection speed (<1h)**: 10:30 지진 → 10:47 RiskAssessment 생성 = 17분 ✔
- **Time to mitigation (<2h)**: 10:47 평가 → 10:48 MitigationAction 생성 = 1분 ✔

종합하면 6개 지표 중 **5개 통과(1개는 경계선), Revenue protection rate만 미달**이다.

---

## 4. `MitigationAction.status` 전이

`status`는 enum `Proposed / Approved / In Progress / Completed / Cancelled` 이며, 워크플로우에서 다음 경로를 밟는다.

```
[Day 1 10:48]  Proposed ──▶ Approved
               (auto-created; AlternativeSupplier.qualificationStatus="Approved"
                + Phase 5 규칙 충족으로 자동 승인/PO 발행)
                     │
[Day 1 11:30]        ▼
               In Progress
               (PO 처리 중, ChipX Europe 48시간 출하 확약,
                생산 영향 7일 → 3일로 재계산)
                     │
[Day 2-4] 4시간 주기 모니터링 (slip 감시)
                     │
[Day 3]              ▼
               Completed   ◀── 입고 확인이 트리거
               (47개 부품 재고 복구, actualCost 2.1M 확정)

                (대안 경로) ──▶ Cancelled
                 대체 공급사 지연/무효화 시 종료하고 contingency 재추천
```

핵심 포인트:

1. **자동 승인 조건** — Phase 5의 규칙 `IF RiskAssessment.revenueAtRisk > $50M AND RiskAssessment.timeToImpactDays < 5`. 실제 값 127M > 50M, 3일 < 5일이므로 두 조건 모두 참 → 사람의 승인 대기 없이 PO 생성·부서 통보·Activator 알림이 발화한다. `Proposed` 단계가 사실상 즉시 통과되는 이유다.
2. **`In Progress`는 감시 대상 상태** — Day 1 마지막 줄 "Start monitoring `MitigationAction.status`"와 Day 2-4의 4시간 주기 루프가 이 상태에 붙어 있다. 이 구간에서 `leadTimeSavedDays`가 슬립하면 알림이 뜨고 contingency 액션이 추천된다.
3. **`Completed`는 물리적 사건에 근거해야 한다** — 상태를 바꾸는 트리거는 "PO 발행"이나 "공급사 확약"이 아니라 **실제 입고(shipment received)** 다. 확약만으로 완료 처리하면 Day 3의 실측치(actualCost, 복구 부품 수)를 확보할 수 없고, Learn 단계에 넣을 데이터가 사라진다.
4. **터미널 상태에서 지표가 확정된다** — `Completed` 시점에 비로소 estimated ↔ actual 쌍이 완성되어 Cost efficiency / Impact estimate accuracy를 채점할 수 있다. 그래서 상태 전이는 곧 **측정 게이트**다.
5. **`ProductLine.productionStatus`도 함께 전이한다** — 노출 시 `At Risk`/`Halted` → Day 3 생산 재개로 `Active`. `MitigationAction`의 완료와 제품 라인 상태 복귀는 짝을 이룬다.

---

## 5. Learn 단계 피드백 — 어떤 값이 다음 추정에 반영되는가

Risk Propagation Model의 6단계 사이클은 **Detect → Trace → Quantify → Recommend → Act → Learn**이고, Learn은 "Track which actions actually worked and their real vs. estimated impact"로 정의된다. Day 3 기록은 이 Learn 단계의 **유일한 입력 데이터**다.

| Day 3 실측치 | 갱신되는 온톨로지 값 | 다음 사이클에 미치는 영향 |
|---|---|---|
| actual cost **2.1M** (est 2.0M) | `MitigationAction.estimatedCost` 산정식에 ×1.05 보정 계수, `AlternativeSupplier.pricePremiumPercent`(12%) 검증 | 동일 유형("Activate Alternative Supplier") 액션의 추정 비용을 5% 상향 → Cost efficiency 경계선 탈출 |
| 지연 **3일**(예상 7일) | `DisruptionEvent.estimatedDurationDays` 사전분포, `MitigationAction.leadTimeSavedDays`(2 → 실측 4) | 리드타임 절감 효과를 2배로 재평가 → Recommend 단계의 ROI 스코어링에서 이 액션 순위 상승 |
| **47개** 부품 전량 복구 | `Supplier → supplies → Component` 트레이싱 경로의 신뢰도, Trace accuracy 100% 기록 | `RiskAssessment.confidenceLevel`을 Medium → High로 올릴 근거 |
| ChipX Europe **48시간 출하 이행** | `AlternativeSupplier.reliabilityScore` 상향, `qualificationStatus = Approved` 유지 근거, `capacityAvailable`(50K/month) 실증 | "어느 대체 공급사가 실제로 성능을 내는가"에 대한 학습 — 다음 사고 시 1순위 후보로 고정 |
| 보호율 **78.7%**(목표 80% 미달) | 플레이북/임계값 자체 수정: 2차 공급사 병렬 활성화 기준, `Component.daysOfSupplyOnHand` 안전재고 목표 상향, Cost efficiency 허용폭의 조건부 완화 | 구조적 개선 — 같은 시나리오가 반복되면 다시 80%를 놓치므로 파라미터가 아니라 규칙을 바꿔야 함 |
| 미보호 노출 **27M** | `revenue_at_risk` 산식 검증(선형 기간 안분이 부적절함 확인), 어느 제품 라인이 27M을 냈는지 역추적 | 회복탄력성이 낮은 제품 라인 식별 → 사전 예방(pre-qualification) 대상 선정 |

원문의 결론 문장이 이 흐름을 요약한다: *"Each disruption event becomes a training opportunity. Your agents learn which alternative suppliers actually perform, which lead times hold up, and which product lines are most resilient."*

### 한 줄 정리

Day 3의 다섯 줄은 **완료 보고가 아니라 채점표이자 학습 데이터**다. `status = "Completed"`가 estimated↔actual 쌍을 확정시키고, 비용은 +5%로 겨우 통과, 추정 노출 127M은 (100+27) 항등식으로 검증되며, 보호율 78.7%는 80% 목표를 1.3%p 놓친다 — 그리고 이 미달분이 다음 사이클의 임계값과 안전재고 정책을 바꾸는 피드백이 된다.
