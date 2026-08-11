# `WITH` 절 — 질의 파이프라인의 경계

> **Q.** GQL 질의에서 `WITH` 절은 어떤 역할을 하는가?
>
> **A.** 매칭 결과를 집계·재구성해 다음 절로 넘기는 중간 단계다. 예시에서는 고객별로 `SUM(inv.currentValue)`와 `SUM(loan.principal)`을 계산해 `portfolio`, `debt` 변수로 넘긴다.

---

## 1. 한 문장으로

`WITH`는 **앞 절이 만든 행 집합(working table)을 받아 투영·집계·정렬·제한을 적용한 뒤, 그 결과만을 뒤 절로 넘기는 파이프라인 경계**다.

여기서 "그 결과만"이 핵심이다. `WITH`는 단순히 값을 계산하는 절이 아니라 **스코프를 다시 선언하는 절**이다. `WITH`에 나열하지 않은 변수는 그 지점부터 존재하지 않는다.

```
MATCH ──▶ [행 집합] ──▶ WITH ──▶ [재구성된 행 집합] ──▶ WHERE / MATCH / WITH ──▶ RETURN
                          ▲
                    여기가 경계선.
                    통과하지 못한 변수는 뒤에서 쓸 수 없다.
```

SQL에 익숙하다면 이렇게 보면 된다: **`WITH` = `SELECT` 목록 + `GROUP BY` + (뒤에 `WHERE`가 붙으면) `HAVING`을 한 절에 합친 것**. 그리고 서브질의를 중첩하는 대신 옆으로 늘어놓는 문법이다.

> ⚠️ **SQL의 `WITH`(CTE)와 이름만 같은 다른 것이다.** SQL의 `WITH`는 질의 앞머리에 이름 붙은 임시 결과를 선언하는 CTE고, Cypher/GQL 계열의 `WITH`는 질의 **중간**에 놓여 흐름을 통과시키는 파이프 단계다. 헷갈리기 쉬운 대표적인 false friend.

---

## 2. 카드의 예시를 한 줄씩 해부

학습 경로의 Complete Banking Model 섹션에 나오는 질의다. 투자 포트폴리오 평가액이 총 대출 원금을 넘는 고객을 찾는다.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment),
      (c)-[:has_loan]->(loan:Loan)
WITH c, SUM(inv.currentValue) AS portfolio, SUM(loan.principal) AS debt
WHERE portfolio > debt
RETURN c.name, portfolio, debt
```

| 단계 | 하는 일 | 통과하는 변수(컬럼) |
|---|---|---|
| `MATCH` | 고객–투자–대출 조합을 모두 펼친다 | `c`, `inv`, `loan` |
| `WITH` | `c`를 그룹 키로 삼아 두 개의 합계를 계산 | `c`, `portfolio`, `debt` — **`inv`, `loan`은 여기서 사라진다** |
| `WHERE` | 집계 **결과**를 비교해 행을 걸러낸다 (SQL의 `HAVING`) | `c`, `portfolio`, `debt` |
| `RETURN` | 최종 출력 | `c.name`, `portfolio`, `debt` |

`MATCH`가 낸 결과는 고객 1명당 여러 행(투자 × 대출 조합)이다. `WITH`가 이를 **고객 1명당 1행**으로 접어 넣고, 그 접힌 결과에 이름(`portfolio`, `debt`)을 붙여 뒤로 넘긴다. `WITH` 없이는 `WHERE portfolio > debt`라고 쓸 대상 자체가 존재하지 않는다.

> 📌 이 학습 경로가 "GQL"이라 부르는 문법은 openCypher 계열 표기다. ISO 표준 GQL에서는 이 `WITH`가 여러 절로 쪼개져 있다 — 8절에서 다룬다.

---

## 3. 규칙 ① 암묵적 GROUP BY: 집계 함수가 아닌 항목이 그룹 키가 된다

`WITH c, SUM(inv.currentValue) AS portfolio` 어디에도 `GROUP BY`가 없다. 그런데 왜 고객별 합계가 나오는가?

**규칙: `WITH`(그리고 `RETURN`)의 항목 중 집계 함수가 아닌 것들이 자동으로 그룹 키(grouping key)가 된다.**

```gql
WITH c, SUM(inv.currentValue) AS portfolio
--   ▲                ▲
--   집계 아님          집계 함수
--   → 그룹 키          → 각 그룹 안에서 계산
```

즉 위 줄은 SQL로 `SELECT c, SUM(inv.currentValue) AS portfolio ... GROUP BY c`와 같다. `GROUP BY`를 쓰지 않는 게 아니라, **적지 않아도 추론된다**.

이 규칙의 실전 함의는 "그룹 키를 늘리면 집계 단위가 잘게 쪼개진다"는 것이다.

```gql
-- (A) 고객별 합계 — 고객 1명당 1행
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, SUM(inv.currentValue) AS portfolio
RETURN c.name, portfolio

