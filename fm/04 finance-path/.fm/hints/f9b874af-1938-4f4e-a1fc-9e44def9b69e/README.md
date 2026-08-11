# 왜 금액 프로퍼티에 단위(USD)를 명시하는가

> **Q.** 온톨로지에서 금액 프로퍼티에 USD 같은 단위를 명시하는 이유는 무엇인가?
>
> **A.** 값의 해석을 명확히 하고 서로 다른 소스 시스템의 값을 비교·집계할 때 혼동을 막기 위해서다. `balance`, `amount`, `principal`, `purchasePrice`, `currentValue`가 모두 decimal(USD)이다.

---

## 1. 단위는 "설명"이 아니라 "계약"이다

Banking & Finance 경로의 엔티티 표를 보면 타입 칸이 그냥 `decimal`이 아니라 **`decimal (USD)`** 로 적혀 있다.

| 엔티티 | 프로퍼티 | 표기 |
|---|---|---|
| Account | `balance` | `decimal (USD)` |
| Account | `interestRate` | `decimal (%)` |
| Transaction | `amount` | `decimal (USD)` |
| Loan | `principal` | `decimal (USD)` |
| Loan | `apr` | `decimal (%)` |
| Loan | `term` | `integer (months)` |
| Investment | `purchasePrice` | `decimal (USD)` |
| Investment | `currentValue` | `decimal (USD)` |
| Investment | `shares` | `decimal` (무단위 수량) |

`decimal`은 **값의 표현 방식**만 말해준다. "소수점을 갖는 십진수"라는 것이다. 하지만 `1500.00`이라는 값이 **무엇 1500개인지**는 말해주지 않는다. 1500달러인가, 1500센트(=15달러)인가, 1500원인가, 1500엔인가?

물리학에서 "속도 = 5"가 무의미하고 "5 m/s"여야 의미가 생기는 것과 정확히 같다. 금액 프로퍼티에서 단위는 **타입 시스템이 잡아주지 못하는 나머지 절반의 계약**이다. 그래서 온톨로지는 이것을 스키마 수준에 못 박아둔다. 온톨로지는 "데이터의 모양을 기술하는 것"이고(경로의 반복되는 메시지), 단위는 그 모양의 일부다.

특히 이 시나리오가 **코어 뱅킹 시스템, 결제 프로세서, 신용평가기관, 증권사 플랫폼**이라는 4개의 서로 다른 소스에서 데이터를 끌어온다는 점이 결정적이다. 단일 시스템 안에서는 "우리는 다 달러야"가 암묵적 상식으로 통하지만, 여러 시스템을 하나의 그래프로 합치는 순간 그 상식은 사라진다. 온톨로지는 바로 이 통합 지점에 놓이는 계층이므로, 암묵적 상식을 명시적 선언으로 승격시키는 것이 그 역할이다.

---

## 2. 단위 없는 숫자가 만드는 세 가지 실제 사고

### 사고 A — 서로 다른 통화를 그냥 `SUM` 한 무의미한 합계

경로 마지막의 GQL 예제를 보자.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment),
      (c)-[:has_loan]->(loan:Loan)
