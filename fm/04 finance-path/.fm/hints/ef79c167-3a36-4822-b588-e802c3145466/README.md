# Merchant를 프로퍼티로 둔 설계의 의미

## 카드가 묻는 것

Banking & Finance 경로의 Transaction 엔티티는 이렇게 정의된다.

| Property | Type | Identifier? |
|---|---|---|
| `transactionId` | string | ✓ |
| `amount` | decimal (USD) | |
| `type` | string | |
| `timestamp` | datetime | |
| `merchant` | string | |

원문의 설명은 두 줄이다.

> The `merchant` property captures where the transaction occurred — useful for spending category analysis.
>
> The `merchant` property opens up spending analysis without adding a Merchant entity.

즉 "가맹점"이라는 개념을 **엔티티로 승격하지 않고 문자열 프로퍼티 한 칸으로 처리**했다. 정답이 말하는 핵심은 이것이 게으름이 아니라 **필요한 분석에 충분한 최소 모델(minimal sufficient model)의 선택**이라는 점이다. 엔티티를 하나 늘리면 노드 1개가 아니라 노드 + 식별자 + 관계 + 조인 경로 + 데이터 파이프라인이 함께 늘어난다. 프로퍼티로 답할 수 있는 질문이라면 프로퍼티로 답하는 것이 모델을 단순하게 유지한다.

---

## 판단 기준 1: 프로퍼티로 충분한 조건

어떤 개념을 프로퍼티로 남겨도 되는지는 아래 네 가지를 모두 만족하는지로 판단한다.

### (1) 자체 식별자가 필요 없다

Transaction은 `transactionId`, Account는 `accountNumber`, Customer는 `customerId`를 갖는다. 엔티티의 존재 이유 중 하나는 "이것과 저것이 같은 것인가"를 판정할 수 있는 안정적 키다. `merchant = "Starbucks"`는 키가 아니라 **라벨**이다. 이 문자열로 특정 가맹점을 유일하게 지목할 필요가 없다면 엔티티일 이유가 약하다.

### (2) 자체 프로퍼티가 없다

Merchant 엔티티가 의미를 갖는 순간은 가맹점에 대해 *별도로 알고 싶은 사실*이 생길 때다. 주소, 업종 카테고리, MCC, 사업자번호, 가맹 시작일 같은 것. 지금 모델에서 가맹점에 대해 알고 싶은 사실은 "이름" 하나뿐이다. 프로퍼티가 하나뿐인 엔티티는 사실상 문자열이다.

### (3) 다른 엔티티와 관계를 맺지 않는다

Merchant는 현재 어떤 화살표의 출발점도 도착점도 아니다. Loan은 Customer(`has_loan`)와 Account(`funds`) 양쪽에 붙기 때문에 엔티티여야 하고, Investment는 `holds`/`linked_to` 두 경로를 만들기 때문에 엔티티여야 한다. Merchant에는 그런 연결 요구가 없다.

### (4) 값 자체가 분석 차원(dimension)으로만 쓰인다

"What did this customer spend at restaurants last month?" 같은 질문에서 가맹점명은 **그룹핑 키 / 필터 값**으로만 등장한다. 차원 값으로만 소비되는 개념은 프로퍼티가 자연스러운 자리다. 데이터 웨어하우스 용어로 말하면, 별도 차원 테이블로 뽑을 필요 없이 팩트 테이블에 남겨두는 **디제너레이트 디멘션(degenerate dimension)** 에 가깝다.

---

## 판단 기준 2: 엔티티로 올려야 하는 신호

반대로 아래 신호가 하나라도 나타나면 프로퍼티는 한계에 도달한 것이다.

| 신호 | 왜 프로퍼티로는 안 되는가 |
|---|---|
| **가맹점 자체의 속성이 필요해짐** — 카테고리, 주소/지역, MCC, 온·오프라인 채널 | 문자열 한 칸에 여러 속성을 담을 수 없다. `merchantCategory`, `merchantCity`, `merchantMcc`를 Transaction에 계속 덧붙이면 Transaction이 두 개념(거래 + 가맹점)을 동시에 기술하게 되어 응집도가 깨진다 |
| **같은 가맹점의 거래를 정확히 묶어야 함** — "이 가맹점에서의 총 지출", "가맹점별 상위 10곳" | 문자열 동일성은 개체 동일성이 아니다(아래 대가 참조) |
| **가맹점끼리 관계가 생김** — 프랜차이즈 본사와 지점, 체인 소속, 모회사, PG사 하위 서브머천트 | 관계는 엔티티 사이에만 그릴 수 있다. 문자열은 다른 문자열을 가리킬 수 없다 |
| **가맹점이 다른 도메인 엔티티와 연결됨** — 정산 계약, 분쟁/차지백 케이스, 사기 조사 대상, 로열티 프로그램, 리스크 스코어 | Transaction의 속성으로는 그 연결의 시작점을 만들 수 없다 |

