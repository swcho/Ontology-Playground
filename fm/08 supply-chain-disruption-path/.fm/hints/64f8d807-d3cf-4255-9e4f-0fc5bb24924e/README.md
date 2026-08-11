# 이 온톨로지가 궁극적으로 달성하는 비즈니스 성과

## 질문과 정답

**Q.** 이 온톨로지가 궁극적으로 달성하는 비즈니스 성과는?

**A.** 교란 대응 시간을 **며칠에서 몇 시간(또는 분) 단위로 단축**해 매출 손실을 줄이는 것이다. 예시 워크플로에서는 20분 만에 조치 추천, 25분 내 실행이 이뤄지고 127M 달러 노출 중 약 100M 달러를 보호했다.

원문 요약 항목의 마지막 줄이 이 성과를 한 문장으로 못 박는다.

> ✅ **Measurable outcomes** — reduce disruption impact from days to hours

즉 이 온톨로지의 최종 산출물은 "잘 정리된 엔티티 7개, 속성 40개, 관계 7개"가 아니다. 그것들은 수단이고, **성과는 시간이며, 그 시간이 곧 돈**이다.

---

## 1. '며칠 → 분' 단축은 어디에서 오는가

### 1.1 온톨로지 없는 세계: 수작업 스프레드시트 분석

원문 Scenario Overview의 대비가 핵심이다.

> **Without an ontology**, this analysis takes days and manual spreadsheets.
> **With an ontology**, an AI agent can: (1) 몇 분 내 영향 부품 전수 식별 … (5) 자동 알림·구매 워크플로 트리거

온톨로지가 없을 때 실제로 벌어지는 일을 단계별로 풀면 이렇다.

| 필요한 작업 | 온톨로지 없을 때 | 소요 |
|---|---|---|
| 대만 소재 공급사 목록 뽑기 | 구매팀에 메일/문의, 벤더 마스터 엑셀 필터 | 수 시간 |
| 그 공급사들이 대는 부품 찾기 | ERP 품목-벤더 테이블 추출 후 VLOOKUP | 반나절 |
| 그 부품을 쓰는 제품 라인 찾기 | BOM 전개를 엑셀에서 수동 조인 | 하루 이상 |
| 제품 라인별 매출 노출 계산 | 재무팀에서 매출 데이터 받아 다시 조인 | 하루 |
| 대체 공급사 자격/캐파 확인 | 담당자 개별 확인, 최신 승인 상태 불명확 | 수 시간~며칠 |
| 조치안 비교(ROI) | 파워포인트 회의체 상정 → 승인 대기 | 며칠 |

여기서 병목은 데이터가 **없는** 것이 아니다. 데이터는 ERP, PLM, 재무, 구매 시스템에 다 있다. 병목은 **그 데이터 사이의 연결이 사람 머릿속과 각자의 엑셀 파일에만 있다**는 점이다. 그래서 매번 사람이 조인 키를 찾아 붙이고, 붙일 때마다 새로 검증해야 한다. 이 '매번 다시 붙이기'가 며칠을 잡아먹는다.

### 1.2 온톨로지가 있는 세계: 관계 탐색 자동화

온톨로지는 그 조인을 **한 번, 스키마 수준에서, 이름 붙여서** 고정해 둔다. Risk Propagation Model의 7개 관계가 그것이다.

```
DisruptionEvent --affects--> Supplier --supplies--> Component --usedIn--> ProductLine
                                  ^                                           |
                                  |                                           v
       AlternativeSupplier --canReplace--         DisruptionEvent --triggers--> RiskAssessment
                 ^                                                              |
                 |                                                              v
                 --activates-- MitigationAction <--recommends-------------------
```

이렇게 인코딩되면 '며칠 걸리던 조인'이 **그래프 탐색 한 번**으로 바뀐다. Mitigation Execution 문서의 Phase 2가 정확히 그 장면이다.

```
"이 3개 공급사가 대는 부품 전부"  →  Supplier → supplies → Component      → 47개 부품
"그 47개 부품을 쓰는 제품 라인"     →  Component → usedIn → ProductLine     → 12개 제품 라인
```

