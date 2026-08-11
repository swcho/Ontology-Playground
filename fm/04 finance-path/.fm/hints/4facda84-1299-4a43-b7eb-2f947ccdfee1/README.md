# 프로퍼티 타입은 "질의 능력의 선언"이다

## 핵심 한 줄

타입을 고르는 행위는 **값을 어떤 비트로 저장할지 정하는 일이 아니라, 그 프로퍼티에 어떤 질문을 던질 수 있는지를 확정하는 일**이다. `creditScore: integer`는 "이 값은 크기를 비교할 수 있다"는 선언이고, `timestamp: datetime`은 "이 값은 시·분·초 단위로 앞뒤를 가릴 수 있다"는 선언이며, `balance: decimal`은 "이 값은 오차 없이 더할 수 있다"는 선언이다.

---

## 1. 타입을 "연산 계약(operation contract)"으로 보기

프로퍼티에 타입 `T`를 붙이면, 동시에 다음 여섯 가지 능력의 on/off가 결정된다.

| 능력 | 의미 | 없으면 못 하는 일 |
|---|---|---|
| **동등 비교** (equality) | `=`, `IN` | 조회·조인·그룹핑 |
| **순서 비교** (ordering) | `<`, `>`, `BETWEEN` | 범위 필터, 정렬, 상·하위 N |
| **산술** (arithmetic) | `+`, `-`, `*`, `/` | 파생값 계산 (손익, 이자액) |
| **집계** (aggregation) | `SUM`, `AVG`, `MIN`, `MAX`, `STDDEV` | 리포트, 대시보드, 임계 감시 |
| **구간/버킷팅** (bucketing) | 히스토그램, 시간 윈도우 | 코호트, 추세, 이동 평균 |
| **패턴 매칭** (pattern) | `LIKE`, 정규식, 접두사 검색 | 텍스트 탐색, 부분 일치 |

이 표가 왜 중요한가 하면, **연산 집합은 타입에서 파생될 뿐 프로퍼티 이름에서 파생되지 않기 때문**이다. 이름이 `amount`여도 타입이 `string`이면 질의 엔진은 그것을 더하지 못한다. 사람에게는 명백해도 엔진에게는 아니다.

그래서 타입 선택은 "저장 형식 결정"이 아니라 **하위의 모든 질의·리포트·규칙이 의존하는 계약서 작성**이다.

---

## 2. finance 온톨로지 전체를 타입별로 훑기

이 학습 경로의 5개 엔티티(Customer, Account, Transaction, Loan, Investment)에 등장하는 모든 프로퍼티를 타입 그룹으로 묶으면, 각 그룹이 열어 주는 연산이 선명하게 갈린다.

### (a) string — 식별자 (identifier)

| 프로퍼티 | 소속 엔티티 |
|---|---|
| `customerId` | Customer |
| `accountNumber` | Account |
| `transactionId` | Transaction |
| `loanId` | Loan |
| `holdingId` | Investment |

- **열리는 연산**: 동등 비교, 조인/트래버설의 키, 접두사 검색(`accountNumber LIKE '4021%'`)
- **의도적으로 닫히는 연산**: 산술. 계좌번호끼리 더하는 일은 의미가 없고, 애초에 불가능해야 옳다.
- **대표 질의**: `MATCH (a:Account {accountNumber: '...'})-[:has_transaction]->(t)` — 여기서 타입은 "이 값은 하나의 노드를 특정한다"는 계약이다.
- 식별자를 string으로 두는 것은 게으름이 아니라 **선행 0, 하이픈, 체크디지트, 영문 접두사를 그대로 보존하기 위한 선택**이다.

### (b) string — 열거형처럼 쓰이는 범주값 (categorical)

| 프로퍼티 | 소속 엔티티 | 실제 값 예 |
|---|---|---|
| `type` | Account | checking / savings / brokerage |
| `type` | Transaction | debit / credit / transfer / fee |
| `status` | Loan | active / paid_off / delinquent |
| `riskProfile` | Customer | low / medium / high |
| `symbol` | Investment | MSFT, AAPL |