WITH c, SUM(inv.currentValue) AS portfolio, SUM(loan.principal) AS debt
WHERE portfolio > debt
RETURN c.name, portfolio, debt
```

`SUM(inv.currentValue)`는 **모든 `currentValue`가 같은 통화라는 가정 위에서만** 의미가 있다. 만약 이 고객이 미국 주식(USD)과 일본 주식(JPY)을 함께 들고 있고 소스 시스템이 각자의 현지 통화로 값을 넣었다면:

```
currentValue: 10000   (USD 포지션)
currentValue: 1000000 (JPY 포지션, 실제로는 약 6,700 USD)
SUM = 1010000   ← 이 숫자는 달러도 아니고 엔도 아니다. 아무 단위도 아니다.
```

더 나쁜 점은 **에러가 나지 않는다**는 것이다. `1010000`은 타입도 맞고 부호도 맞고 그럴듯하게 보인다. `WHERE portfolio > debt` 비교도 조용히 통과한다. 결과는 "포트폴리오가 부채보다 크다"는 완전히 잘못된 결론이고, 이 값이 리스크 리포트나 규제 보고에 실려 나간다. 단위 불일치 버그는 크래시가 아니라 **조용한 오답**으로 나타나기 때문에 가장 위험하다.

### 사고 B — 센트 시스템 + 달러 시스템 = 100배 오차

금액을 정수 센트로 저장하는 관행은 매우 흔하다(Stripe, Adyen 등 대부분의 결제 API가 minor unit 정수를 쓴다). 그래서 실무에서 자주 벌어지는 일:

- 코어 뱅킹 시스템: `balance = 1500.00` → 1,500달러
- 결제 프로세서: `amount = 150000` → 1,500달러 (센트 정수)

두 값을 같은 `amount` 프로퍼티로 매핑하면 결제 프로세서 쪽 거래가 **100배로 뻥튀기**된다. 이상거래 탐지 룰("1만 달러 이상 거래 플래그")이 모든 거래를 잡아내고, 일별 정산이 100배로 어긋나고, 반대 방향 실수(달러 값을 센트로 해석)에서는 반대로 100배 축소되어 이상거래가 전부 임계값 밑으로 숨는다.

이 사고를 막는 건 코드가 아니다. **"`amount`는 USD, major unit, 소수 2자리"** 라는 스키마 선언이 있어야 매핑 담당자가 `150000`을 보고 "이건 스케일이 안 맞는다"고 판단할 근거가 생긴다.

### 사고 C — 비율을 0.05와 5로 섞어 저장

`interestRate`와 `apr`은 `decimal (%)`이다. 여기서 `%`가 없으면:

- A 시스템: `interestRate = 0.05` (소수 비율, fraction)
- B 시스템: `interestRate = 5` (퍼센트 포인트)

둘 다 "연 5%"를 뜻하지만 숫자는 100배 다르다. 이자 계산에 그대로 넣으면:

```
이자 = principal × rate
     = 300000 × 5      = 1,500,000  ← 원금의 5배를 이자로 청구
     = 300000 × 0.05   = 15,000     ← 정답