사람이 하면 이틀짜리 BOM 역전개가, 관계가 선언되어 있으면 **에이전트가 홉 두 번 따라가는 질의**가 된다. 이것이 '며칠 → 분' 단축의 1차 원천이다.

### 1.3 실제 타임라인: 분 단위 페이즈

원문은 이 단축을 4개 페이즈 + 실측 시계로 두 번 보여준다.

**설계상의 페이즈 (minute 기준)**

| 시각 | 페이즈 | 하는 일 | 산출 |
|---|---|---|---|
| minute 0 | Detection | 외부 신호 수신, `Supplier.country` × `DisruptionEvent.region` × `type` 매칭 | 핵심 공급사 3곳 |
| minute 5 | Trace impact | `supplies` → `usedIn` 2홉 전개 | 부품 47개, 제품 라인 12개 |
| minute 15 | Quantify impact | 매출 노출·긴급도 계산 및 집계 | $127M, 3일, 고객 45만+ |
| minute 20 | **Recommend actions** | 승인된 대체 공급사 필터 + 스코어링 | Top 3 조치안 (ROI 포함) |
| minute 25 | **Execute** | 규칙 충족 시 PO 발행·스케줄 갱신·알림·Activator | 자동 실행 |

**실제 워크플로 시계 (Day 1)**

| 시각 | 이벤트 |
|---|---|
| 10:30 | 대만 규모 6.8 지진 발생 |
| 10:45 | `DisruptionEvent` 생성 (type=Natural Disaster, severity=Critical, region=Taiwan, estimatedDurationDays=7) |
| 10:46 | Data Agent 영향 전파 추적 → 공급사 3, 부품 47, 제품 라인 12, **$127M 위험, 생산 중단까지 3일** |
| 10:47 | `RiskAssessment` 생성, ROI 순 조치 추천 |
| 10:48 | `MitigationAction` 자동 생성 → ChipX Europe에 PO, 안전재고 발주, 구매·운영·재무 알림 |
| 10:50 | Activator 발동 → 대시보드, 에스컬레이션, 구매팀 수신 확인 |
| 11:30 | `MitigationAction.status = "In Progress"`, ChipX Europe 48시간 출하 확약, **생산 영향 7일 → 3일** |

지진 발생부터 **조치 착수까지 18분**, 실행 확정까지 **1시간**이다. 여기서 정답의 "20분 만에 조치 추천, 25분 내 실행"은 설계상의 페이즈 기준 수치이고, 워크플로 예시는 그것이 벽시계로도 성립함을 보여준다.

---

## 2. 시간 단축이 곧 금액으로 환산되는 경로

이 부분이 카드의 핵심이다. "빠르다"는 것만으로는 성과가 아니다. **빨라진 시간이 왜 돈이 되는지**는 다음 인과 사슬로 설명된다.

```
[1] 재고 소진까지 남은 시간이 마감 시한이다
    Component.daysOfSupplyOnHand = 3
    → RiskAssessment.timeToImpactDays = 3
    → "3일 안에 대체 공급이 흐르기 시작하지 않으면 라인이 멈춘다"

[2] 대응이 며칠 걸리면 이 마감을 놓친다
    분석 2일 + 회의 승인 1~2일 + PO 발행
    → 대체 물량 발주 시점이 이미 재고 소진 이후
    → 교란 기간 전체(estimatedDurationDays = 7)가 그대로 생산 중단으로 전이

[3] 대응이 분 단위면 마감 전에 조치가 들어간다
    10:48 PO 발행 → 11:30 ChipX Europe 48시간 출하 확약
    → Day 3에 입고 (재고 소진 시점과 맞물림)
    → 47개 부품 재고 복원, 생산 재개

[4] 생산 중단 기간이 줄어든다
    "Production impact reduced from 7 days → 3 days"
    = 중단 4일치를 되찾음

[5] 되찾은 생산일수가 보호된 매출이다
    노출: $127M
    보호: 약 $100M  (Revenue protected: ~$100M of $127M exposure)
    비용: 실제 $2.1M (추정 $2M)
```