-- (B) 고객 × 종목별 합계 — inv.symbol을 그룹 키로 추가하면 집계 단위가 달라진다
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, inv.symbol AS symbol, SUM(inv.currentValue) AS bySymbol
RETURN c.name, symbol, bySymbol
```

(B)에서 `inv.symbol`을 무심코 "그냥 같이 보고 싶어서" 추가하면 집계 결과가 조용히 달라진다. **`WITH` 목록에 항목을 추가하는 것은 출력 컬럼을 추가하는 게 아니라 `GROUP BY`를 바꾸는 것**이라는 감각이 필요하다. 이것이 `WITH` 관련 버그의 최대 원인이다.

전체 합계(그룹 키 없음)를 원하면 집계 함수만 남긴다.

```gql
MATCH (:Customer)-[:has_loan]->(loan:Loan)
WHERE loan.status = 'active'
WITH SUM(loan.principal) AS bankExposure, COUNT(loan) AS loanCount, AVG(loan.apr) AS avgApr
RETURN bankExposure, loanCount, avgApr   -- 정확히 1행
```

---

## 4. 규칙 ② 변수 가시성: `WITH`에 없으면 스코프에서 사라진다

`WITH`는 **블로킹(blocking)** 절이다. 통과 목록을 직접 적어야 하고, 적지 않은 것은 버려진다.

```gql
MATCH (c:Customer)-[:owns]->(a:Account)-[:has_transaction]->(t:Transaction)
WITH c, SUM(t.amount) AS spend
RETURN c.name, spend, a.accountNumber   -- ❌ 오류: a는 스코프에 없음
```

계좌 `a`는 `WITH` 목록에 없으므로 `RETURN` 시점에는 존재하지 않는다. 에러 메시지는 보통 `Variable 'a' not defined` 같은 형태로 나오는데, "분명히 위에서 `MATCH`했는데?"라며 당황하기 쉬운 지점이다.

해결책은 세 가지다.

**(1) 그룹 키에 포함시킨다** — 단, 집계 단위가 계좌별로 바뀐다는 점을 의도해야 한다.

```gql
WITH c, a, SUM(t.amount) AS spend      -- 고객×계좌별 합계
RETURN c.name, a.accountNumber, spend
```

**(2) `COLLECT`로 리스트에 담아 넘긴다** — 집계 단위는 유지하면서 세부 정보를 살리고 싶을 때.

```gql
MATCH (c:Customer)-[:owns]->(a:Account)-[:has_transaction]->(t:Transaction)
WITH c,
     SUM(t.amount) AS spend,
     COLLECT(DISTINCT a.accountNumber) AS accountNumbers   -- 계좌번호를 리스트로 보존
RETURN c.name, spend, accountNumbers
```

**(3) 필요한 속성만 미리 뽑아 넘긴다** — 노드 전체가 아니라 스칼라 값만 남긴다.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, SUM(inv.currentValue) AS portfolio, COLLECT(inv.symbol) AS symbols
WHERE portfolio > 100000
RETURN c.name, portfolio, symbols
```

> 💡 `COLLECT`는 "집계 때문에 잃어버릴 세부 정보를 리스트라는 가방에 넣어 검문소를 통과시키는" 도구로 기억하면 좋다. 뒤에서 다시 행으로 펼쳐야 하면 `UNWIND`를 쓴다.

---

## 5. 규칙 ③ `WHERE`의 위치가 의미를 바꾼다

같은 `WHERE`인데 **어디에 놓느냐**에 따라 전혀 다른 일을 한다.

| 위치 | 대상 | 집계와의 순서 | SQL 대응 |
|---|---|---|---|
| `MATCH ... WHERE` | 매칭된 **개별 행** | 집계 **전** | `WHERE` |
| `WITH ... WHERE` | `WITH`가 만든 **집계 결과 행** | 집계 **후** | `HAVING` |

