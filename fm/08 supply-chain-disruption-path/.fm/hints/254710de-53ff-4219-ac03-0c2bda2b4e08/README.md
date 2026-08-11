# Phase 4의 3가지 점수화 기준

> **Q.** Phase 4에서 각 대체안을 점수화하는 3가지 기준은?
>
> **A.** 절약되는 리드타임(`leadTimeSavedDays`), 비용 영향(`pricePremiumPercent`), 신뢰도(`reliabilityScore`)다. 세 축을 종합해 상위 3개 조치를 ROI와 함께 추천한다.

---

## 1. 원문에서의 위치

Mitigation Execution & Automation 문서의 **Phase 4: Recommend actions (minute 20)** 단계다. 입력은 Phase 3에서 나온 RiskAssessment 결과(총 노출액, 임박 시점)이고, 출력은 **ROI가 붙은 상위 3개 조치**다.

```
Recommendation Engine:
  1. Find AlternativeSupplier records where:
     - qualificationStatus="Approved"
     - capacityAvailable >= demand
     - country NOT IN earthquake_region

  2. Score each alternative by:
     - Lead time saved (leadTimeSavedDays)
     - Cost impact (pricePremiumPercent)
     - Reliability (reliabilityScore)

  3. Recommend top 3 actions with ROI
```

여기서 **1단계와 2단계는 성격이 완전히 다르다**. 1단계는 통과/탈락을 가르는 **필터(hard constraint)**, 2단계는 통과한 후보들의 **순위를 매기는 스코어링(soft preference)**이다. 이 구분이 이 카드의 숨은 핵심이다(§5 참조).

---

## 2. 세 기준은 각각 다른 엔터티의 속성이다

가장 자주 틀리는 지점: **세 기준이 한 엔터티에 모여 있지 않다.** 세 개의 서로 다른 엔터티에 흩어져 있고, 관계(relationship)를 타고 조인해야 하나의 점수가 된다.

| 기준 | 속성 | 소속 엔터티 | 타입/범위 | 방향 |
|---|---|---|---|---|
| 절약 리드타임 | `leadTimeSavedDays` | **MitigationAction** | integer (일) | 클수록 좋음 (benefit) |
| 비용 영향 | `pricePremiumPercent` | **AlternativeSupplier** | decimal (%) | 작을수록 좋음 (cost) |
| 신뢰도 | `reliabilityScore` | **Supplier** | decimal (0–100) | 클수록 좋음 (benefit) |

조인 경로는 이렇게 생긴다.

```
RiskAssessment
  └─ recommends →  MitigationAction        ← leadTimeSavedDays, estimatedCost
                     └─ activates (M:N) →  AlternativeSupplier   ← pricePremiumPercent, capacityAvailable, qualificationStatus
                                             └─ canReplace (M:1) →  Supplier          ← reliabilityScore, singleSourced, country
```

### 왜 이렇게 흩어져 있는가

- **`leadTimeSavedDays`가 MitigationAction에 있는 이유**: "며칠을 벌었나"는 공급사의 고유 성질이 아니라 **실행 계획의 결과**다. 같은 ChipX Europe이라도 항공 특송으로 부르면 2일, 해상이면 0일이다. 게다가 `MitigationAction → AlternativeSupplier`는 **M:N**이라, 하나의 조치가 유럽·일본 두 곳을 동시에 가동시킬 수 있다. 이때 절약 일수는 "두 곳을 합친 계획"의 속성이지 개별 공급사의 속성이 아니다.
- **`pricePremiumPercent`가 AlternativeSupplier에 있는 이유**: 프리미엄 단가는 그 백업 업체와 맺은 계약 조건이므로 업체 고유 속성이다.
- **`reliabilityScore`가 Supplier에 있는 이유**: 원본 온톨로지의 40개 속성 목록에서 `reliabilityScore`(0–100)는 **Supplier에만** 정의되어 있다. AlternativeSupplier에는 `qualificationStatus`, `capacityAvailable`, `pricePremiumPercent`만 있다.

> ⚠️ **모델링 주의점 (면접·설계에서 짚으면 좋은 부분)**
> 그래서 "대체안의 신뢰도"를 가져오려면 `canReplace`를 타고 **교체 대상 원 공급사**의 점수를 읽게 되는데, 그건 논리적으로 어긋난다(망가진 업체의 신뢰도로 백업을 평가하는 셈). 실무에서는 둘 중 하나로 푼다.
> 1. AlternativeSupplier에도 `reliabilityScore`를 추가한다.
> 2. 백업 업체를 **Supplier로도 이중 등록**하고, AlternativeSupplier ↔ Supplier 동일성 링크를 둔 뒤 그 Supplier 레코드의 `reliabilityScore`를 읽는다.
>
> 어느 쪽이든 이 카드가 말하는 "3축"은 **엔터티 3개를 횡단하는 조인 결과**라는 사실은 변하지 않는다.

