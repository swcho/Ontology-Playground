# 센서 이상과 품질 실패를 상관 분석하는 GQL 쿼리

**Q.** 센서 이상과 품질 실패를 상관 분석하는 GQL 쿼리는?

**A.**

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

---

## 1. 이 쿼리가 답하려는 질문

Smart Manufacturing 학습 경로의 **Complete Factory Model**(3단계) 마지막에 나오는 예제다.
경로 첫 문서에서 던진 질문이 여기서 회수된다.

> **"Which machines with abnormal sensor readings produced parts that failed quality checks last week?"**
> (비정상 센서 값을 보인 기계 중, 품질 검사에 실패한 부품을 생산한 기계는?)

이 질문 하나가 **IoT 텔레메트리 + 생산 추적 + 부품 이력 + 검사 기록** 네 영역을 가로지른다.
완성된 5-엔티티 온톨로지에서는 이것이 그래프 경로 하나로 떨어진다.

```
Sensor ──monitors──▶ Machine ──has_part──▶ Part ◀──inspects── QualityCheck
 (이상)                                                          (실패)
```

원문의 표에도 이 경로가 그대로 적혀 있다.

| Question | Graph path |
|---|---|
| Which sensors were abnormal when defective parts were produced? | `Sensor → Machine → Part ← Quality-Check (passed=false)` |

---

## 2. MATCH 절 — 경로 패턴 뜯어보기

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
```

MATCH는 **그래프에서 이 모양과 똑같이 생긴 부분그래프를 전부 찾아라**는 뜻이다.
`(변수:라벨)`은 노드, `-[:타입]->`는 방향 있는 엣지다.

### 2.1 노드 4개

| 변수 | 라벨 | 역할 | 이 쿼리에서 쓰는 속성 |
|---|---|---|---|
| `s` | `Sensor` | 이상 징후의 출처 | `lastReading`, `threshold`, `type` |
| `m` | `Machine` | 상관 분석의 **중심축** | `name` |
| `p` | `Part` | 센서와 검사를 이어주는 다리 | `name` |
| `qc` | `QualityCheck` | 실패 사실의 출처 | `passed`, `defectCode` |

> **라벨 표기 주의:** 온톨로지 문서상의 엔티티 이름은 `Quality-Check`(하이픈)지만,
> 쿼리에서는 `:QualityCheck`로 쓴다. 대부분의 그래프 질의어에서 라벨은 식별자 토큰이라
> 하이픈을 쓸 수 없기 때문이다. 엔티티 이름과 라벨 문자열을 매핑하는 규칙이 있다는 점을 기억해 두자.

### 2.2 관계 3개 — 5개 중 어떤 것을 썼나

이 온톨로지의 관계는 총 5개다. 이 쿼리는 그중 **3개를 쓰고 2개를 건너뛴다.**

| # | 관계 | 방향 | 카디널리티 | 이 쿼리에서 |
|---|---|---|---|---|
| 1 | `monitors` | `Sensor → Machine` | many-to-one | ✅ 사용 |
| 2 | `assigned_to` | `Work-Order → Machine` | many-to-one | ❌ 미사용 |
| 3 | `produces` | `Work-Order → Part` | one-to-many | ❌ 미사용 |
| 4 | `has_part` | `Machine → Part` | one-to-many | ✅ 사용 |
| 5 | `inspects` | `QualityCheck → Part` | many-to-one | ✅ 사용 |

**`monitors` — 화살표가 센서에서 기계로 향한다**

1단계 문서가 방향을 못 박는다.

> The direction matters: **sensors monitor machines**, not the other way around.

many-to-one이므로 기계 한 대에 온도·진동·압력 센서가 여러 개 매달린다.
따라서 `s`가 여러 개면 같은 `m`에 대해 **행이 센서 수만큼 늘어난다**(부분그래프 매칭이므로 조합이 전개된다).

**`has_part` — 출력 관점의 지름길**

2단계 문서는 `has_part`를 "A machine produces parts (the **output perspective**)"라고 설명한다.
정석 생산 체인은 `Machine ← Work-Order → Part`로 작업지시라는 **이벤트 엔티티**를 거치지만,
`has_part`는 그 2홉을 1홉으로 미리 요약해 둔 관계다.
이 쿼리가 `assigned_to`와 `produces`를 안 쓰는 이유가 바로 이것이다. → 5장에서 다시 다룬다.

**`inspects` — 유일하게 역방향으로 걷는 엣지**

`<-[:inspects]-`의 화살표가 왼쪽을 향한다. 관계 자체는 `QualityCheck → Part`로 정의돼 있는데,
쿼리는 `Part`에 도착한 상태에서 **"이 부품을 검사한 검사 기록들"** 로 거슬러 올라가야 하기 때문이다.

> 그래프 질의에서 **저장 방향과 탐색 방향은 별개**다. 엣지 방향은 의미(누가 누구를 검사했나)를 고정하고,
> 탐색은 그 엣지를 어느 쪽으로든 통과할 수 있다. 원문이 말하는 **feedback loop**
> (`Quality-Check → Part → Work-Order → Machine`)가 성립하는 것도 이 역방향 순회 덕분이다.

many-to-one이라 한 부품이 여러 번 검사될 수 있다(초기 검사 + 재작업 후 재검사).
이 역시 행 수를 늘리는 요인이다.

### 2.3 패턴의 모양 — "V자 조인"

경로를 그려 보면 화살표가 `Part`에서 마주친다.

```
   s ──▶ m ──▶ p ◀── qc
  이상            실패
   └── 텔레메트리 ──┘└─ 품질 ─┘