정리하면 **시간 → 금액 환산의 축은 "생산 중단 일수"**다.

- 대응 시간을 줄이면 → 재고가 다 떨어지기 전에 대체 공급이 파이프라인에 들어가고
- 대체 공급이 재고 소진 시점에 맞춰 도착하면 → 중단 일수가 7일에서 3일로 줄고
- 중단 일수가 줄면 → 그 기간 출하하지 못했을 제품 매출이 보호된다

`estimatedDurationDays`(교란이 얼마나 지속되는가)와 `daysOfSupplyOnHand`(우리가 얼마나 버티는가)의 차이가 곧 노출 구간이고, 대응 속도가 그 구간을 파고들어 갉아먹는 유일한 레버다.

### 2.1 ROI가 자명해지는 이유

Phase 4 추천 엔진이 제시하는 숫자를 나란히 놓으면 의사결정이 회의체를 거칠 필요조차 없어진다.

| 항목 | 금액 |
|---|---|
| 방치 시 매출 노출 | $127M (개별 assessment 예시로는 $80M) |
| 조치 A: ChipX Europe 활성화 | $2M (실제 $2.1M), 2일 단축 |
| 조치 B: 안전재고 확대 | $500K, 2주 커버 |
| 실제 보호된 매출 | 약 $100M |

원문의 문장이 이 비교를 그대로 요약한다.

> **Recommend** — "Activate pre-qualified alternatives that save 2 days and cost $2M vs. $80M loss"

$2M을 써서 $100M을 지킨다 — 약 **50배 ROI**. 이 계산이 20분 안에 나오는지, 3일 뒤에 나오는지가 성과의 전부다. 3일 뒤에 나온 똑같이 정확한 계산은 이미 무가치하다(재고가 이미 소진되었으므로).

### 2.2 예시 수치를 읽을 때의 주의점

원문 Phase 3의 계산식은 다음과 같다.

```
revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand
urgency         = 100 - (daysOfSupplyOnHand * 10)
```

한편 cascade 예시는 연매출 $50M + $30M 두 라인에 대해 `revenueAtRisk = $80M`으로 적어 두었다. 이는 식대로 계산한 값(약 $657K)과 맞지 않는다. **원문의 금액들은 교육용 예시 수치이며 식과 정합적이지 않다.** 카드가 묻는 것은 계산식의 정확성이 아니라 "노출 $127M 중 $100M 보호"라는 **성과의 형태**이므로, 숫자는 그 형태를 기억하는 앵커로 쓰면 된다. 실무에서는 노출액을 "중단 일수 × 일평균 매출(또는 마진) × 영향 라인"으로 다시 정의하게 된다.

---

## 3. 이 성과를 지탱하는 6개 자동화 단계와 6개 지표

성과(시간 단축 → 매출 보호)는 6단계 자동화 루프가 만들고, 6개 지표가 각 단계가 실제로 작동하는지를 감시한다. **둘은 거의 1:1로 짝지어진다.**

### 3.1 6개 자동화 단계 (Why this structure enables automation)

| # | 단계 | 무엇을 하는가 | 쓰이는 온톨로지 요소 |
|---|---|---|---|
| 1 | **Detect** | 특정 공급사·지역 모니터링, `DisruptionEvent` 생성 | `DisruptionEvent.type/severity/region`, `Supplier.country` |
| 2 | **Trace** | "ChipX Corp에 문제 생기면 영향받는 제품 라인 14개를 자동 추적" | `supplies`, `usedIn` 관계 |
| 3 | **Quantify** | 총 매출 노출($80M)과 영향 도달 시간(3일) 산출 | `annualRevenue`, `daysOfSupplyOnHand`, `revenueAtRisk`, `timeToImpactDays` |
| 4 | **Recommend** | 2일 절감·$2M 비용 대안을 $80M 손실과 비교해 제시 | `AlternativeSupplier.qualificationStatus/capacityAvailable/pricePremiumPercent`, `reliabilityScore`, `leadTimeSavedDays` |
| 5 | **Act** | 구매 알림, 생산 스케줄 갱신, 이해관계자 통지 | `MitigationAction.type/status/estimatedCost`, Activator 규칙 |
| 6 | **Learn** | 어떤 조치가 실제로 통했는지, 추정 대비 실적 추적 | `MitigationAction.status`, `assessedDate`, 실제 vs 추정 비교 |