```gql
MATCH (c:Customer)-[:has_loan]->(loan:Loan)
WHERE loan.status = 'active'          -- ① 행 단위 필터(집계 전): 해지된 대출을 합계에서 제외
WITH c, SUM(loan.principal) AS debt
WHERE debt > 100000                   -- ② 집계 결과 필터(= HAVING): 총 부채 10만 초과 고객만
RETURN c.name, debt
ORDER BY debt DESC
```

①과 ②를 뒤바꾸면 결과가 완전히 달라진다.

- ①을 ② 자리로 옮기면? `loan`이 이미 스코프에서 사라져 **에러**가 난다.
- ②를 ① 자리로 옮기면? `WHERE loan.principal > 100000`이 되어 "**개별 대출**이 10만을 넘는 건"만 남는다. 5만짜리 대출 3건을 가진 고객(총 15만)은 탈락한다.

**"집계에 들어갈 재료를 고르는 필터는 `MATCH` 쪽, 집계 결과를 고르는 필터는 `WITH` 뒤"** 로 정리하면 된다.

`WITH ... WHERE`는 집계가 없을 때도 유용하다. 이 경우엔 단순히 "계산해서 이름 붙인 값으로 필터"하는 용도다.

```gql
-- 평가손익을 계산해 그 별칭으로 필터
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, inv, inv.currentValue - inv.purchasePrice AS gain
WHERE gain < 0                        -- 별칭으로 바로 비교 가능
RETURN c.name, inv.symbol, gain
ORDER BY gain ASC
```

---

## 6. 규칙 ④ 별칭 재사용 — 왜 뒤 절에서 `portfolio`를 쓸 수 있는가

`WITH ... AS portfolio`는 계산 결과에 **이름을 붙여 새로운 컬럼으로 승격**시킨다. 승격된 뒤에는 다른 컬럼과 완전히 동등하게 취급되므로, 뒤 절에서 자유롭게 필터·정렬·재계산에 쓸 수 있다.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, SUM(inv.currentValue) AS portfolio      -- ① 이름 부여
WHERE portfolio > 50000                         -- ② 필터에 사용
WITH c, portfolio, portfolio * 0.01 AS annualFee -- ③ 별칭으로 재계산
ORDER BY annualFee DESC                         -- ④ 정렬에 사용
RETURN c.name, portfolio, annualFee
```

이것이 SQL에 비해 편한 지점이다. SQL에서는 `SELECT`에서 만든 별칭을 같은 레벨의 `WHERE`에서 쓸 수 없고(대부분의 엔진), 서브질의나 CTE로 한 겹 감싸야 한다. `WITH`는 **그 "한 겹 감싸기"를 절 하나로 대신한다**. 파이프라인이 이미 새 단계로 넘어간 상태이므로 별칭이 정식 컬럼이기 때문이다.

같은 이유로 **집계 함수를 다시 집계**할 수도 있다.

```gql
MATCH (c:Customer)-[:owns]->(a:Account)-[:has_transaction]->(t:Transaction)
WITH a, SUM(t.amount) AS accountVolume     -- 1단: 계좌별 거래 총액
WITH AVG(accountVolume) AS avgVolume,      -- 2단: 그 총액들의 평균 (집계의 집계)
     MAX(accountVolume) AS maxVolume