```

그리고 이 값들은 **둘 다 "그럴듯한 이자율"** 이다. `0.05`도 `5`도 검증 로직 `0 < rate < 100`을 통과한다. 즉 값의 범위만으로는 어느 쪽 규약인지 구별할 수 없다. `decimal (%)`라는 단위 선언은 "이 프로퍼티에는 퍼센트 포인트 값(5)이 들어간다, 0.05가 아니다"를 스키마에 고정시키는 장치다.

---

## 3. 단위를 표기하는 세 가지 실무 방식과 트레이드오프

### (a) 프로퍼티 이름에 단위를 박는다 — `balanceUsd`

```
Account.balanceUsd : decimal
Transaction.amountUsd : decimal
Loan.principalUsd : decimal
```

- **장점**: 단위가 이름과 물리적으로 붙어 다닌다. 쿼리를 쓰는 사람, 로그를 읽는 사람, CSV 헤더를 보는 사람 모두가 별도 메타데이터를 조회하지 않고도 단위를 안다. 스키마 메타데이터를 지원하지 않는 하위 시스템(플랫 파일, 레거시 BI 도구)으로 값이 흘러가도 단위 정보가 살아남는다. NASA식 명명 규약(`altitudeMeters`, `delayMs`)의 금융판이다.
- **단점**: 단위가 바뀌면 **이름이 바뀌고, 이름이 바뀌면 모든 쿼리·리포트·다운스트림 코드가 깨진다**. 통화를 추가하려면 `balanceUsd`, `balanceEur`, `balanceJpy`처럼 프로퍼티가 통화 수만큼 늘어나는 조합 폭발이 일어난다. 도메인 용어("balance")와 표현 규약("Usd")이 한 문자열에 섞여 있어서 온톨로지 어휘가 지저분해진다.

### (b) 스키마 메타데이터로 단위를 선언한다 — `decimal (USD)` ← **이 경로가 택한 방식**

```
Account.balance : decimal    unit = USD
Loan.apr        : decimal    unit = %
Loan.term       : integer    unit = months
```

- **장점**: 프로퍼티 이름은 순수한 도메인 어휘(`balance`, `amount`, `principal`)로 유지된다. 단위는 스키마의 1급 속성이므로 도구가 기계적으로 읽어 UI 포맷팅(통화 기호, 소수 자릿수), 검증, 문서 생성에 쓸 수 있다. 단위를 바꿀 때 이름을 바꾸지 않으므로 쿼리 호환성이 유지된다. 학습용 온톨로지가 "타입 + 단위"를 한 칸에 적어 보여주기에도 가장 간결하다.
- **단점**: 단위가 **스키마 레벨의 상수**다. 즉 이 프로퍼티의 모든 인스턴스가 같은 단위임을 전제한다. 인스턴스마다 통화가 다른 다통화 데이터를 표현할 수 없다. 또한 값이 스키마 컨텍스트를 벗어나는 순간(JSON으로 export, 메시지 큐로 전송, 스프레드시트로 붙여넣기) 단위 정보가 떨어져 나간다.

### (c) 값과 통화 코드를 함께 갖는 복합 프로퍼티/엔티티 — `amount` + `currencyCode`

```
Transaction.amount        : decimal
Transaction.currencyCode  : string   (ISO 4217, 예: "USD", "JPY", "KWD")
```

또는 독립 값 객체(value object)로 승격:

```
MonetaryAmount { value: decimal, currency: string(ISO 4217) }
Transaction.amount : MonetaryAmount
```

- **장점**: 단위가 **데이터와 함께 이동한다**. 인스턴스마다 통화가 다를 수 있으므로 진짜 다통화를 표현할 수 있다. 집계 시 통화 코드로 `GROUP BY`를 강제할 수 있어서 사고 A(무의미한 SUM)를 구조적으로 막는다. 이것이 FIBO 같은 실무 금융 온톨로지와 대부분의 결제 API가 취하는 형태다.
- **단점**: 모든 산술이 무거워진다. 두 `MonetaryAmount`를 더하려면 통화가 같은지 검사하거나 환율 변환을 거쳐야 하고, 그 자리에서 "언제 시점의 환율인가"라는 질문이 따라온다(→ 6절). 그래프 쿼리도 `SUM(amount)`가 아니라 통화별 분리 집계가 되어 복잡해진다. 스키마와 쿼리와 UI 모두에 비용이 붙는다.

> **다통화를 다뤄야 하면 답은 (c)다.** (a)와 (b)는 둘 다 "단위가 프로퍼티마다 고정"이라는 같은 한계를 공유한다. 통화가 인스턴스 속성인 세계에서는 인스턴스에 통화를 담을 자리가 반드시 있어야 한다.

### 이 경로가 (b)에 머문 이유

이 시나리오는 **미국 리테일 뱅킹 플랫폼**이다. 문제 정의 자체가 `$100K 초과 대출`, `creditScore 300–850`, `ssn`, `MSFT`/`AAPL` 같은 미국 단일 통화 컨텍스트로 잡혀 있다. 단일 통화 가정이 도메인 사실로 성립하는 상황에서 모든 금액 프로퍼티에 `currencyCode`를 하나씩 붙이면, 항상 `"USD"`인 컬럼 5개가 생기고 쿼리는 무의미한 통화 일치 검사로 뒤덮인다.

즉 (b)는 **타협이 아니라 명시된 가정 위의 올바른 선택**이다. 중요한 건 그 가정이 스키마에 적혀 있다는 점이다. `decimal (USD)`라는 표기가 있으면 나중에 이 온톨로지에 유럽 지점 데이터를 붙이려는 사람이 "아, 이 모델은 단일 통화를 가정했구나 → (c)로 마이그레이션이 필요하구나"를 즉시 안다. 단위가 안 적혀 있으면 그 사람은 아무것도 모른 채 EUR 값을 `balance`에 밀어넣고 사고 A를 재현한다. **단위 표기는 현재의 정확성뿐 아니라 미래의 확장 판단에도 필요한 정보다.**

---

## 4. ISO 4217과 통화별 소수 자릿수 — "센트 정수 저장"이 통화마다 달라지는 이유

통화 코드의 표준은 **ISO 4217**이다. 3글자 알파벳 코드(USD, JPY, KRW)와 3자리 숫자 코드를 정의하고, 여기에 **minor unit(소수 자릿수, exponent)** 을 함께 규정한다. minor unit은 "주 통화 단위를 몇 자리 소수까지 쪼개는가"다.

| exponent | 예시 통화 | 보조 단위 | 1 주단위 = |
|---|---|---|---|
| **0** | JPY, KRW, VND, ISK, CLP, XAF, XOF, BIF, GNF, RWF, UGX, PYG, VUV, KMF, DJF, XPF | 없음 | — |
| **2** | USD, EUR, GBP, CHF, CNY, CAD, AUD (대다수) | cent, penny, centime… | 100 |
| **3** | BHD, KWD, OMR, JOD, TND, IQD, LYD | fils, millime | 1,000 |

- **JPY(일본 엔)**: 소수 자릿수 **0**. `¥1500`은 1500엔이고 그 아래 단위가 유통되지 않는다.
- **USD(미국 달러)**: 소수 자릿수 **2**. 1달러 = 100센트.
- **BHD(바레인 디나르), KWD(쿠웨이트 디나르)**: 소수 자릿수 **3**. 1 KWD = 1,000 fils.

### 그래서 "센트 정수로 저장" 전략은 통화 독립적이지 않다

정수 저장의 정확한 표현은 "센트로 저장"이 아니라 **"해당 통화의 minor unit으로 저장"** 이다. 곱하는 배수가 통화마다 다르다.

| 사람이 읽는 금액 | 통화 | exponent | minor unit 정수 |
|---|---|---|---|
| 15.00 | USD | 2 | `1500` (×100) |
| 1500 | JPY | 0 | `1500` (×1) |
| 15.000 | KWD | 3 | `15000` (×1000) |

같은 정수 `1500`이 통화에 따라 **15달러 / 1500엔 / 1.5디나르** 를 뜻한다. 여기서 두 가지 결론이 나온다.

1. **정수 저장 방식은 통화 코드 없이는 원천적으로 해석 불가능하다.** minor unit 정수를 쓰겠다면 (c) 방식(값 + 통화 코드)이 사실상 필수다. `×100`을 하드코딩한 코드는 JPY 값을 100배로, KWD 값을 10배 작게 만든다.
2. **`decimal (USD)` 표기는 exponent 2까지 간접적으로 함의한다.** USD의 minor unit이 2라는 것이 표준에 있으므로, 단위를 USD로 못 박으면 "소수 2자리까지 유효, 반올림 단위는 0.01"이라는 정밀도 규약이 따라온다. 화면 포맷, 반올림 규칙, 정산 오차 허용 범위가 모두 이 한 줄에서 파생된다.

> 참고: `shares`(보유 주식 수)는 표에서 단위 표기 없는 순수 `decimal`이다. 이건 누락이 아니라 **본질적으로 무차원 수량(count)** 이기 때문이다. 소수인 이유는 소수점 주식(fractional shares)과 주식 분할 때문이고, 여기에 "USD"를 붙이면 오히려 틀린다. 단위 표기의 규율은 "모든 숫자에 단위를 붙이라"가 아니라 **"단위가 있는 양에는 반드시 붙이고, 무차원 양에는 붙이지 않는다"** 다.

---

## 5. `decimal` vs `float` — 왜 타입까지 금액용으로 골랐나

금액 프로퍼티가 전부 `decimal`이고 `float`/`double`이 하나도 없는 것도 같은 계약의 일부다.

IEEE 754 이진 부동소수점은 값을 2의 거듭제곱의 합으로 표현한다. 그런데 `0.1`이나 `0.01` 같은 십진 소수는 2진법에서 **유한 자리로 표현되지 않는다**(1/10은 2진 순환소수). 그래서 저장 순간부터 아주 작은 오차가 들어간다.

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 0.1 + 0.2 == 0.3
False
>>> 1.10 - 1.00
0.10000000000000009
```