### 3.2 6개 지표 (Continuous improvement)

| 지표 | 계산 | 목표 |
|---|---|---|
| Detection speed | 교란 발생 → `RiskAssessment` 생성까지 시간 | < 1시간 |
| Trace accuracy | 실제 영향 부품 중 식별된 비율 | > 95% |
| Impact estimate accuracy | 추정 vs 실제 매출 노출 | ±10% |
| Time to mitigation | assessment → `MitigationAction` 실행까지 시간 | < 2시간 |
| Cost efficiency | 조치 실제 비용 vs 추정 비용 | ±5% |
| Revenue protection rate | 위험 매출 중 조치로 보호된 비율 | > 80% |

### 3.3 단계 ↔ 지표 매핑

```
Detect     ──▶ Detection speed (< 1h)          ── 얼마나 빨리 알아채나
Trace      ──▶ Trace accuracy (> 95%)          ── 빠트린 영향이 없나
Quantify   ──▶ Impact estimate accuracy (±10%) ── 금액 추정이 신뢰할 만한가
Recommend ─┐
Act       ─┴▶ Time to mitigation (< 2h)        ── 판단이 실행까지 얼마나 걸리나
Act        ──▶ Cost efficiency (±5%)           ── 조치 비용이 예상대로인가
Learn      ──▶ Revenue protection rate (> 80%) ── 결국 얼마를 지켰나 (최종 성과 지표)
```

읽는 법이 중요하다.

- **앞 4개 지표는 "속도와 정확성"의 선행지표**다. Detection speed와 Time to mitigation은 시간을, Trace accuracy와 Impact estimate accuracy는 그 빠른 판단이 틀리지 않았음을 보증한다. 빠르지만 틀리면 잘못된 공급사에 PO를 날리므로, 속도 지표와 정확성 지표는 반드시 함께 봐야 한다.
- **Cost efficiency는 비용 측 통제**다. $2M이라던 조치가 실제로 $10M이었다면 ROI 논리가 무너진다. 예시에서는 추정 $2M / 실제 $2.1M = 5% 이내로 목표를 만족한다.
- **Revenue protection rate가 유일한 후행·최종 지표**다. 앞 5개가 다 좋아도 이것이 낮으면 성과가 없는 것이다.

실제 예시값을 지표에 대보면:

| 지표 | 예시 실측 | 목표 | 판정 |
|---|---|---|---|
| Detection speed | 10:30 → 10:47 (17분) | < 1h | 충족 |
| Time to mitigation | 10:47 → 10:48 (1분), 실행 확정 11:30 | < 2h | 충족 |
| Cost efficiency | $2.1M vs $2M (+5%) | ±5% | 경계선 충족 |
| Revenue protection rate | $100M / $127M ≈ 78.7% | > 80% | **미달** |

마지막 줄이 시사하는 바가 있다. 분 단위로 대응해도 보호율은 79%에 그쳤다 — 즉 **속도만으로 100%를 지킬 수는 없다.** 남은 21%는 재고 자체(`daysOfSupplyOnHand`), 단일 소싱 구조(`singleSourced=true`), 사전 자격심사된 대체 공급사 수 같은 **평시 구조 개선**으로만 줄어든다. 그래서 Fabric IQ 연계 예시에서 에이전트가 평상시에도 이렇게 답한다.

> "You have 3 critical single-source suppliers. If any are disrupted, you lose ~$180M in 4-9 days. We recommend pre-qualifying 8 alternative suppliers."

즉 이 온톨로지의 성과는 **사후 대응 속도(며칠 → 분)** + **사전 취약점 가시화(단일 소싱 노출 상시 조회)** 두 축으로 완성된다. 6단계 루프의 마지막 Learn이 이 두 축을 잇는 고리다.