```

`Part`가 **양쪽에서 들어오는 정보가 만나는 접점**이다.
왼쪽 절반은 "이 기계 상태가 이상했다", 오른쪽 절반은 "이 기계가 만든 부품이 불합격했다".
두 사실을 잇는 것이 `Machine → Part` 한 홉이다.

---

## 3. WHERE 절 — 독립된 두 필터의 교집합

```gql
WHERE s.lastReading > s.threshold AND qc.passed = false
```

### 3.1 `s.lastReading > s.threshold` — 이상 판정

1단계 문서의 `threshold` 설계 의도가 그대로 조건이 된다.

> The `threshold` property defines the alert boundary. When `lastReading` exceeds `threshold`, the system triggers an alarm.

여기서 눈여겨볼 점: **양변이 모두 같은 노드의 속성**이다.
`s.threshold`가 상수 리터럴이 아니라 센서 자신이 들고 있는 값이므로,
온도 센서는 85.0, 진동 센서는 4.5처럼 **센서마다 다른 기준으로 동시에 판정**된다.
하드코딩된 `WHERE s.lastReading > 85`였다면 센서 종류마다 쿼리를 따로 짜야 했을 것이다.

> 이것이 온톨로지 설계의 이득이다. **판정 기준을 데이터로 끌어올리면 쿼리가 종류에 무관해진다.**

### 3.2 `qc.passed = false` — 실패 판정

3단계 문서는 `passed`를 "the critical property — it determines whether a part ships or gets reworked"라고 부른다.
불리언이라 애매한 구간이 없다. 원문의 key takeaway 5번 그대로,
**boolean 속성은 워크플로에 명확한 결정 지점을 만든다.**

### 3.3 `AND`가 핵심인 이유

두 조건은 **서로 다른 노드**에, **서로 다른 시스템 출신 데이터**에 걸린다.

| 조건 | 걸리는 노드 | 원래 데이터 출처 |
|---|---|---|
| `lastReading > threshold` | `s` (Sensor) | IoT 텔레메트리 |
| `passed = false` | `qc` (QualityCheck) | 품질 관리 DB |

각각 따로 실행하면 이미 존재하는 대시보드와 다를 게 없다.

- 센서 조건만 → **알람 목록**. "지금 이상한 기계"만 나온다. 예지보전 화면.
- 품질 조건만 → **불량 리포트**. "불합격한 부품"만 나온다. QC 화면.

`AND`로 묶는 순간 질문이 바뀐다.

> **"이상 신호와 불량이 같은 기계 위에서 동시에 나타난 조합은 무엇인가?"**

즉 `AND`는 필터를 강화하는 장치가 아니라 **두 도메인의 교집합을 정의하는 장치**다.
이 교집합이야말로 근본 원인 분석(root cause analysis)의 출발선이다.
그리고 이 교집합을 만들어 주는 것이 MATCH의 경로다 — 두 조건이 `m`이라는 **같은 기계**를
공유하도록 강제하기 때문에 무관한 센서와 무관한 불량이 짝지어지지 않는다.

---

## 4. RETURN 절 — 왜 하필 이 5개 필드인가

```gql
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