정리하면: **개념이 "값"으로만 쓰이면 프로퍼티, "주체"로 쓰이기 시작하면 엔티티.** 무언가를 *가지기* 시작하거나 무언가와 *관계 맺기* 시작하면 승격 시점이다.

---

## 프로퍼티로 둘 때 실제로 치르는 대가

이 선택은 공짜가 아니다. 카드 거래 데이터에서는 대가가 아주 구체적으로 드러난다.

### (1) 문자열 표기 불일치로 그룹핑이 깨진다

카드 명세서에 찍히는 가맹점명은 사람이 정리해 넣은 이름이 아니라 **인수사(acquirer)가 승인 메시지에 넣은 디스크립터 원문**이다. 같은 브랜드가 이런 식으로 흩어진다.

```
STARBUCKS #12345 SEATTLE WA
SBX*STARBUCKS MOBILE ORDER
STARBUCKS COFFEE 0012345 CARD PURCHASE
SQ *STARBUCKS
TST* STARBUCKS - DOWNTOWN
```

`merchant`가 단순 문자열이면 `GROUP BY merchant`는 이들을 **다섯 개의 서로 다른 가맹점**으로 센다. 같은 매장이라도 점포번호, 국가, 구매 채널(모바일/키오스크/온라인)에 따라 표기가 달라지고, 결제 대행사 접두어(`SQ *`, `TST*`, `SBX*`)가 앞에 붙는다. 게다가 `SBUX`처럼 축약형이 섞이면 문자열 유사도로도 잡히지 않는다.

그래서 실무에서는 **가맹점명 정규화(merchant name normalization / merchant name cleansing)** 를 별도 단계로 둔다. 결제 네트워크와 데이터 벤더는 하나의 가맹점에 대해 여러 층의 이름을 관리한다 — Raw Merchant Name(인수사에서 받은 원문), Descriptor Name, Parsed Name, Normalized Name, DBA(상호), Merchant Corporate Name(법인명). 정규화 파이프라인은 특수문자·불용어 제거, 인코딩·구분자 표준화, 거래 ID 제거, 악센트 문자 치환을 거친 뒤 문자열 유사도나 NLP 모델로 후보를 같은 개체에 붙인다. 요컨대 **"프로퍼티로 두면 엔티티 해석(entity resolution) 문제를 쿼리 시점으로 미루는 것"** 이다. 모델은 단순해지고, 그 복잡성은 분석 쪽으로 이동한다.

### (2) 가맹점 단위 집계의 신뢰도가 떨어진다

이 경로가 노린 분석은 "소비 카테고리"다. 즉 *가맹점 하나하나*가 아니라 *가맹점 묶음(음식점, 주유, 항공)* 이 관심 대상이다. 여기서 표기 불일치의 타격은 상대적으로 작다 — Starbucks 표기가 다섯 갈래여도 전부 "커피/음식점" 버킷에 들어가면 카테고리 합계는 맞는다.

문제는 요구가 한 단계 정밀해질 때다. "가맹점별 상위 지출처", "이 가맹점에서의 첫 거래 시점", "같은 가맹점에서의 중복 청구 탐지" 같은 질문은 가맹점 단위 동일성이 보장되지 않으면 답 자체가 틀린다. 그리고 카테고리 분류 역시 문자열만으로 하면 규칙 기반 추측이 되는데, 실제 결제 인프라에는 이미 표준 코드가 있다.

**MCC(Merchant Category Code)** 는 ISO 18245로 정의된 네 자리 숫자 코드로, 가맹점이 온보딩될 때 인수사/결제 사업자가 그 업종에 가장 가까운 코드를 부여한다. 부여된 MCC는 인수사의 merchant master file에 저장되고 ISO 8583 승인 메시지의 DE-18 필드에 실려 발급사로 전달된다. 발급사는 이 코드로 카드 약관상 허용 거래인지 판단하고, 지출 관리·리워드 카테고리·규제 보고도 이 코드를 축으로 돈다. 즉 **카테고리는 원래 "가맹점에 붙은 속성"** 이며, 이런 속성을 제대로 다루려면 그것을 담을 주체(Merchant 엔티티)가 필요하다. `merchant` 문자열만으로 카테고리를 추정하는 것은 이미 존재하는 코드를 역추정하는 셈이다.