---

## 4. 온톨로지가 없으면 왜 같은 속도가 안 나오는가

"데이터 웨어하우스에 SQL 잘 짜면 되지 않나?"에 대한 답이다. 두 가지 결정적 결핍이 있다.

### 4.1 관계가 인코딩되어 있지 않다 → 전파 추적이 매번 새 작업이 된다

온톨로지의 7개 관계는 **카디널리티까지 선언된 1급 시민**이다.

| 관계 | 카디널리티 | 왜 필요한가 |
|---|---|---|
| Supplier → Component | 1:N | 공급사 하나가 여러 부품을 댄다 |
| Component → ProductLine | M:N | 부품이 재사용되고, 제품이 부품을 공유한다 |
| Disruption → Supplier | M:N | 재해 하나가 여러 공급사를 때린다 |
| Disruption → Assessment | 1:N | 교란마다 라인별 assessment가 생긴다 |
| Assessment → Action | 1:N | assessment마다 조치안이 여러 개 |
| Action → Alternative | M:N | 조치 하나가 여러 백업을 동시 가동 |
| Alternative → Supplier | M:1 | 한 공급사에 승인된 백업이 여럿 |

이것이 없으면 무슨 일이 생기는가.

- **다홉 전개를 사람이 매번 조립해야 한다.** `공급사 3 → 부품 47 → 제품 라인 12`는 두 홉이다. 관계 이름(`supplies`, `usedIn`)이 없으면 매번 "어느 테이블의 어느 컬럼이 조인 키인가"부터 다시 찾는다. M:N 구간에서는 중간 테이블 존재조차 조직 지식에 의존한다.
- **폭발(fan-out)을 놓친다.** 1:N과 M:N을 모르면 "이 부품은 이 제품만 쓰는 줄 알았다" 같은 누락이 발생한다. Trace accuracy > 95% 목표가 깨지고, 3일째에 몰랐던 제품 라인이 멈춘다.
- **역방향 질의가 불가능하다.** `AlternativeSupplier canReplace Supplier`가 선언되어 있어야 "ChipX Corp을 대체할 승인 백업이 있는가?"를 즉답할 수 있다. 없으면 담당자에게 전화해야 하고, 그 전화가 시간을 며칠 단위로 되돌린다.
- **에이전트가 그라운딩할 대상이 없다.** Fabric IQ 데이터 에이전트는 관계를 따라 질의를 구성한다. 자연어 질문("지금 우리 공급망 리스크 노출이 얼마인가?")이 `singleSourced=true → supplies → usedIn → revenueAtRisk 집계`로 번역되는 것은 관계가 스키마에 있기 때문이다. 관계가 없으면 에이전트는 추측하고, 추측은 신뢰할 수 없으므로 사람이 다시 검증한다 — 자동화의 이점이 소멸한다.

### 4.2 enum이 정의되어 있지 않다 → 규칙 자동화가 불가능하다

원문 요약이 이를 명시한다.

> ✅ **Automation-ready** with enum classifications and timestamps

Phase 5의 실행 규칙을 보자.

```
IF RiskAssessment.revenueAtRisk > $50M AND
   RiskAssessment.timeToImpactDays < 5:
THEN
   1. 추천 대체 공급사에 PurchaseOrder 생성
   2. ProductionSchedule 갱신
   3. 구매/운영/재무/CEO 통지
   4. 에스컬레이션 정책이 걸린 Activator 알림 생성
   5. MitigationAction.status 모니터링 개시
```

Phase 4의 필터도 마찬가지다.

```
AlternativeSupplier WHERE qualificationStatus = "Approved"
                      AND capacityAvailable >= demand
                      AND country NOT IN earthquake_region
```

이 규칙들이 성립하려면 값 집합이 **닫혀 있고 표준화되어** 있어야 한다.