RETURN avgVolume, maxVolume
```

`SUM(SUM(...))`처럼 중첩해서는 쓸 수 없다. `WITH`로 단계를 끊어야 한다.

---

## 7. 대표 패턴 다섯 가지

### 패턴 1 — `WITH ... ORDER BY ... LIMIT`: 상위 N개만 다음 단계로 (퍼널 축소)

`WITH`에는 `ORDER BY`, `SKIP`, `LIMIT`을 붙일 수 있다. 최종 출력이 아니라 **파이프라인 중간에서 후보를 잘라내는** 용도다. 뒤에 오는 무거운 `MATCH`가 처리할 행 수를 극적으로 줄인다.

고위험 고객의 대출 중 원금 상위 5건과, 그 대출의 상환 계좌를 함께 보는 질의:

```gql
MATCH (c:Customer)-[:has_loan]->(loan:Loan)
WHERE c.riskProfile = 'high' AND loan.status = 'active'
WITH c, loan
ORDER BY loan.principal DESC
LIMIT 5                                      -- ★ 여기서 5행으로 축소
MATCH (a:Account)-[:funds]->(loan)           -- 5행에 대해서만 추가 탐색
RETURN c.name, c.creditScore, loan.loanId, loan.principal, a.accountNumber
ORDER BY loan.principal DESC
```

`LIMIT`을 `RETURN` 뒤에 두면 `funds` 탐색을 **모든** 고위험 대출에 대해 수행한 뒤 5행만 남긴다. `WITH` 단계에서 자르면 탐색 자체가 5건으로 줄어든다. 결과는 같지만 비용이 다르다.

> ⚠️ `LIMIT`은 반드시 의도한 `ORDER BY` **직후**에 와야 한다. 사이에 다른 절이 끼면 정렬 순서가 보장되지 않을 수 있다.

그룹별 상위 N("각 고객의 최대 대출 1건")은 `COLLECT` + 리스트 인덱싱으로 푼다.

```gql
MATCH (c:Customer)-[:has_loan]->(loan:Loan)
WITH c, loan
ORDER BY loan.principal DESC
WITH c, COLLECT(loan)[0] AS biggestLoan     -- 정렬된 순서대로 담기고, 첫 원소가 최대
RETURN c.name, biggestLoan.loanId, biggestLoan.principal
```

### 패턴 2 — `WITH DISTINCT`: 카티션 곱 중복 제거

여러 관계를 함께 탐색하면 경로 조합이 곱해진다. 노드 목록만 필요할 때는 `WITH DISTINCT`로 접는다.

```gql
-- ❌ 거래가 200건인 계좌를 가진 고객이 200번 등장
MATCH (c:Customer)-[:owns]->(:Account)-[:has_transaction]->(:Transaction)
RETURN c.name

-- ✅ 고객 단위로 중복 제거
MATCH (c:Customer)-[:owns]->(:Account)-[:has_transaction]->(:Transaction)
WITH DISTINCT c
RETURN c.name, c.riskProfile
```

**집계와 결합하면 훨씬 중요해진다.** 카드의 예시 질의는 실은 이 함정을 품고 있다.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment),
      (c)-[:has_loan]->(loan:Loan)
WITH c, SUM(inv.currentValue) AS portfolio, SUM(loan.principal) AS debt
```

`MATCH`의 두 패턴이 `c`만 공유하므로, 투자 3건 × 대출 1건 = **3행**이 만들어진다. 그 3행 위에서 `SUM`을 돌리면:

| 실제 데이터 | `MATCH` 결과 | `SUM(inv.currentValue)` | `SUM(loan.principal)` |
|---|---|---|---|
| 투자 3건(40+30+30=100), 대출 1건(90) | 3행 | 100 ✅ (대출 1건 → 배수 1) | 90 × 3 = **270** ❌ |

진짜 비교는 `100 > 90` → 참이지만, 질의는 `100 > 270` → 거짓으로 판정해 **이 고객을 결과에서 누락시킨다**. 각 합계가 상대편 건수만큼 부풀려지는데 그 배수가 서로 다르기 때문에, 부등호 방향까지 뒤집힐 수 있다.

`WITH DISTINCT`로는 이걸 못 고친다(값이 같은 서로 다른 투자 건이 합쳐져 버린다). 정답은 **집계를 단계로 분리**하는 것이다 → 패턴 3.

한편 "몇 개인지" 세는 것뿐이라면 집계 함수 안의 `DISTINCT`로 충분하다.

```gql
MATCH (c:Customer)-[:owns]->(a:Account)-[:has_transaction]->(t:Transaction)
WITH c, COUNT(DISTINCT a) AS accountCount, COUNT(t) AS txCount
RETURN c.name, accountCount, txCount
```

### 패턴 3 — 여러 `WITH`를 연달아 쓰는 다단 파이프라인

`WITH`는 몇 번이든 이어 쓸 수 있고, 사이에 `MATCH`를 끼울 수 있다. 패턴 2의 카티션 곱 문제를 이렇게 해결한다.

```gql
-- ✅ 포트폴리오와 부채를 각각 별도 단계에서 집계
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, SUM(inv.currentValue) AS portfolio          -- 1단: 투자만으로 집계 (대출 미개입)
MATCH (c)-[:has_loan]->(loan:Loan)                  --      c를 이어받아 대출 탐색
WITH c, portfolio, SUM(loan.principal) AS debt      -- 2단: 대출만으로 집계
WHERE portfolio > debt                              -- 3단: 집계 결과 비교
RETURN c.name, portfolio, debt
ORDER BY portfolio - debt DESC
```