### 이 3개 축이 대표하는 것

세 축은 임의로 고른 게 아니라 조달 의사결정의 세 가지 통화(currency)에 대응한다.

- 리드타임 = **시간** (Phase 3의 `timeToImpactDays`와 직접 경쟁)
- 가격 프리미엄 = **돈** (Finance가 감당해야 할 추가 비용)
- 신뢰도 = **확률/리스크** (그 계획이 실제로 작동할 가능성)

시간·돈·확률을 다 보므로 "빠르지만 못 믿을 업체"나 "싸지만 늦는 업체"가 자동으로 걸러진다. 한 축만 보면 반드시 한쪽으로 망가진 추천이 나온다.

---

## 3. 단위가 다른 세 축을 어떻게 하나의 점수로 만드는가

문제: 축의 **단위**(일 / % / 0–100 점)와 **방향**(클수록 좋음 / 작을수록 좋음)이 모두 다르다. 그대로 더하면 `2일 + 12% + 92점` 같은 무의미한 값이 나온다. 표준 해법은 **정규화 → 방향 정렬 → 가중합** 3단계다.

### 3-1. 정규화 (min–max, 0~1 스케일)

후보 집합 $C$ 안에서 각 축을 0~1로 눌러 넣는다. 클수록 좋은 축(benefit)과 작을수록 좋은 축(cost)의 식이 다르다는 점이 핵심이다.

$$
\tilde{L}_i=\frac{L_i-\min_{j\in C}L_j}{\max_{j\in C}L_j-\min_{j\in C}L_j}
\qquad(L=\texttt{leadTimeSavedDays},\ \text{benefit})
$$

$$
\tilde{P}_i=\frac{\max_{j\in C}P_j-P_i}{\max_{j\in C}P_j-\min_{j\in C}P_j}
\qquad(P=\texttt{pricePremiumPercent},\ \text{cost} \rightarrow \text{역방향})
$$

$$
\tilde{R}_i=\frac{R_i}{100}
\qquad(R=\texttt{reliabilityScore},\ \text{범위가 이미 고정 } 0\text{–}100)
$$

`reliabilityScore`만 min–max가 아니라 **고정 스케일 나눗셈**을 쓴 것에 주의. 정의상 상한이 100으로 못 박혀 있어 후보 집합에 의존할 필요가 없고, 그래야 "후보가 전부 신뢰도 낮음"인 상황에서도 절대적으로 낮은 점수가 유지된다(min–max를 쓰면 최악의 후보도 상대적으로 1.0을 받아버린다).

### 3-2. 가중합

$$
S_i \;=\; w_L\,\tilde{L}_i \;+\; w_P\,\tilde{P}_i \;+\; w_R\,\tilde{R}_i,
\qquad w_L+w_P+w_R=1,\; w_\bullet \ge 0
$$

가중치는 상황 변수로 정한다. Phase 3이 내놓은 `timeToImpactDays`가 작고 `revenueAtRisk`가 크면 시간이 돈보다 압도적으로 중요하므로 $w_L$을 올린다.

$$
w_L \propto \frac{1}{\texttt{timeToImpactDays}},
\qquad
w_P \propto \frac{\text{추가비용}}{\texttt{revenueAtRisk}}
$$

$80M이 걸린 상황에서 $2M의 비용 차이는 2.5%에 불과하니 $w_P$가 작아지는 게 합리적이다. 반대로 노출액이 $3M짜리 사소한 건이면 비용 가중치가 커진다.

---

## 4. ChipX 대체 3사로 실제 계산해 보기

### 4-1. 원문에서 확정된 데이터

Fabric IQ 에이전트 질의 "Which alternatives are approved for ChipX?"의 응답:

| AlternativeSupplier | `capacityAvailable` | `pricePremiumPercent` |
|---|---|---|
| ChipX Europe | 50,000 units/month | +12% |
| SemiCorp Japan | 30,000 units/month | +18% |
| Semiconductor Direct USA | 25,000 units/month | +15% |

그리고 cascade 예시에서 확정된 값: `revenueAtRisk = $80M`, `timeToImpactDays = 3`, MitigationAction "Activate ChipX Europe"의 `estimatedCost = $2M`, `leadTimeSavedDays = 2`.

### 4-2. 계산에 필요한 보강 가정