| enum 속성 | 허용값 | 자동화에서의 역할 |
|---|---|---|
| `DisruptionEvent.type` | Natural Disaster / Geopolitical / Financial / Logistics / Quality Recall / Pandemic / Cyber Attack | 유형별 대응 플레이북 분기 |
| `DisruptionEvent.severity` | Critical / High / Medium / Low | 에스컬레이션 레벨·대응 타임라인 결정 |
| `Supplier.tier` | Tier 1 / 2 / 3 | 모니터링 우선순위 |
| `Component.criticalityLevel` | Critical / High / Medium / Low | 알림 임계값 |
| `ProductLine.productionStatus` | Active / At Risk / Halted / Discontinued | 상태 전이 트리거 |
| `AlternativeSupplier.qualificationStatus` | Pre-qualified / Approved / Pending Audit / Not Qualified | **자동 PO 발행 가능 여부의 게이트** |
| `MitigationAction.status` | Proposed / Approved / In Progress / Completed / Cancelled | 진행 모니터링·Learn 단계 집계 |
| `Supplier.singleSourced` | boolean | 리스크 증폭기 플래깅 |

enum이 없고 자유 텍스트라면:

- `"Approved"`, `"approved"`, `"승인완료"`, `"OK(2023 audit)"`가 뒤섞인다. `qualificationStatus = "Approved"` 필터가 조용히 후보를 누락하거나, 자격 미달 공급사에 PO를 발행한다. **자동 실행을 켤 수 없다** — 사람이 눈으로 확인해야 하고, 그 확인이 25분을 며칠로 되돌린다.
- severity가 표준화되지 않으면 에스컬레이션 정책을 쓸 수 없다. "Critical이면 임원 통지"라는 규칙 자체가 표현 불가다.
- 의사결정 트리를 학습·검증할 수 없다. Learn 단계에서 "어떤 type의 교란에 어떤 조치가 통했나"를 집계하려면 type과 status가 범주형이어야 한다. 자유 텍스트는 집계가 안 되고, 집계가 안 되면 6개 지표를 측정할 수 없고, 측정할 수 없으면 개선 루프가 멈춘다.

여기에 **타입 체계**도 같은 역할을 한다. `revenueAtRisk`가 decimal이라 비용-편익 산술이 되고, `daysOfSupplyOnHand`가 integer라 임계값 알림이 되고, `assessedDate`가 datetime이라 감사 추적과 추세 분석이 된다. 문자열로 뭉개져 있으면 매번 파싱·정제부터 시작해야 한다.

### 4.3 요약: 세 가지가 함께 있어야 분 단위가 된다

```
관계(7개)   →  전파 추적을 그래프 탐색으로 만든다        (Trace 자동화)
타입/enum   →  판단을 실행 가능한 규칙으로 만든다        (Recommend·Act 자동화)
식별자·타임스탬프 → 감사 추적과 학습을 만든다             (Learn 자동화)
────────────────────────────────────────────────────
        = 며칠 → 분,  그리고 $127M 중 $100M 보호
```

하나라도 빠지면 사슬이 사람 손으로 끊긴다. 그리고 사람 손이 개입하는 지점마다 시간 단위가 분에서 시간으로, 시간에서 일로 올라간다.

---

## 5. 암기 포인트

- **성과의 한 줄**: "reduce disruption impact from **days to hours**" — 대응 시간 단축이 곧 매출 손실 감소.
- **분 단위 페이즈**: 0 감지 / 5 추적 / 15 정량화 / **20 조치 추천** / **25 실행**.
- **금액 앵커**: 노출 **$127M** → 보호 **약 $100M**, 비용 $2.1M, 생산 중단 **7일 → 3일**.
- **환산 축**: 재고 소진(3일) 전에 조치 → 대체 공급 48시간 출하 → 중단 일수 축소 → 매출 보호.
- **6단계**: Detect → Trace → Quantify → Recommend → Act → Learn.
- **6지표**: 감지 <1h / 추적 >95% / 추정 ±10% / 조치 <2h / 비용 ±5% / **보호율 >80%**.
- **없으면 안 되는 것**: 관계 인코딩(전파 추적), enum(규칙 자동화). 둘 중 하나만 없어도 사람 손이 들어가고 속도가 무너진다.