상관 분석 결과 테이블은 읽는 사람이 **바로 행동할 수 있어야** 쓸모가 있다.
5개 필드는 각각 "어디서 / 무엇이 / 얼마나 / 무엇에 / 어떻게" 를 담당한다.

| 필드 | 질문 | 왜 필요한가 |
|---|---|---|
| `m.name` | **어디서?** | 상관의 축이자 조치 대상. `machineId` 대신 `name`을 쓰는 건 현장 작업자가 읽는 표이기 때문 |
| `s.type` | **무엇이?** | temperature / vibration / pressure 중 무엇이 튀었나. 고장 유형을 좁힌다 (진동↑ → 베어링·정렬, 온도↑ → 냉각·윤활) |
| `s.lastReading` | **얼마나?** | 이상의 **정도**. 임계 바로 위인지 한참 위인지에 따라 긴급도가 갈린다 |
| `p.name` | **무엇에?** | 영향받은 산출물. 격리·회수 범위를 정하고, 특정 부품에만 몰렸는지 확인 |
| `qc.defectCode` | **어떻게?** | 불량의 **종류**. 원문대로 "categorizes failures for root cause analysis" |

### 설계 원칙 두 가지

**(1) 이상의 종류와 불량의 종류를 나란히 놓는다.**
`s.type`(입력 측 이상 유형)과 `qc.defectCode`(출력 측 불량 유형)를 한 행에 두면
"진동 이상 → 치수 불량(DIM-XX)", "온도 이상 → 표면 결함(SURF-XX)" 같은 **패턴**이 눈에 보인다.
이 두 컬럼이 사실상 상관 분석의 본체다.

**(2) 판정 근거를 같이 내보낸다.**
`s.lastReading`은 WHERE에서 이미 필터에 쓴 값인데도 RETURN에 다시 등장한다.
필터를 통과했다는 사실(boolean)만으로는 부족하고, **얼마나 벗어났는지**가 있어야 우선순위를 매길 수 있기 때문이다.
반면 `qc.passed`는 RETURN에 없다 — 어차피 전부 `false`라서 정보량이 0이다.
대신 정보량이 있는 `defectCode`를 내보낸다. **WHERE로 고정된 값은 빼고, 변하는 값만 반환한다.**

---

## 5. 이 한 줄이 대체하는 것 — 다중 시스템 조인

시나리오 문서는 데이터 출처를 이렇게 밝힌다.

> Data flows from **IoT sensors**, **MES (Manufacturing Execution Systems)**, **ERP platforms**, and **quality management databases**.

온톨로지가 없다면 같은 답을 얻기 위해 이런 과정을 거쳐야 한다.

| # | 시스템 | 하는 일 | 현실의 장애물 |
|---|---|---|---|
| 1 | IoT 히스토리안 (시계열 DB) | 임계 초과 센서·기계 추출 | 태그 이름이 `TT_1042_PV` 같은 계측 코드. 자산 마스터와 별도 매핑 필요 |
| 2 | MES | 그 기계의 작업지시·생산 부품 조회 | 기계 키가 `EQ_CNC01`, 시계열 태그와 다름 |
| 3 | 품질 DB (LIMS/QMS) | 그 부품들의 검사 결과 조회 | 부품 키가 로트/시리얼 단위. MES 키와 또 다름 |
| 4 | 사람 / 스프레드시트 | 세 결과를 엑셀에서 VLOOKUP | 조인 키 정합성이 매번 수작업. 재현 불가 |

문제는 단계 수가 아니라 **조인 키가 시스템 경계마다 깨진다**는 점이다.
그래서 이런 질문은 보통 애드혹 분석 프로젝트가 되고, 며칠이 걸리고, 다음 달에 또 처음부터 한다.