원문은 Europe의 `leadTimeSavedDays`(=2)만 주고, 나머지 두 곳의 리드타임과 세 곳의 신뢰도는 주지 않는다. 아래는 **계산 예시를 위한 가정값**이다(실제 온톨로지에서는 각 후보 MitigationAction과 Supplier 레코드에서 읽어온다).

| 후보 | $L$ = `leadTimeSavedDays` | $P$ = `pricePremiumPercent` | $R$ = `reliabilityScore` |
|---|---|---|---|
| A. ChipX Europe | 2 *(원문 확정)* | 12 *(원문 확정)* | 92 *(가정)* |
| B. SemiCorp Japan | 3 *(가정)* | 18 *(원문 확정)* | 88 *(가정)* |
| C. Semiconductor Direct USA | 1 *(가정)* | 15 *(원문 확정)* | 80 *(가정)* |

일부러 **단일 축 승자가 서로 다르게** 잡았다. 리드타임 1위는 B, 비용 1위는 A, 신뢰도 1위는 A다. 세 축을 합쳐야만 답이 나오는 구조를 보기 위한 설정이다.

### 4-3. 필터 통과 확인 (Step 1)

월 수요를 25,000 units으로 가정하면:

- `qualificationStatus = "Approved"` → 3사 모두 통과 (원문이 approved 목록으로 돌려준 결과)
- `capacityAvailable >= 25,000` → A(50K) ✅, B(30K) ✅, C(25K) ✅ (경계값 통과)
- `country NOT IN earthquake_region(Taiwan)` → 유럽·일본·미국 모두 통과

> 수요가 40,000이었다면 B(30K)와 C(25K)는 **점수 계산 전에 탈락**하고 A만 남는다. 필터는 이렇게 후보 집합 $C$ 자체를 바꿔버리므로, min–max 정규화의 분모까지 달라진다. **필터를 먼저, 스코어링을 나중에** 하는 순서가 중요한 이유다.

### 4-4. 정규화 (Step 2-a)

$L$: $\min=1,\ \max=3$ → 분모 2

$$
\tilde{L}_A=\frac{2-1}{3-1}=0.50,\quad
\tilde{L}_B=\frac{3-1}{3-1}=1.00,\quad
\tilde{L}_C=\frac{1-1}{3-1}=0.00
$$

$P$: $\min=12,\ \max=18$ → 분모 6, **역방향**

$$
\tilde{P}_A=\frac{18-12}{18-12}=1.00,\quad
\tilde{P}_B=\frac{18-18}{6}=0.00,\quad
\tilde{P}_C=\frac{18-15}{6}=0.50
$$

$R$: 고정 스케일

$$
\tilde{R}_A=\frac{92}{100}=0.92,\quad
\tilde{R}_B=0.88,\quad
\tilde{R}_C=0.80
$$

| 후보 | $\tilde{L}$ | $\tilde{P}$ | $\tilde{R}$ |
|---|---|---|---|
| A. ChipX Europe | 0.50 | **1.00** | **0.92** |
| B. SemiCorp Japan | **1.00** | 0.00 | 0.88 |
| C. Semiconductor USA | 0.00 | 0.50 | 0.80 |

### 4-5. 가중합 (Step 2-b)

`timeToImpactDays = 3`(임박)이지만 `revenueAtRisk = $80M`에 비하면 비용 차이가 작다. 균형 가중치 $w_L=0.5,\ w_P=0.3,\ w_R=0.2$를 쓰면:

$$
S_A = 0.5(0.50)+0.3(1.00)+0.2(0.92)=0.250+0.300+0.184=\mathbf{0.734}
$$

$$
S_B = 0.5(1.00)+0.3(0.00)+0.2(0.88)=0.500+0.000+0.176=\mathbf{0.676}
$$

$$
S_C = 0.5(0.00)+0.3(0.50)+0.2(0.80)=0.000+0.150+0.160=\mathbf{0.310}
$$

**순위: A(0.734) > B(0.676) > C(0.310)** → 원문이 Action A로 ChipX Europe을 추천한 결과와 일치한다. 리드타임 단독 1위는 B였지만, 비용 축에서 최하위(0.00)로 깎여 역전당했다.

### 4-6. 가중치 민감도 — 답이 뒤집히는 지점

지진 피해가 커져 `timeToImpactDays`가 1로 줄었다고 하자. 시간 가중치를 올려 $w_L=0.7,\ w_P=0.15,\ w_R=0.15$:

$$
S_A = 0.7(0.50)+0.15(1.00)+0.15(0.92)=0.350+0.150+0.138=\mathbf{0.638}
$$