- **열리는 연산**: 동등 비교, `IN`, **그룹핑**(`GROUP BY type`), 카운트
- **대표 질의**: `Customer (riskProfile='high') → Loan (principal > 100000)` — 학습 경로가 처음부터 강조한 컴플라이언스 질의의 진입 조건이 바로 이 범주값이다.
- **주의**: 순서 비교가 문자열의 사전순으로만 열린다. `riskProfile`은 개념적으로 low < medium < high라는 순서가 있는데, 문자열 정렬로는 high < low < medium이 된다. 위험 등급으로 **정렬**해야 한다면 별도의 순위 integer(예: `riskRank: 1/2/3`)를 두거나 코드 테이블로 순서를 정의해야 한다. 즉 "범주값 string"은 그룹핑은 열어 주지만 순서는 열어 주지 않는다.

### (c) integer — 셀 수 있는 정수

| 프로퍼티 | 소속 엔티티 | 단위 |
|---|---|---|
| `creditScore` | Customer | (300–850 척도) |
| `term` | Loan | months |

- **열리는 연산**: 순서 비교, 범위 필터, 집계, 버킷팅, 산술
- **대표 질의**: `creditScore > 700`(대출 심사 임계), `AVG(creditScore) GROUP BY riskProfile`(등급 검증), `term >= 360`(30년 만기 모기지 추출), `term / 12`(연 단위 환산)
- **소수가 필요 없다는 정보 자체가 계약**이다. 정수 선언은 "0.5개월 만기, 712.4점 신용점수는 존재하지 않는다"는 도메인 사실을 스키마에 새긴다.

### (d) decimal — 금액 (USD)

| 프로퍼티 | 소속 엔티티 |
|---|---|
| `balance` | Account |
| `amount` | Transaction |
| `principal` | Loan |
| `purchasePrice` | Investment |
| `currentValue` | Investment |

- **열리는 연산**: 정확한 산술과 집계. decimal은 10진 기반이라 `0.1 + 0.2`가 정확히 `0.3`이 된다.
- **대표 질의**: `SUM(inv.currentValue) > SUM(loan.principal)`(포트폴리오 vs 부채), `SUM(t.amount) GROUP BY merchant`(지출 분석), `currentValue - purchasePrice`(손익)
- **왜 float이 아닌가**: 이진 부동소수는 0.01 같은 값을 정확히 표현하지 못한다. 거래 수백만 건을 `SUM`하면 오차가 누적되어 원장 대조(reconciliation)가 깨진다. 금융에서 decimal 선택은 취향이 아니라 **감사 가능성(auditability) 요건**이다.

### (e) decimal — 비율/퍼센트 (%)

| 프로퍼티 | 소속 엔티티 |
|---|---|
| `interestRate` | Account |
| `apr` | Loan |

- **열리는 연산**: 범위 비교(`apr > 15.0`), 금액과의 곱셈(`principal × apr` → 이자 비용), 평균
- **금액 decimal과 타입은 같지만 단위가 다르다.** 그래서 온톨로지는 타입 옆에 **단위(%)를 함께 표기**한다. 타입이 "무엇을 할 수 있는가"를 정하고, 단위가 "그 결과를 어떻게 읽어야 하는가"를 정한다. 단위 표기가 없으면 4.5가 4.5%인지 0.045인지 알 수 없어 산술은 가능하지만 **의미가 없는 산술**이 된다.

### (f) decimal — 수량

| 프로퍼티 | 소속 엔티티 |
|---|---|
| `shares` | Investment |

- 주식 수량은 왜 integer가 아니고 decimal인가. **소수점 주식(fractional shares)** 과 배당 재투자 때문에 0.3742주 같은 보유가 실재한다. integer로 선언하면 이 도메인 사실이 스키마 단계에서 잘려 나가고, 이후 모든 평가액 계산이 반올림 오차를 안는다.
- **대표 질의**: `shares × currentPrice`(평가액), `SUM(shares) GROUP BY symbol`(종목별 총 보유)

### (g) date — 날짜

| 프로퍼티 | 소속 엔티티 |
|---|---|
| `openDate` | Account |