온톨로지는 이 조인을 **미리, 한 번, 그래프 엣지로 물리화**해 둔 것이다.

| | 다중 시스템 조인 | 온톨로지 순회 |
|---|---|---|
| 조인 키 | 질의 시점마다 매핑 | 적재 시점에 엣지로 확정 |
| 표현 | 3-way JOIN + ETL 파이프라인 | 경로 패턴 한 줄 |
| 새 질문 대응 | 파이프라인 재작성 | MATCH 패턴만 변경 |
| 실행 비용 | 시스템 간 데이터 이동 | 포인터 따라가기(index-free adjacency) |

> **핵심:** 온톨로지는 조인을 없애지 않는다. **조인을 질의 시점에서 모델링 시점으로 옮긴다.**
> 그 대가로 얻는 것이, 도메인 전문가가 SQL 없이도 읽을 수 있는 위 한 줄짜리 쿼리다.

---

## 6. 상관이지 인과가 아니다

이 쿼리의 결과를 두고 **"이 센서 이상이 이 불량을 일으켰다"** 고 말하면 안 된다.
쿼리가 실제로 보장하는 것은 훨씬 약하다.

> 같은 기계에 연결된 어떤 센서가 임계를 넘은 **상태이고**,
> 그 기계가 만든 어떤 부품이 어떤 검사에서 불합격한 **적이 있다.**

인과로 못 넘어가는 구체적인 이유들:

**(1) 시간 정보가 패턴에 전혀 없다.**
가장 큰 구멍이다. `s.lastReading`은 이름 그대로 **"가장 최근 값"** — 지금 이 순간의 스냅샷이다.
반면 `qc.checkDate`가 가리키는 검사는 지난주일 수도 있다.
**오늘 뜨거운 기계**와 **지난달 불량**이 아무 제약 없이 같은 행에 묶인다.
엄밀히 하려면 센서 판독을 시계열 이력(`Reading` 엔티티에 `timestamp`)으로 모델링하고
생산 시각과 겹치는 구간만 봐야 한다.

**(2) 어느 센서가 관련 있는지 구분하지 못한다.**
기계에 센서 5개가 달려 있고 그중 압력 센서만 튀었다면,
불량 원인이 압력인지, 아니면 무관한 다른 요인인지 이 쿼리는 말해 주지 않는다.
`monitors`가 many-to-one이라 **이상 센서마다 행이 복제될 뿐**이다.

**(3) 대조군이 없다.**
정상 센서 값에서도 불량이 같은 비율로 나온다면 상관 자체가 없다.
`WHERE`가 이상+실패 조합만 남기므로 **분자만 세고 분모를 못 센다.**
이는 확증 편향(confirmation bias)을 부르는 전형적 구조다.

**(4) 교란 변수(confounder)가 얼마든지 가능하다.**
예: 야간 교대조가 (a) 기계를 무리하게 돌려 온도를 올리고 (b) 숙련도가 낮아 불량을 낸다면,
온도와 불량은 상관이 있지만 서로 원인이 아니다. 진짜 원인은 교대조다.

그래서 이 쿼리의 올바른 위치는 **가설 생성기**다.

```
이 쿼리 → 의심 조합 목록 → 시간 정렬·대조군·통계 검정 → 현장 검증 → 인과 결론
   ↑                                                                    │
   └──────────── 개선 조치 후 재실행으로 효과 확인 ──────────────────────┘
```

원문이 말하는 continuous improvement 루프의 **첫 칸**이지, 마지막 칸이 아니다.

---

## 7. 결과 예시

작은 팩토리 그래프를 가정해 보자.

**데이터**

| Machine | Sensor | type | lastReading | threshold | 이상? |
|---|---|---|---|---|---|
| CNC-01 | S-11 | temperature | 92.4 | 85.0 | ✅ |
| CNC-01 | S-12 | vibration | 6.8 | 4.5 | ✅ |
| CNC-01 | S-13 | pressure | 3.1 | 5.0 | ❌ |
| LATHE-07 | S-21 | vibration | 2.2 | 4.5 | ❌ |
| PRESS-03 | S-31 | temperature | 101.7 | 90.0 | ✅ |