$$
S_B = 0.7(1.00)+0.15(0.00)+0.15(0.88)=0.700+0.000+0.132=\mathbf{0.832}
$$

$$
S_C = 0.7(0.00)+0.15(0.50)+0.15(0.80)=0.000+0.075+0.120=\mathbf{0.195}
$$

**순위가 A > B에서 B > A로 뒤집힌다.** 가중치가 바뀌면 추천도 바뀌므로, 온톨로지 기반 추천 엔진은 반드시 **가중치를 데이터로 외부화**하고(하드코딩 금지) 어떤 가중치로 뽑은 순위인지 함께 기록해야 감사(audit)와 사후 학습이 가능하다. 원문의 "Learn — 어떤 조치가 실제로 통했는지 추적"이 바로 이 가중치를 보정하는 루프다.

$A$와 $B$의 역전 임계점을 직접 구할 수도 있다. $w_R=0.2$로 고정하고 $w_L+w_P=0.8$일 때 $S_A=S_B$ 조건은:

$$
w_L(0.50)+w_P(1.00)+0.184 = w_L(1.00)+w_P(0.00)+0.176
$$

$w_P = 0.8-w_L$을 대입하면 $0.5w_L + 0.8 - w_L + 0.184 = w_L + 0.176$, 즉 $1.5w_L = 0.808$, $w_L \approx 0.539$. **$w_L$이 약 0.54를 넘는 순간 SemiCorp Japan이 앞선다.**

### 4-7. Step 3 — ROI까지 붙이기

점수는 순위만 준다. Phase 4의 산출물은 "상위 3개 조치 **+ ROI**"이므로, 정규화 점수를 다시 **금액**으로 되돌려야 경영진 보고가 된다.

프리미엄 비용을 실제 금액으로 환산해 보자. 월 수요 25,000개, 정상 단가 $600/개로 가정하면 기준 조달액은 $15M/월이다.

$$
\text{프리미엄 비용} = 15{,}000{,}000 \times \frac{P}{100}
$$

| 후보 | 프리미엄 비용/월 | + 일회성 특송·전환비 (가정) | ≈ `estimatedCost` |
|---|---|---|---|
| A. ChipX Europe | $1.80M | $0.2M | **$2.0M** *(원문 값과 일치)* |
| B. SemiCorp Japan | $2.70M | $0.2M | $2.9M |
| C. Semiconductor USA | $2.25M | $0.2M | $2.45M |

ROI는 "막아낸 매출 ÷ 들인 비용"이다. 원문의 Action A 기준:

$$
\mathrm{ROI}_A=\frac{\texttt{revenueAtRisk}-\texttt{estimatedCost}}{\texttt{estimatedCost}}
=\frac{\$80\text{M}-\$2\text{M}}{\$2\text{M}}=39\times
$$

원문이 "activate alternatives that save 2 days and cost \$2M vs. \$80M loss"라고 표현한 게 이 계산이다. 신뢰도를 확률로 해석해 **기대값 형태**로 다듬으면 세 축이 한 식에 다 들어온다.

$$
\mathbb{E}[\text{순편익}]_i=\underbrace{\frac{R_i}{100}}_{\text{신뢰도}}\times \texttt{revenueAtRisk}\;+\;\underbrace{L_i \times \frac{\text{일매출}}{1}}_{\text{리드타임 가치}}\;-\;\underbrace{\texttt{estimatedCost}_i}_{\text{비용}}
$$

노출된 두 제품라인($50M + $30M 연매출)의 일매출은 $80\text{M}/365 \approx \$0.219\text{M}$/일이므로:

| 후보 | 기대 보호 매출 | 리드타임 가치 | 비용 | 기대 순편익 |
|---|---|---|---|---|
| A | $0.92 \times 80 = 73.6$M | $2 \times 0.219 = 0.44$M | −$2.00M | **≈ $72.0M** |
| B | $0.88 \times 80 = 70.4$M | $3 \times 0.219 = 0.66$M | −$2.90M | ≈ $68.2M |
| C | $0.80 \times 80 = 64.0$M | $1 \times 0.219 = 0.22$M | −$2.45M | ≈ $61.8M |

가중합(§4-5)과 같은 순위 **A > B > C**가 나오면서, 이번에는 결과가 임의의 $w$가 아니라 **금액**으로 표현된다. 가중치를 손으로 정하는 대신 모든 축을 달러로 환산하는 이 방식을 dollarized scoring이라 부르며, 축 간 교환비를 추정할 수 있을 때 가중합보다 방어하기 쉽다. 반대로 "안전재고 증설"처럼 성격이 다른 조치(원문 Action B: $500K로 2주 커버)나 "부품 재설계"(Action C: 리드타임 미상)와 나란히 비교할 때는, 리드타임이 결측이라 정규화가 불가능하므로 **미지값 처리 규칙**(보수적으로 최악값 대입 또는 별도 "정보 부족" 버킷)이 필요하다.