- **열리는 연산**: 날짜 범위(`openDate >= '2020-01-01'`), 연/월 버킷팅, 기간 계산(계좌 개설 후 경과 일수)
- 계좌 개설은 **영업일 단위 사건**이라 시·분·초 해상도가 불필요하다. date는 "이 값의 의미 있는 최소 단위는 하루"라는 선언이다.

### (h) datetime — 시각

| 프로퍼티 | 소속 엔티티 |
|---|---|
| `timestamp` | Transaction |

- **열리는 연산**: 초 단위 순서 비교, 시간 윈도우(최근 10분 내 N건), 동일 시각 다중 거래 탐지, 시간 파티셔닝
- **대표 질의**: 사기 탐지 — "같은 계좌에서 5분 안에 3개 도시에서 결제". 이 질의는 date로는 **원리적으로 표현 불가능**하다. 필요한 정보가 저장 단계에서 사라졌기 때문이다.
- 같은 "시간"인데 `openDate`는 date, `timestamp`는 datetime인 이유가 이 카드의 요지를 압축한다. **필요한 질의의 해상도가 타입을 결정한다.**

---

## 3. 타입이 질의 엔진에 주는 부수 효과

타입은 논리적 계약이지만, 실제 엔진에서는 물리적 실행 계획까지 바꾼다.

| 효과 | 내용 |
|---|---|
| **인덱스 종류 선택** | 순서가 있는 타입(integer, decimal, date, datetime)은 **B-tree** 범위 인덱스를 만들 수 있어 `principal > 100000`이 인덱스 스캔으로 처리된다. 식별자 string은 **해시 인덱스**로 점 조회에 최적화되고, 자유 텍스트는 **역인덱스(inverted index)** 로 토큰 검색에 대응한다. 타입을 보고 엔진이 인덱스 전략을 고른다. |
| **옵티마이저 통계** | 카디널리티 추정과 **히스토그램**은 값에 순서가 있어야 구간별로 만들 수 있다. `riskProfile`처럼 값이 몇 개뿐인 저카디널리티 범주값과 `transactionId`처럼 유일한 고카디널리티 식별자는 완전히 다른 조인 순서를 유도한다. |
| **파티셔닝** | **시간 파티셔닝은 datetime/date 타입이 있어야만 가능하다.** `timestamp`가 string이면 "2026년 3월 파티션만 읽기" 같은 파티션 프루닝을 못 하고 전체 스캔이 된다. Transaction처럼 수십억 행으로 자라는 엔티티에서 이 차이가 질의 성공/실패를 가른다. |
| **압축·인코딩** | 저카디널리티 범주값은 **딕셔너리 인코딩**, 정렬된 정수·시각은 **델타 인코딩**과 런-렝스 압축이 잘 먹는다. 같은 값을 string으로 두면 이 최적화가 전부 사라진다. |

즉 타입은 "어떤 질의가 가능한가"에 이어 **"그 질의가 실용적 시간 안에 끝나는가"** 까지 결정한다.

---

## 4. 타입은 문서이고 검증기이기도 하다

- **문서**: `term: integer (months)`라는 한 줄이 주석 여러 줄을 대신한다. 새 팀원, 데이터 분석가, 다운스트림 시스템이 값의 형태와 사용법을 스키마에서 바로 읽는다.
- **검증**: 적재 파이프라인이 타입을 검사하므로 `creditScore: "N/A"`, `amount: "1,250.00 USD"` 같은 오염된 값이 온톨로지에 들어오기 전에 걸러진다. 검증이 없으면 오염은 조용히 들어와 몇 달 뒤 리포트 이상으로 발견된다.
- **매핑 명세**: 소스 시스템이 코어뱅킹, 결제 프로세서, 신용평가사, 증권사로 나뉘어 있으므로 각 소스의 물리 타입을 온톨로지 타입으로 **캐스팅하는 규칙**이 명시되어야 한다. 타입 선언이 그 캐스팅 규칙을 요구하는 앵커가 된다.

---