한 번은 무해해 보이지만 금융에서는 두 가지 방식으로 터진다.

1. **오차 누적** — 거래를 수백만 건 합산하면 개별 오차가 쌓여서 센트 단위, 나아가 눈에 보이는 금액 단위의 정산 불일치가 된다.

```python
>>> total = 0.0
>>> for _ in range(1_000_000):
...     total += 0.01      # 1센트 거래 100만 건
>>> total
10000.000000018848         # 정답은 정확히 10000.00
```

2. **동등성/임계값 비교 실패** — `balance == 0.0`이 성립하지 않아 "잔액 0" 계좌가 잡히지 않고, `amount >= 10000` 규제 임계값이 경계에서 어긋난다.

`decimal`(십진 고정소수점 / 임의정밀도 십진)은 값을 10의 거듭제곱 기반으로 저장하므로 십진 소수를 정확히 표현하고, 반올림 시점과 규칙을 **명시적으로** 통제할 수 있다.

```python
from decimal import Decimal, getcontext, ROUND_HALF_UP

Decimal("0.1") + Decimal("0.2") == Decimal("0.3")   # True

# 금액은 반드시 문자열/정수로 생성한다. Decimal(0.1)은 float 오차를 그대로 물려받는다.
Decimal(0.1)        # Decimal('0.1000000000000000055511151231257827021181583404541015625')
Decimal("0.1")      # Decimal('0.1')

# USD는 minor unit 2자리 → 0.01 단위로 명시적 반올림
getcontext().rounding = ROUND_HALF_UP
balance   = Decimal("1500.00")
apr       = Decimal("5.25") / Decimal("100")        # decimal (%) → fraction 변환은 한 곳에서만
interest  = (balance * apr).quantize(Decimal("0.01"))
interest  # Decimal('78.75')

total = sum((Decimal("0.01") for _ in range(1_000_000)), Decimal("0"))
total  # Decimal('10000.00')  ← 오차 0
```