### (3) 중복 값을 한 번에 갱신할 수 없다

가맹점이 상호를 바꾸거나(리브랜딩), 정규화 규칙이 개선되거나, 잘못 분류된 카테고리를 고쳐야 할 때, 값이 수백만 건의 Transaction 행에 복제되어 있으면 **모든 행을 일괄 수정**해야 한다. 엔티티였다면 Merchant 노드 하나를 고치면 그 노드를 참조하는 모든 거래가 즉시 새 값을 본다. 이것이 정규화(normalization)의 고전적 이점이고, 비정규화의 고전적 대가다. 사기 조사나 감사처럼 "언제 무엇으로 판단했는가"를 재현해야 하는 맥락에서는 이 대량 갱신이 이력 추적까지 흐린다.

---

## 그래서 왜 이 단계에서는 프로퍼티인가

이 학습 경로의 목표를 다시 보면 답이 나온다.

- 3단계 커리큘럼의 학습 목표는 **소유 체인**(`Customer → Account → Transaction / Loan / Investment`), **datetime 정밀도**, **다중 경로 관계**다. Merchant는 이 세 가지 중 어느 것도 가르치지 않는다.
- 이 단계에서 답하려는 질문은 "이 고객이 지난달 식당에서 얼마 썼나" 수준의 **소비 카테고리 분석**이다. 여기에는 문자열 라벨로 충분하다.
- 엔티티를 하나 늘리면 학습자는 관계 하나(`made_at`)와 식별자 하나(`merchantId`)를 더 관리해야 하고, 정작 배워야 할 소유 체인의 형태가 흐려진다. 5 엔티티 / 6 관계라는 결과물의 선명함이 손해를 본다.

이것이 정답의 두 번째 문장 — "엔티티를 늘리지 않고 프로퍼티로 해결할 수 있으면 모델이 단순해진다" — 의 실질이다. 판단 기준은 **미래에 있을 수 있는 모든 질문**이 아니라 **지금 답해야 하는 질문**이다. 온톨로지는 도메인의 모든 진실을 담는 사전이 아니라 특정 질문을 답하기 위한 구조다.

---

## 나중에 엔티티로 승격할 때의 마이그레이션 경로

프로퍼티 선택이 되돌릴 수 없는 결정이 아니라는 점이 중요하다. 승격 경로는 명확하다.

**목표 형태**

```
Transaction --made_at--> Merchant
```

**Merchant 엔티티**

| Property | Type | Identifier? |
|---|---|---|
| `merchantId` | string | ✓ |
| `name` | string | |
| `mcc` | string | |
| `category` | string | |
| `city` | string | |

**관계**

- **made_at** — `Transaction` → `Merchant` (many-to-one)
  많은 거래가 한 가맹점에서 발생한다. 방향이 Transaction에서 나가는 것에 주의 — `has_transaction`(Account → Transaction)과 달리 여기서는 Transaction이 참조하는 쪽이다.

이렇게 하면 소유 체인이 `Customer → Account → Transaction → Merchant`로 한 칸 길어지고, "고위험 고객이 특정 업종에서 쓴 금액" 같은 질문이 순수한 그래프 순회가 된다.

**이행 단계**

1. **엔티티 해석** — 기존 `merchant` 문자열들을 정규화해 고유 가맹점 집합을 도출하고 `merchantId`를 부여한다. 여기가 가장 비싼 단계이며, 프로퍼티로 두는 동안 미뤄둔 비용을 이때 치른다.
2. **속성 채우기** — MCC·카테고리·주소를 결제 네트워크 데이터나 외부 벤더에서 보강(enrichment)한다.
3. **관계 생성** — 각 Transaction을 해석된 Merchant에 연결한다.
4. **원본 보존** — `Transaction.merchant` 문자열을 즉시 지우지 말고 원문 디스크립터로 남겨둔다. 정규화가 틀렸을 때 재처리할 근거가 되고, 감사 추적에도 쓰인다. 다만 이름은 `merchantDescriptor`처럼 "원문"임이 드러나게 바꾸는 편이 낫다. 정규화된 이름은 Merchant 쪽 `name`이 단일 진실 원천(single source of truth)이 된다.
5. **쿼리 이관** — `GROUP BY t.merchant`를 `MATCH (t:Transaction)-[:made_at]->(m:Merchant) ... GROUP BY m.merchantId`로 바꾼다.