---

## 5. 필터(hard constraint) vs 스코어링(soft preference)

Phase 4를 외울 때 "3가지 기준"만 기억하면 절반만 아는 것이다. 그 앞단에 **3가지 필터**가 있고, 둘의 역할이 다르다.

| | 필터 (Step 1) | 스코어링 (Step 2) |
|---|---|---|
| 성격 | hard constraint, 절대 조건 | soft preference, 상대 비교 |
| 조건 | `qualificationStatus="Approved"`, `capacityAvailable >= demand`, `country NOT IN 재해지역` | `leadTimeSavedDays`, `pricePremiumPercent`, `reliabilityScore` |
| 결과 | 이진 (통과 / 탈락) | 연속값 (0~1 점수 → 순위) |
| 다른 축으로 보상 가능? | **불가능.** 미승인 업체는 아무리 싸고 빨라도 후보가 될 수 없다 | **가능.** 비싸도 충분히 빠르면 이길 수 있다 (§4-5의 A vs B) |
| 온톨로지 대응 | enum·boolean·정수 임계값 → 결정 트리, 자격 검증 | decimal → 비용·편익 계산 |

### 왜 굳이 분리하는가

1. **범주 오류 방지.** 미승인 업체를 "신뢰도 20점"으로 스코어링에 섞으면, 가격만 충분히 싸면 승인 없이도 1위로 올라올 수 있다. 규제·품질·계약상 통과 불가한 조건은 점수로 깎을 대상이 아니라 **아예 제거할 대상**이다. 감사·컴플라이언스에서 "왜 미승인 업체에 PO를 냈나"라는 질문을 원천 차단한다.
2. **정규화 왜곡 제거.** min–max 정규화는 후보 집합에 의존한다. 어차피 탈락할 극단값(예: +80% 프리미엄 업체)이 집합에 남아 있으면 분모를 부풀려 생존 후보들의 점수 차이를 뭉개버린다. 필터를 먼저 돌려야 스케일이 의미를 갖는다(§4-3 참조).
3. **계산량 절감.** 원문 규모(47개 부품 × 12개 제품라인)에서 조합 폭발을 막는다. 값싼 enum/정수 비교로 후보를 줄인 뒤, 비싼 조인·환산은 살아남은 소수에만 적용한다.
4. **설명 가능성.** 실패 이유를 사람 말로 돌려줄 수 있다. "SemiCorp Japan은 capacity 30K < 수요 40K로 탈락"은 명확한 근거이고, "점수가 0.31이라 탈락"은 근거가 아니다.

### 온톨로지 속성 타입이 이 구분을 그대로 반영한다

원문의 property type 표를 다시 보면 설계 의도가 드러난다.

- `enum`(qualificationStatus, severity, tier) → "Classification, **decision trees**" = 필터용
- `boolean`(singleSourced) → "**Risk flagging**" = 필터/플래그용
- `integer`(capacityAvailable, daysOfSupplyOnHand) → "**Threshold-based alerts**" = 임계값 필터용
- `decimal`(pricePremiumPercent, reliabilityScore, revenueAtRisk) → "**Cost-benefit calculations**" = 스코어링용

즉 **속성 타입을 무엇으로 정의하느냐가 그 속성이 필터로 쓰일지 점수로 쓰일지를 결정한다.** 신뢰도를 0–100 decimal로 둔 덕분에 연속 가중합이 가능하고, 만약 High/Medium/Low enum이었다면 "Medium 이상만" 같은 필터로만 쓸 수 있었다. 반대로 자격 상태를 0–100 점수로 뒀다면 규제 조건을 돈으로 살 수 있게 되는 셈이다.

---

## 6. 한 줄 정리

Phase 4는 **필터 3개(승인 상태·capacity·지역)로 후보를 걸러낸 뒤**, `leadTimeSavedDays`(MitigationAction, 시간) · `pricePremiumPercent`(AlternativeSupplier, 돈) · `reliabilityScore`(Supplier, 확률) **3축을 0~1로 정규화해 가중합**하고, 그 순위를 다시 금액 ROI로 환산해 상위 3개 조치를 내놓는다. 시간·돈·확률을 함께 보기 때문에 "빠른데 못 믿을 곳"도 "싼데 늦는 곳"도 1위가 되지 않는다.