정리하면 금액 프로퍼티의 완전한 계약은 **세 조각**이다: `decimal`(표현 방식) + `USD`(단위) + `2자리 / 0.01 반올림`(정밀도). 온톨로지 표의 `decimal (USD)`는 이 셋을 압축해 담은 표기다.

---

## 6. 같은 원리가 적용된 다른 단위 프로퍼티들

### `interestRate` / `apr` — `decimal (%)`

- **fraction vs percent 혼동**: 3절 사고 C. `0.05` vs `5`. `%` 표기는 후자로 고정.
- **연이율 vs 월이율 혼동**: 이게 더 흔하고 더 조용하다. `apr = 5`가 연 5%인지 월 5%인지 구별되지 않으면 12배 오차가 난다. 월 5%는 복리로 연 79.6%다. 대출 상환 스케줄 계산은 보통 월 이율(`apr / 12`)을 쓰기 때문에, 소스 시스템이 이미 월 이율을 넣어둔 값을 다시 12로 나누면 실제 이자의 1/12이 나온다. 이름에 있는 **A**nnual과 스키마의 `%`가 함께 "이 값은 연율, 퍼센트 포인트"를 못 박는다. 엄밀하게 하려면 `unit = % per annum` 수준까지 적는 게 맞다.
- **APR vs APY 차이**: 둘 다 `decimal (%)`이지만 **의미가 다른 단위**다.
  - **APR**(Annual Percentage Rate)은 **차입 비용**이다. 이자에 수수료까지 포함한 총 차입 비용을 연율로 환산하지만, **복리 효과를 반영하지 않는다**(명목 연율). 대출·신용카드·모기지에 쓰인다. 이 경로에서 `Loan.apr`인 이유다.
  - **APY**(Annual Percentage Yield)는 **예금에서 얻는 수익률**이고, **복리를 반영한다**. `APY = (1 + r/n)^n − 1` (r = 명목 연이율, n = 연간 복리 횟수).
  - 그래서 같은 명목 5%라도 월 복리면 APY ≈ 5.116%다. `apr = 5`인 값과 `apy = 5.116`인 값을 같은 컬럼에 섞으면 대출 비용과 예금 수익을 직접 비교하는 리포트가 미묘하게 틀린다. **단위가 같아도(`%`) 의미론적 규약이 다르면 여전히 섞어선 안 된다** — 단위 표기의 한계이자, 프로퍼티 이름과 문서가 함께 필요한 이유다.