1단에서 이미 고객 1행으로 접혔으므로, 2단의 `MATCH`는 고객당 대출 건수만큼만 행을 만든다. 곱셈이 발생하지 않는다.

> 2단 `WITH`의 그룹 키는 `c`와 `portfolio` 둘이다. `portfolio`는 `c`에 종속된 값이므로 그룹을 더 쪼개지 않지만, **집계가 아닌 항목은 반드시 나열해야 통과한다**는 규칙 때문에 적어줘야 한다.

투자만 있고 대출은 없는 고객까지 포함하려면 두 번째 `MATCH`를 `OPTIONAL MATCH`로 바꾸고 `COALESCE(SUM(loan.principal), 0)`로 처리한다.

3단 이상도 자연스럽다 — 계좌별 월간 지출을 집계하고, 과소비 월을 세고, 고객 단위로 다시 요약하는 질의:

```gql
MATCH (c:Customer)-[:owns]->(a:Account)-[:has_transaction]->(t:Transaction)
WHERE t.type = 'debit'                                    -- ① 행 필터: 출금만
WITH c, a,
     t.timestamp.year  AS yr,
     t.timestamp.month AS mo,
     SUM(t.amount)     AS monthlySpend                    -- ② 계좌×월별 합계
WITH c, a, monthlySpend, yr, mo
WHERE monthlySpend > 5000                                 -- ③ HAVING: 과소비 월만
WITH c, a,
     COUNT(*)          AS heavyMonths,                    -- ④ 계좌별 재집계
     MAX(monthlySpend) AS peakSpend
WITH c,
     SUM(heavyMonths)  AS totalHeavyMonths,               -- ⑤ 고객별 재집계
     MAX(peakSpend)    AS worstMonth
ORDER BY worstMonth DESC
LIMIT 10                                                  -- ⑥ 상위 10명
RETURN c.name, c.riskProfile, totalHeavyMonths, worstMonth
```

각 `WITH`가 "여기까지가 한 단계"라는 눈에 보이는 구분선이 되어, 질의를 위에서 아래로 읽기만 해도 데이터 흐름을 따라갈 수 있다. 서브질의를 5겹 중첩한 SQL과 비교하면 가독성 차이가 크다.

### 패턴 4 — 비율·파생 지표 계산

`WITH`는 집계값끼리 조합해 새 지표를 만드는 자리이기도 하다.

```gql
-- 부채 대비 자산 비율(leverage)로 고객 건전성 순위
MATCH (c:Customer)-[:holds]->(inv:Investment)
WITH c, SUM(inv.currentValue) AS portfolio
MATCH (c)-[:has_loan]->(loan:Loan)
WHERE loan.status = 'active'
WITH c, portfolio, SUM(loan.principal) AS debt, SUM(loan.principal * loan.apr / 100) AS annualInterest
WHERE debt > 0
WITH c, portfolio, debt, annualInterest,
     portfolio / debt AS coverageRatio                    -- 파생 지표
WHERE coverageRatio < 1.2                                 -- 그 지표로 다시 필터
RETURN c.name, c.creditScore, portfolio, debt, annualInterest, coverageRatio
ORDER BY coverageRatio ASC
```

학습 경로가 말한 "고객의 투자 수익이 대출 비용을 넘는가?"(`Customer → Investment (currentValue)` vs `Customer → Loan (principal × apr)`)를 그대로 구현한 형태다.

### 패턴 5 — 중간 결과를 다음 탐색의 시작점으로

`WITH`로 좁힌 노드 집합을 뒤 `MATCH`의 앵커로 쓰면, 그래프 탐색 범위 자체가 줄어든다.

```gql
-- 부채가 큰 상위 3명의 계좌에서 발생한 대형 거래를 감사
MATCH (c:Customer)-[:has_loan]->(loan:Loan)
WITH c, SUM(loan.principal) AS debt
ORDER BY debt DESC
LIMIT 3                                            -- 고객 3명으로 축소
MATCH (c)-[:owns]->(a:Account)-[:has_transaction]->(t:Transaction)
WHERE t.amount > 10000
RETURN c.name, debt, a.accountNumber, t.transactionId, t.amount, t.timestamp
ORDER BY t.amount DESC
```

---

## 8. SQL 사용자를 위한 대응표