| Part | 생산 기계 | QualityCheck | passed | defectCode |
|---|---|---|---|---|
| Bracket-A | CNC-01 | QC-501 | false | DIM-OUT-OF-TOL |
| Shaft-B | CNC-01 | QC-502 | true | — |
| Housing-C | LATHE-07 | QC-503 | false | SURF-SCRATCH |
| Flange-D | PRESS-03 | QC-504 | false | CRACK-EDGE |

**실행 결과**

| m.name | s.type | s.lastReading | p.name | qc.defectCode |
|---|---|---|---|---|
| CNC-01 | temperature | 92.4 | Bracket-A | DIM-OUT-OF-TOL |
| CNC-01 | vibration | 6.8 | Bracket-A | DIM-OUT-OF-TOL |
| PRESS-03 | temperature | 101.7 | Flange-D | CRACK-EDGE |

**행 하나하나가 왜 나왔는지 / 왜 안 나왔는지**

- `Shaft-B` 제외 → `qc.passed = true`. 기계는 이상이지만 불량이 아니다.
- `Housing-C` 제외 → 불량이지만 LATHE-07의 센서가 정상. 이상 신호가 없다.
- `S-13`(pressure) 제외 → `3.1 > 5.0`이 거짓. 같은 기계라도 정상 센서는 안 나온다.
- **CNC-01이 두 행** → 이상 센서 2개 × 불량 부품 1개 = 2조합.
  부분그래프 매칭이라 조합이 전개된다. **행 수 = 불량 건수가 아니다.** 집계할 때 반드시 조심할 지점이다.

이 표를 보고 사람이 하는 판단: CNC-01은 온도·진동이 **동시에** 튀면서 치수 불량이 났으니
공구 마모나 주축 베어링을 의심할 만하다 — 하지만 이건 **가설**이고, 6장의 절차로 검증해야 한다.

---

## 8. 확장 방법

실무에서 이 쿼리는 출발점일 뿐이다. 세 방향으로 키운다.

### 8.1 시간 창(time window) 걸기 — 가장 시급한 보완

6장의 첫 번째 구멍을 막는다. 원래 질문의 "**last week**"를 실제로 구현하는 부분이다.

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold
  AND qc.passed = false
  AND qc.checkDate >= date('2026-08-05')
  AND qc.checkDate <  date('2026-08-12')
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode, qc.checkDate
ORDER BY qc.checkDate DESC
```

- `checkDate`는 `Quality-Check`에 이미 정의된 date 속성이라 모델 변경 없이 바로 쓸 수 있다.
- 상한을 `<`(미포함)로 두는 게 경계 중복을 막는 안전한 관례다.
- **다만 이건 절반의 해결이다.** 검사 시각만 좁혔을 뿐 `lastReading`은 여전히 현재 스냅샷이다.
  진짜로 맞추려면 `Sensor`에 시계열 `Reading`(timestamp, value)을 붙여
  생산 시각과 판독 시각을 겹쳐야 한다. 온톨로지 확장이 필요한 지점.

### 8.2 `defectCode`로 집계하기 — 개별 사건에서 패턴으로

행 단위 목록은 몇십 건만 넘어가도 읽히지 않는다. 묶어서 **어느 조합이 반복되는지** 본다.

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name,
       s.type,
       qc.defectCode,
       count(DISTINCT qc)      AS failures,
       count(DISTINCT p)       AS affectedParts,
       avg(s.lastReading)      AS avgReading,
       max(s.lastReading)      AS peakReading
ORDER BY failures DESC
LIMIT 20
```

- `count(*)` 대신 **`count(DISTINCT qc)`** 를 쓴 이유가 중요하다.
  7장에서 봤듯 이상 센서 수만큼 행이 복제되므로 `count(*)`는 불량 건수를 **부풀린다**.
  경로 곱셈(path multiplication)은 그래프 집계의 대표적 함정이다.