승격은 기존 프로퍼티를 버리는 일이 아니라 **원문 문자열 옆에 해석된 개체를 추가하는 일**이다.

---

## 같은 판단이 적용된 다른 예

이 경로 안에는 동일한 저울질이 여러 번 등장한다. 전부 "엔티티가 될 수도 있었지만 프로퍼티로 남은" 개념이다.

| 프로퍼티 | 엔티티로 올린다면 | 지금 프로퍼티인 이유 | 승격 신호 |
|---|---|---|---|
| `Account.type` (checking / savings / brokerage) | `AccountType` 또는 `Product` 엔티티 | 값의 종류가 소수의 고정 집합이고, 계좌를 분류하는 차원으로만 쓰인다 | 상품별 수수료 체계·약관·규제 요건·상품 계층(브랜드 → 상품군 → 상품)이 필요해질 때. 실제 은행은 상품 카탈로그를 별도 엔티티로 관리한다 |
| `Transaction.type` (debit / credit / transfer) | `TransactionType` 코드 엔티티 | 열거형에 가깝고 자체 속성이 없다. 필터·집계 축으로만 소비된다 | 유형별 처리 규칙, 수수료 정책, 결제 스킴(ACH / 카드 / 와이어)별 메타데이터가 붙을 때 |
| `Investment.symbol` (MSFT, AAPL) | `Security` / `Instrument` 엔티티 | 지금 필요한 것은 "어떤 종목인가"의 라벨과 gain/loss 계산(`purchasePrice` vs `currentValue`)뿐 | 발행사·거래소·섹터·시가·ISIN/CUSIP 같은 식별자 체계가 필요해질 때. 특히 **여러 고객의 보유를 같은 종목으로 묶어 집계**해야 하면 승격이 사실상 강제된다 — 이때 종목은 `merchant`와 똑같은 개체 동일성 문제를 만난다 |

`symbol`이 `merchant`와 특히 대칭적이다. 둘 다 "외부 세계의 어떤 개체를 가리키는 짧은 문자열"이고, 둘 다 그 개체에 대해 더 알고 싶어지는 순간 엔티티가 된다. 차이는 `symbol`이 티커라는 **표준화된 코드**라서 표기 불일치 위험이 낮다는 점이다. 반면 가맹점 디스크립터는 표준이 없어서 정규화 부담이 훨씬 크다. **같은 "프로퍼티냐 엔티티냐" 질문에서도, 값이 표준 코드인지 자유 텍스트인지가 프로퍼티로 버틸 수 있는 기간을 좌우한다.**

---

## 한 줄 요약

`merchant`를 프로퍼티로 둔 것은 "가맹점은 중요하지 않다"는 판단이 아니라, **이 단계에서 답할 질문(소비 카테고리)에는 문자열 라벨이면 충분하고, 가맹점이 자체 속성을 갖거나 다른 개체와 관계를 맺기 시작할 때 `Transaction → made_at → Merchant`로 승격하면 된다**는 판단이다. 최소 모델은 미완성 모델이 아니라 **현재 질문에 맞춰 절제한 모델**이다.

---

## 참고 자료

- [Merchant category code — Wikipedia](https://en.wikipedia.org/wiki/Merchant_category_code)
- [ISO 18245 — Wikipedia](https://en.wikipedia.org/wiki/ISO_18245)
- [Merchant Category Codes (MCCs) Explained — Corpay](https://www.corpay.com/resources/blog/merchant-category-codes)
- [Creating Greater Insights with Merchant Name Cleansing (PDF) — Citi](https://www.citibank.com/tts/docs/1913475_Data_Is_King_Article.pdf)
- [What Is Merchant Normalization? — Coupa](https://www.coupa.com/blog/technology-innovation/what-merchant-normalization)
- [Parsing bank transaction strings is way harder than you think — DEV](https://dev.to/wes_dieleman/parsing-bank-transaction-strings-is-way-harder-than-you-think-4ao1)
- [Building a Merchant Name Cleaning Engine with SequenceMatcher and spaCy — Towards Data Science](https://towardsdatascience.com/an-overview-of-building-a-merchant-name-cleaning-engine-with-sequencematcher-and-spacy-9d8138b9aace/)
- [Transaction Enrichment for Fintech — Triqai](https://www.triqai.com/article/complete-guide-to-transaction-enrichment-for-fintech-apps)