| Cypher/GQL 표기 | SQL 대응 | 메모 |
|---|---|---|
| `MATCH (a)-[:r]->(b)` | `FROM a JOIN b ON ...` | 관계가 조인 조건 역할 |
| `MATCH ... WHERE x > 0` | `WHERE x > 0` | 행 단위, 집계 전 |
| `WITH c, SUM(x) AS s` | `SELECT c, SUM(x) AS s ... GROUP BY c` | **`GROUP BY c`가 암묵적** |
| `WITH ... WHERE s > 0` | `HAVING s > 0` | 집계 후 |
| `WITH c, x AS y` (집계 없음) | 서브질의/CTE의 `SELECT` 목록 | 투영 + 별칭 부여 |
| `WITH ... ORDER BY ... LIMIT n` | `(SELECT ... ORDER BY ... LIMIT n)` 서브질의 | 중간 단계의 top-k |
| `WITH DISTINCT c` | `SELECT DISTINCT c` | 행 중복 제거 |
| `COUNT(DISTINCT a)` | `COUNT(DISTINCT a)` | 동일 |
| `WITH` 여러 개 연달아 | 서브질의 중첩 또는 CTE 체인 | 중첩 대신 선형 배치 |
| `COLLECT(x) AS xs` | `ARRAY_AGG(x)` / `STRING_AGG` | 세부 정보 보존 |
| `UNWIND xs AS x` | `UNNEST(xs)` / `CROSS JOIN LATERAL` | 리스트 → 행 |

**핵심 감각 차이**: SQL은 하나의 `SELECT`가 논리적 실행 순서(`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`)를 내부에 감추고 있고, 복잡해지면 바깥으로 중첩된다. Cypher/GQL은 그 순서를 **절의 나열 순서로 평평하게 펼쳐** 놓았다. `WITH`가 그 이음매다.

---

## 9. 표준 GQL(ISO/IEC 39075)에서는 `WITH`가 없다

여기서 용어를 정확히 정리해 둘 필요가 있다. **`WITH`는 openCypher(Neo4j Cypher) 계열의 절이고, 2024년 제정된 ISO/IEC 39075 표준 GQL에는 `WITH`라는 절이 없다.** 표준 GQL은 `WITH`가 겸하던 역할을 여러 개의 독립 문장으로 분리했다.

| Cypher `WITH`가 하던 일 | 표준 GQL의 해당 문장 | 차이점 |
|---|---|---|
| 새 값 계산 + 별칭 부여 | `LET <var> = <expr>, ...` | **비파괴적** — 컬럼을 추가할 뿐, 기존 변수는 모두 스코프에 남는다 |
| 집계 후 행 필터(`HAVING`) | `FILTER [WHERE] <predicate>` | 독립 문장. 파이프라인 어디에나 놓을 수 있다 |
| 집계 + 그룹핑 | `RETURN ... GROUP BY <var>, ...` | **`GROUP BY`를 명시**해야 한다 (암묵 추론에 의존하지 않음) |
| 정렬/건너뛰기/제한 | `ORDER BY` / `OFFSET` / `LIMIT` | 각각 독립 문장이거나 `RETURN`의 후행 절 |
| 중복 제거 | `RETURN DISTINCT` | — |
| 단계를 이어붙이는 파이프 경계 | **`NEXT`** (linear composition) | 앞 문장의 결과 테이블을 뒤 문장의 입력으로 넘긴다 |

가장 중요한 두 가지 차이:

1. **`LET`은 블로킹이 아니다.** Cypher `WITH`는 통과 목록을 다 적어야 하고 안 적은 변수를 버리지만, `LET`은 워킹 테이블에 컬럼을 하나 붙이는 것뿐이어서 기존 변수가 그대로 살아 있다. 즉 4절의 "스코프 소실" 함정이 `LET`에는 없다. 대신 스코프를 **일부러 좁히려면** `RETURN`으로 투영해야 한다.
2. **암묵적 GROUP BY가 없다.** 표준 GQL은 `RETURN c, SUM(x) AS s GROUP BY c`처럼 그룹 키를 명시한다. 3절에서 본 "항목을 하나 추가했더니 집계 단위가 조용히 바뀌는" 사고가 구조적으로 덜 일어난다.

카드의 예시 질의를 표준 GQL 스타일로 옮기면 대략 이렇게 된다.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment)
RETURN c, SUM(inv.currentValue) AS portfolio
  GROUP BY c
NEXT
MATCH (c)-[:has_loan]->(loan:Loan)
RETURN c, portfolio, SUM(loan.principal) AS debt
  GROUP BY c, portfolio