- `s.type` × `qc.defectCode` 교차표가 나오면 "진동 이상 ↔ 치수 불량" 같은 결합이 수치로 드러난다.
- `avgReading` / `peakReading`으로 이상의 정도까지 요약한다.
- 여기에 8.1의 시간 창을 얹어 주 단위 추이를 보면 개선 조치의 효과 검증에 쓸 수 있다.

### 8.3 `assigned_to` + `produces`로 우회 — 생산 맥락 되찾기

`has_part`는 요약된 지름길이라 **작업지시가 사라진다**. 정석 생산 체인으로 되돌리면
`Work-Order`가 들고 있는 맥락(priority, dueDate, status)을 함께 볼 수 있다.

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)<-[:assigned_to]-(wo:WorkOrder)-[:produces]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading,
       wo.workOrderId, wo.priority, wo.startDate, wo.dueDate,
       p.name, qc.defectCode
```

패턴이 어떻게 바뀌었는지 보자.

```
has_part 버전 :  s ──▶ m ─────has_part─────▶ p ◀── qc      (m→p 1홉)

assigned_to +
produces 버전 :  s ──▶ m ◀──assigned_to── wo ──produces──▶ p ◀── qc
                       └──── m→wo 역방향, wo→p 정방향 ────┘   (2홉)
```

- `<-[:assigned_to]-`는 **역방향**이다. 관계 정의는 `Work-Order → Machine`인데
  우리는 기계에서 출발해 작업지시로 거슬러 올라가기 때문이다.
- 2단계 문서가 강조한 `Machine ← Work-Order → Part` 구조가 그대로 드러난다.
  `Work-Order`는 헬스케어 경로의 `Appointment`와 같은 **이벤트/중개 엔티티**다.
- 얻는 것:
  - **`priority`별 불량률** — "긴급 작업지시가 불량을 더 많이 내는가?" (원문 표의 세 번째 질문)
  - **`startDate`/`dueDate`** — 생산 시각 구간. 8.1의 시간 정합 문제를 푸는 실마리다.
    `wo.startDate ~ wo.dueDate` 구간과 센서 판독 시각을 교차하면 인과에 한 걸음 다가간다.
  - **납기 압박 가설** — 마감이 촉박한 작업지시에서 이상·불량이 몰리는지.
- 잃는 것: 홉이 하나 늘어 비용이 오르고, 작업지시가 누락된 부품은 **결과에서 빠진다**.

> **모델링 교훈:** `has_part`와 `assigned_to`+`produces`는 같은 사실의 두 표현이다.
> 중복 관계(shortcut edge)는 **자주 쓰는 질의를 빠르고 단순하게** 만들지만,
> 대신 **맥락을 잃고 정합성 유지 부담**을 낳는다. 어떤 걸 쓸지는 질문이 결정한다.

---

## 9. 한 줄 요약

> **이 쿼리는 `Part`를 접점으로 텔레메트리(`monitors`)와 품질(`inspects`)을 잇고,
> 각 도메인의 판정 기준(`lastReading > threshold`, `passed = false`)을 `AND`로 교차시켜
> "이상 신호와 불량이 같은 기계에서 겹친 조합"을 뽑아내는 상관 분석기다.**
>
> 여러 시스템에 걸친 조인을 경로 한 줄로 대체하지만, 결과는 **인과가 아니라 가설**이다.
> 시간 창·집계·생산 체인 확장을 얹어야 실무 도구가 된다.

---

## 10. 함께 보면 좋은 카드

| 개념 | 관계 |
|---|---|
| `Sensor.threshold` | 이 쿼리의 왼쪽 절반. 기준값을 데이터로 올려 종류 무관 판정을 만든다 |
| `Quality-Check` 피드백 루프 | `QC → Part → Work-Order → Machine`. 이 쿼리의 역방향 순회와 같은 원리 |
| `has_part` vs `Work-Order` 체인 | 8.3의 트레이드오프. 지름길 엣지 대 이벤트 엔티티 |
| `Part.tolerance` | 치수 불량(`DIM-OUT-OF-TOL`)이 발생하는 근본 제약 |
| `Machine.status` | `running`/`maintenance` 등. 정비 중 기계를 제외하는 추가 필터로 유용 |