## 5. 잘못 고른 타입이 만드는 실패 유형

| 실수 | 무엇이 깨지는가 | finance 예 |
|---|---|---|
| **숫자를 string으로** | 순서·범위·집계 전부 붕괴. 정렬이 사전순이 되어 `"1000" < "700"`, `SUM` 불가 | `creditScore`가 string이면 `> 700` 심사 규칙 자체를 쓸 수 없다 |
| **식별자를 integer로** | **선행 0 소실**(`00451` → `451`), 무의미한 산술이 허용되어 버그가 조용히 통과, 영문·하이픈 포함 값 적재 실패 | `accountNumber`, `loanId`는 integer로 두면 안 된다 |
| **금액을 float으로** | 표현 오차 누적, 원장 불일치, 반올림 결과가 실행 순서에 의존 | `SUM(amount)`가 실행마다 미세하게 달라져 감사 대조 실패 |
| **datetime을 date로** | **해상도 손실은 복구 불가능**. 시간 윈도우 질의가 원리적으로 불가 | 분 단위 사기 패턴 탐지 불가 (`timestamp`) |
| **열거형을 통제 없는 자유 문자열로** | 표기 불일치(`high` / `High` / `HIGH` / `hi`)로 **그룹핑과 필터가 조용히 누락** | `riskProfile='high'` 필터가 대문자 레코드를 놓쳐 컴플라이언스 리포트가 과소 집계 |

마지막 항목의 대안이 **열거형(enum) 또는 코드 테이블**이다. 허용 값 목록을 스키마에 못박거나 별도 코드 엔티티로 참조 무결성을 걸면, 타입이 열어 준 그룹핑 능력이 표기 흔들림에 무너지지 않는다. 순서가 필요한 등급(`riskProfile`)이라면 코드 테이블에 순위 컬럼을 함께 두는 것이 정석이다.

---

## 6. 타입은 나중에 바꾸기 어렵다

이것이 타입 선택을 "단순한 저장 형식 결정"으로 볼 수 없는 결정적 이유다.

- 이미 적재된 데이터 전체를 재해석해야 한다. 확장 방향(integer → decimal)은 대체로 안전하지만, 축소 방향(decimal → integer)이나 재해석(string → datetime)은 **값 손실과 파싱 실패**를 낳는다.
- 그 프로퍼티에 의존하는 **모든 질의·리포트·대시보드·알림 규칙**이 함께 깨진다. `timestamp`를 date에서 datetime으로 승격하려면 과거 데이터에 없던 시각 정보를 어디선가 복원해야 하는데, 대개 복원 불가다.
- 인덱스, 파티션, 캐시, 다운스트림 추출물(BI 모델, ML 피처)이 모두 재생성 대상이 된다.

즉 타입 변경은 스키마 수정이 아니라 **마이그레이션 이벤트**다. 그래서 모델링 단계에서 "이 프로퍼티로 어떤 질문을 할 것인가"를 먼저 나열하고, 그 질문 집합이 요구하는 최소 타입을 고르는 순서가 옳다.

---

## 7. 온톨로지 타입과 물리 저장 타입은 분리된다

온톨로지가 선언하는 것은 **의미론적 타입(semantic type)** 이다. 소스 시스템의 물리 타입은 다를 수 있다.

- 코어뱅킹 COBOL 레거시가 `balance`를 zoned decimal 문자열로 들고 있어도, 온톨로지는 `balance: decimal (USD)`로 선언한다.
- 결제 프로세서가 `timestamp`를 epoch 정수(밀리초)로 주더라도, 온톨로지는 `timestamp: datetime`이다.
- 신용평가사가 `creditScore`를 `"712"` 문자열로 주더라도, 온톨로지는 `creditScore: integer`다.

이 간극을 메우는 것이 **매핑 계층(mapping layer)** 이고, 캐스팅·정규화·단위 변환·타임존 표준화는 거기서 일어난다. 이 분리 덕에 소스 시스템이 교체되어도 온톨로지 계약(=질의 가능성)은 유지된다. 학습 경로가 말한 "온톨로지는 데이터베이스가 아니라 스키마"라는 문장의 실무적 의미가 바로 이것이다.