### `Loan.term` — `integer (months)`

`term = 360`은 360**개월**(30년 모기지)이다. `months`가 없으면 360년, 360일, 360주로 읽힐 수 있고, 30년 모기지를 `term = 30`으로 넣는 시스템과 섞이면 12배 오차가 난다. 상환액 계산 공식이 `n = 개월 수`를 전제하므로, 이 오차는 월 상환액을 12배 부풀리거나 1/12로 줄인다. `integer`인 것도 계약이다 — 반개월 같은 값은 허용하지 않는다.

### `Investment.shares` — 단위 없는 `decimal`

앞서 말한 무차원 수량. 다만 여기에도 숨은 규약이 있다: `purchasePrice`와 `currentValue`가 **1주당 가격인지 포지션 전체 금액인지**. `shares = 10, purchasePrice = 150` 이면 총액은 1,500달러(주당 가격) 또는 150달러(포지션 총액)로 10배 갈린다. 표는 이걸 명시하지 않는데, 실무 온톨로지라면 `purchasePricePerShare` 같은 이름이나 프로퍼티 설명으로 못 박아야 한다. **단위 다음 층의 계약은 "무엇에 대한 값인가(per what)"** 다.

---

## 7. 환율이 개입하면 — 시점 의존 단위 변환

다통화로 확장하는 순간 새 문제가 생긴다. USD와 JPY는 단순 배수 관계가 아니라 **시간에 따라 변하는 환율**로 연결된다. 즉 통화 간 변환은 정적 단위 변환(미터↔피트)이 아니라 **시점 의존 변환**이다.

그래서 `SUM(currentValue)`를 다통화에서 하려면 스키마에 새 정보가 필요해진다.

- **어느 시점의 환율인가** — 거래 발생 시점(historical rate)? 리포트 기준일(spot rate)? 회계 기간 평균? 결산일 마감 환율? 같은 포트폴리오가 기준에 따라 다른 값을 낸다. 회계 기준(예: 자산·부채는 마감 환율, 손익은 거래일 환율)이 이걸 규정한다.
- **어떤 환율 소스인가** — 중앙은행 고시, 시장 미드레이트, 매수/매도 호가. 매수·매도 스프레드 때문에 방향에 따라 값이 다르다.
- **보고 통화(reporting currency)는 무엇인가** — 원 통화(transaction currency)와 별도로, 집계 결과를 표현할 통화를 명시해야 한다.

그러면 모델이 이렇게 자란다.

```
Transaction.amount           : decimal            # 원 통화 금액
Transaction.currencyCode     : string (ISO 4217)  # 원 통화
Transaction.fxRate           : decimal            # 보고 통화 환산율
Transaction.fxRateAsOf       : datetime           # 그 환율의 기준 시점
Transaction.amountReporting  : decimal (USD)      # 환산 결과 (보고 통화)
```