NEXT
FILTER portfolio > debt
RETURN c.name AS name, portfolio, debt
  ORDER BY portfolio - debt DESC
  LIMIT 10
```

`WITH` 한 줄이 `RETURN ... GROUP BY` + `NEXT` + `FILTER`로 풀어헤쳐진 모습이다. 파이프라인 경계는 이제 `NEXT`가 명시적으로 표시한다.

집계 없이 계산만 하는 경우라면 `LET`이 훨씬 가볍다.

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment)
LET gain = inv.currentValue - inv.purchasePrice     -- c, inv 모두 스코프 유지
FILTER gain < 0
RETURN c.name AS name, inv.symbol AS symbol, gain
  ORDER BY gain ASC
```

> ⚠️ **실무 주의**: 표준 GQL 구현체는 아직 제품별 지원 범위가 다르다. Neo4j는 Cypher의 `WITH`를 계속 쓰고 GQL 호환을 점진 도입 중이며, Microsoft Fabric graph는 `MATCH`/`LET`/`FILTER`/`ORDER BY`/`LIMIT`/`RETURN ... GROUP BY` 조합을 지원하지만 일부 집합 연산은 미지원, Google Spanner/BigQuery graph는 `NEXT` 기반 선형 합성을 지원한다. **면접이나 시험에서는 "`WITH`는 Cypher 계열, 표준 GQL에서는 `LET`/`FILTER`/`RETURN ... GROUP BY`/`NEXT`로 나뉜다"까지 말할 수 있으면 충분하다.**

---

## 10. 체크리스트 — `WITH`를 쓸 때 스스로에게 묻기

- [ ] `WITH` 목록에 넣은 **집계 아닌 항목**이 모두 의도한 그룹 키인가? (하나만 더 넣어도 집계 단위가 바뀐다)
- [ ] 뒤 절에서 쓸 변수를 **전부** 나열했는가? 아니면 `COLLECT`로 담아 넘겨야 하는가?
- [ ] 이 `WHERE`는 집계 **전**(`MATCH` 뒤)에 있어야 하나, **후**(`WITH` 뒤)에 있어야 하나?
- [ ] 여러 관계를 한 `MATCH`에서 매칭하고 집계하는가? → **카티션 곱으로 합계가 부풀려질 수 있다.** 단계를 나눠라
- [ ] `LIMIT`을 `RETURN` 뒤가 아니라 `WITH` 단계에 두면 뒤 탐색 비용을 줄일 수 있나?
- [ ] `LIMIT`이 의도한 `ORDER BY` 직후에 붙어 있는가?

---

## 11. 한 문장 정리

`WITH`는 **파이프라인 경계**다 — 앞 절의 행 집합을 받아 투영·집계·정렬·제한을 적용하고, 나열한 변수만 뒤 절로 통과시킨다. 집계 아닌 항목은 암묵적 그룹 키가 되고, 뒤에 붙는 `WHERE`는 SQL의 `HAVING`이 된다. 표준 GQL(ISO/IEC 39075)에서는 이 역할이 `LET`·`FILTER`·`RETURN ... GROUP BY`·`NEXT`로 나뉘어 있다.

---

## 참고 자료

- [ISO/IEC 39075:2024 — Information technology, Database languages, GQL](https://www.iso.org/standard/76120.html)
- [GQL Language Guide for graph in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/graph/gql-language-guide) — `LET`/`FILTER`/`ORDER BY`/`LIMIT`/`RETURN ... GROUP BY` 문장별 문법과 워킹 테이블 흐름 예시
- [Linear Composition in GQL — gql.net](https://gql.net/linear-composition-in-gql/) — `NEXT`로 선형 합성하는 방식
- [GQL query statements — Google Cloud Spanner](https://docs.cloud.google.com/spanner/docs/reference/standard-sql/graph-query-statements) — `NEXT`, `LET` 문장 정의
- [GQL vs. Cypher: What the New ISO Standard Brings to the Table — NebulaGraph](https://nebula-graph.io/posts/gql-vs.-cypher-what-the-new-iso-standard-brings-to-the-table) — Cypher `WITH`와 GQL `LET`의 블로킹 여부 비교
- [Creating the GQL database language standard — Neo4j](https://neo4j.com/blog/cypher-and-gql/gql-database-language-standard/)
- 학습 경로 원문: `Banking & Finance / Complete Banking Model` 섹션의 GQL query example