---

## 8. 표준에서는 어떻게 다루는가 (짧게)

- **RDF/OWL — `xsd:` 데이터타입**: XML Schema 데이터타입을 그대로 차용한다. 각 데이터타입은 **어휘 공간(lexical space)**, **값 공간(value space)**, 그리고 둘을 잇는 **사상(lexical-to-value mapping)** 의 3요소로 정의된다. 이 정의 방식이 이 카드의 요지와 정확히 맞물린다. `"1.0"`과 `"1.00"`은 어휘 공간에서는 다르지만 `xsd:decimal`의 값 공간에서는 같은 값이므로 비교가 성립한다. `xsd:decimal`의 값 공간은 "정수를 10의 거듭제곱으로 나눈 수"의 집합이라 10진 금액을 정확히 표현하고, `xsd:date`/`xsd:time`/`xsd:dateTime`은 타임존을 선택적으로 갖고 `xsd:dateTimeStamp`는 타임존을 필수로 요구한다. 타임존 없는 시각은 ±14시간 불확실성 때문에 **부분 순서(partially comparable)** 만 성립한다는 점까지 표준이 명시한다 — 즉 "타입이 어떤 비교를 보장하는가"가 표준 수준의 관심사다. 반대로 `xsd:float`/`xsd:double` 같은 이진 부동소수는 RDF에서 값 동등성과 반올림 문제를 일으켜 금액에는 부적합하다고 지적되어 왔다.
- **Property graph — GQL (ISO/IEC 39075:2024)**: `STRING`, `BOOLEAN`, `INT`, `DOUBLE`, `DATE`, `TIMESTAMP` 등 사전 정의 값 타입과 리스트·레코드 같은 구성 타입을 제공하고, 닫힌 스키마(closed graph)에서는 노드/에지 타입 정의 시 프로퍼티 타입을 **명시적으로 선언**한다. 여기에 **nullability**(MANDATORY / OPTIONAL)까지 타입 시스템의 일부로 다뤄, "값이 없을 수 있는가"도 질의 작성자에게 주는 계약에 포함된다. PG-Schema 같은 후속 연구도 프로퍼티 그래프에 이런 타입·제약 선언을 정형화하는 방향으로 진행됐다.

두 표준 계열 모두 공통점이 같다. **타입은 저장 형식 표기가 아니라, 값 공간·비교 가능성·연산 가능성을 규정하는 의미론적 선언으로 취급된다.**

---

## 한 줄 정리

프로퍼티 타입은 값의 그릇이 아니라 **질의 계약서**다. finance 온톨로지에서 `creditScore: integer`는 임계 심사를, `timestamp: datetime`은 분 단위 사기 탐지를, `balance/amount/principal: decimal`은 오차 없는 원장 집계를 각각 "가능하게 만든다". 반대로 잘못 고른 타입은 그 질문을 **영구히 불가능하게 만들고**, 되돌리려면 마이그레이션 이벤트를 치러야 한다.

---

## 참고 자료

- [XML Schema Datatypes in RDF and OWL (W3C)](https://www.w3.org/TR/swbp-xsch-datatypes/)
- [XSD Datatypes (W3C RDF WG wiki)](https://www.w3.org/2011/rdf-wg/wiki/XSD_Datatypes)
- [The Problem with XSD Binary Floating Point Datatypes in RDF](https://arxiv.org/pdf/2011.08077)
- [Datatypes — Ontotext Semantic Objects](https://platform.ontotext.com/semantic-objects/soml/datatypes.html)
- [Values and Types — ISO GQL (Ultipa Docs)](https://www.ultipa.com/docs/gql/values-and-types)
- [ISO/IEC 39075:2024 — GQL Standard for Property Graph Database Language](https://standards.iteh.ai/catalog/standards/iso/8b68feb3-7ba2-468a-8f9d-ee2e7cc205ab/iso-iec-39075-2024)
- [PG-Schema: Schemas for Property Graphs (ACM)](https://dl.acm.org/doi/10.1145/3589778)