`fxRateAsOf`가 `datetime`인 것에 주목하자. 트랜잭션 `timestamp`가 `date`가 아니라 `datetime`인 이유(사기 탐지 정밀도)와 같은 성격의 판단이다.

**이 경로는 이 확장을 다루지 않는다.** 5 엔티티 / 6 관계 규모의 학습 온톨로지가 단일 통화 가정으로 끝나기 때문에, 환율·보고 통화·시점 기준은 등장하지 않는다. 하지만 `decimal (USD)`라는 한 줄이 바로 이 확장이 **필요한지 여부를 판단할 수 있는 지점**을 남겨둔다. 단위를 안 적어두면, 다통화가 필요해졌다는 사실 자체를 사고가 터진 뒤에야 알게 된다.

---

## 8. 요약

| 프로퍼티 | 타입 | 단위 | 단위 누락 시 위험 |
|---|---|---|---|
| `Account.balance` | decimal | USD | 다통화 계좌를 그냥 SUM해 무의미한 총자산; 센트 저장 시스템과 합쳐 100배 오차 |
| `Transaction.amount` | decimal | USD | 결제 프로세서의 minor unit 정수(`150000`)를 달러로 오해 → 이상거래 임계값·정산 100배 붕괴 |
| `Loan.principal` | decimal | USD | `principal > 100000` 규제 필터가 통화별로 다른 뜻이 됨 → 고위험 대출 누락 또는 오탐 |
| `Investment.purchasePrice` | decimal | USD | 주당 가격 vs 포지션 총액, 통화 혼재로 손익 계산 오류 |
| `Investment.currentValue` | decimal | USD | 포트폴리오 집계가 통화 혼합으로 오염 → `portfolio > debt` 비교가 조용히 오답 |
| `Account.interestRate` | decimal | % (연율) | `0.05` vs `5` 100배; 연이율 vs 월이율 12배; 둘 다 검증을 통과함 |
| `Loan.apr` | decimal | % (연율) | 위와 동일 + APR(복리 미반영, 수수료 포함) / APY(복리 반영) 혼재 → 비용·수익 비교 왜곡 |
| `Loan.term` | integer | months | 360개월 ↔ 360년/일/주 오해; 30년을 `30`으로 넣는 시스템과 섞여 12배 오차 |
| `Investment.shares` | decimal | (무차원 수량) | 단위가 없어야 맞음 — 단위 규율은 "무차원 양에는 붙이지 않는다"까지 포함 |
| `Transaction.timestamp` | datetime | (시각, 타임존 규약 필요) | 단위의 사촌 문제: 로컬 시각 vs UTC 혼재로 일별 마감·사기 탐지 윈도우 어긋남 |

**핵심 한 줄**: `decimal`은 값이 *어떻게 표현되는지*를 말하고, `(USD)`는 값이 *무엇을 의미하는지*를 말한다. 여러 소스 시스템을 하나의 그래프로 통합하는 온톨로지에서는 후자가 없으면 모든 비교와 집계가 근거를 잃는다 — 그리고 그 실패는 에러가 아니라 그럴듯한 오답으로 나타난다.

---

### 출처

- [ISO 4217 — Currency codes (ISO)](https://www.iso.org/iso-4217-currency-codes.html)
- [ISO 4217 (Wikipedia) — 통화 코드 및 minor unit 목록](https://en.wikipedia.org/wiki/ISO_4217)
- [Currency codes and minor units (Adyen Docs)](https://docs.adyen.com/development-resources/currency-codes)
- [Currency Codes and Minor Units (Datatrans Docs)](https://docs.datatrans.ch/docs/currency-codes)
- [APY vs. APR: differences (CIBC US)](https://us.cibc.com/en/personal/cibc-insights/apy-vs-apr-differences.html)
- [What is APY and how is it calculated? (Fidelity)](https://www.fidelity.com/learning-center/smart-money/what-is-apy)
- [APR vs APY (Ally)](https://www.ally.com/stories/save/apy-vs-apr-what-is-apr-what-is-apy/)
