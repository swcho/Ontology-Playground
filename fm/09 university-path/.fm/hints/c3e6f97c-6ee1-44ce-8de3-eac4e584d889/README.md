# Professor의 `tenured`가 boolean인 이유

## 질문과 답

**Q.** Professor의 `tenured` 속성이 boolean인 이유는?

**A.** 정년보장 여부는 예/아니오로 나뉘는 이분 범주이기 때문이다. 고용 안정성이나 기관의 투자 수준을 필터링하는 질의에 바로 쓰인다.

---

## 1. 학습 자료에서의 위치

University System 학습 경로 2단계(Faculty)에서 Professor 엔티티가 추가되며 등장한다.

| Property | Type | Identifier? |
|---|---|---|
| `professorId` | string | ✓ |
| `name` | string | |
| `rank` | string | |
| `tenured` | **boolean** | |
| `officeHours` | string | |

원문의 핵심 문장:

> The `rank` property (Assistant, Associate, Full) reflects academic hierarchy.
> The `tenured` boolean enables queries about job security and institutional investment.

그리고 "What we learned" 절에서:

> **Boolean properties** (tenured) create yes/no categorizations for filtering

즉 이 단계에서 `tenured`는 단순한 데이터 하나가 아니라 **"boolean 속성이라는 타입 선택 자체를 가르치기 위한 교보재"** 로 배치되어 있다. 같은 단계에서 배우는 다른 개념(transitive query)과 짝을 이뤄, "필터 조건 하나로 그래프 탐색 결과를 좁히는" 사례를 만든다.

---

## 2. tenure(정년보장)가 실제로 무엇인가

`tenured`가 왜 이분 범주인지 이해하려면 제도 자체를 알아야 한다.

- **tenure**는 미국·캐나다 등 영미권 대학의 교원 신분보장 제도다. 심사를 통과한 교수는 정당한 사유(due cause)나 재정 위기 같은 예외적 상황이 아니면 해고되지 않는 **영구 임용(permanent appointment)** 지위를 얻는다.
- 목적은 복지가 아니라 **학문의 자유(academic freedom)** 보호다. 인기 없거나 정치적으로 불편한 연구·발언을 이유로 교원을 내치지 못하게 하는 장치다. 1940년 AAUP(미국대학교수협회)의 "Statement of Principles on Academic Freedom and Tenure"가 현대적 기준의 뿌리다.
- **부여 방식이 결정적**이다. tenure는 점진적으로 쌓이는 점수가 아니라, 보통 임용 후 6년쯤에 이루어지는 **단일 심사(tenure review)의 판정 결과**다. 학과 → 단과대 → 본부 위원회 → 총장/이사회를 거쳐 최종적으로 "승인" 또는 "부결" 중 하나가 나온다.
- 결과는 문자 그대로 이분법이다. 통과하면 tenured, 부결되면 통상 **"up or out"** 원칙에 따라 유예 계약 1년 후 대학을 떠난다. "70% tenured" 같은 중간 상태는 제도상 존재하지 않는다.

이 제도적 성격이 데이터 모델링으로 그대로 번역된다. **현실 세계의 값 도메인이 정확히 두 개**이므로 boolean이 자연스러운 대응이다.

### rank와의 차이

같은 Professor 엔티티에서 `rank`는 string인데 `tenured`는 boolean인 이유가 여기서 갈린다.

| 속성 | 값 도메인 | 타입 | 이유 |
|---|---|---|---|
| `rank` | Assistant / Associate / Full (그 외 Lecturer, Distinguished 등 확장 가능) | string | 3개 이상의 순서 있는 범주. 기관마다 명칭이 다르고 늘어날 수 있음 |
| `tenured` | 있음 / 없음 | boolean | 값이 정확히 둘. 확장될 여지가 구조적으로 없음 |

주의할 점은 둘이 **상관관계는 있지만 종속되지 않는다**는 것이다. 미국 대학에서 Associate 승진과 tenure 승인이 대체로 함께 오지만, tenure 없는 Associate도 있고 tenure 받은 Assistant도 드물게 있다. 그래서 `rank`로 tenure를 유도(derive)하지 않고 **독립 속성으로 분리**한 설계가 옳다.

---

## 3. boolean 타입을 고른 실질적 이점

### 3.1 질의가 그대로 필터가 된다

학습 자료가 제시하는 질문들:

- "Which tenured faculty teach introductory courses?"
- "Which students are taking courses from tenured professors?"
- "Which departments have the most tenured faculty?" → `Department ← Professor (tenured=true, count)`

boolean이면 조건이 `WHERE p.tenured = true` 한 줄로 끝난다. 문자열이었다면 `IN ['Yes','yes','Y','TENURED','tenured']` 같은 방어 코드가 필요하고, 값의 철자 흔들림이 곧 데이터 품질 사고가 된다.

```gql
MATCH (d:Department)<-[:belongs_to]-(p:Professor)
WHERE p.tenured = true
RETURN d.name, COUNT(p) AS tenured_count
ORDER BY tenured_count DESC
```

transitive query와 결합하면 이렇게 된다.

```gql
MATCH (p:Professor)-[:teaches]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE p.tenured = true
RETURN DISTINCT s.name, c.title
```

`tenured = true` 하나가 다중 홉 탐색의 **시작 노드 집합을 절반 이하로 잘라내는 가지치기(pruning) 조건**으로 작동한다. 이게 boolean 속성이 그래프 질의에서 특히 값어치 있는 이유다.

### 3.2 저장·인덱싱 효율

- 값이 1비트 정보량이므로 저장 공간이 작고, 컬럼 지향 저장소에서는 **비트맵 인덱스**로 표현하기에 이상적이다. 비트맵끼리의 AND/OR 연산으로 `tenured=true AND rank='Full'` 같은 복합 조건을 매우 빠르게 처리한다.
- 카디널리티가 2라서 **집계·그룹화 비용이 낮다.** `GROUP BY tenured`는 버킷이 두 개뿐이다.
- 반대로 카디널리티가 낮다는 점은 B-tree 인덱스 단독으로는 선택도(selectivity)가 나빠 풀스캔보다 이득이 적을 수 있다는 뜻이기도 하다. 실무에서는 `(departmentId, tenured)`처럼 **복합 인덱스의 뒷자리**로 쓰거나 부분 인덱스(partial index)를 거는 편이 낫다. "boolean이니 무조건 인덱스가 빠르다"고 외우면 틀린다.

### 3.3 의미가 스키마에 박힌다

boolean은 값 검증이 타입 수준에서 끝난다. 별도의 enum 테이블, CHECK 제약, 정규화 로직이 필요 없다. 여러 소스 시스템(HR, SIS, 학사 DB)에서 데이터를 통합할 때 **"참/거짓"은 시스템 간 매핑 손실이 가장 적은 표현**이다. 자료 서두에서 밝혔듯 이 온톨로지의 데이터는 SIS·LMS·HR·학사기획 DB에 흩어져 있는데, HR이 `'T'/'N'`을 쓰고 SIS가 `'tenured'/'non-tenured'`를 쓰더라도 온톨로지 층에서 boolean 하나로 수렴시키면 하위 표현 차이가 질의로 새어 나오지 않는다.

---

## 4. 이분법이 무너지는 경계 사례

여기가 이 카드에서 가장 중요한 부분이다. boolean은 "현실이 정말 둘로 나뉠 때만" 옳다. tenure는 그 조건을 **대체로** 만족하지만 완전히는 아니다.

### 4.1 tenure-track 진행 중 (가장 흔한 반례)

임용 6년 차 심사를 앞둔 Assistant Professor는 아직 tenured가 아니다. 그러나 심사 대상조차 아닌 비정년트랙 강사와 **같은 `false`로 뭉뜽그려진다.** 실제로는 세 상태가 구분된다.

1. tenured (심사 통과)
2. tenure-track, 미판정 (심사 예정 — 잠재적 tenured)
3. non-tenure-track (심사 대상 아님 — 구조적으로 tenure 불가)

`tenured: boolean` 하나로는 2번과 3번을 구별할 수 없다. "고용 안정성"이라는 질의 목적에서 보면 이 둘은 전혀 다른 집단이다.

**해결책:** `tenured` boolean은 유지하되 `tenureTrack: boolean`을 함께 두거나, 아예 `tenureStatus: string`(enum: `tenured` / `tenure_track` / `non_tenure_track` / `emeritus`)으로 승격한다. 어느 쪽이든 **"질문이 세 갈래 이상으로 나뉘는 순간 boolean은 부족하다"** 는 신호로 읽어야 한다.

### 4.2 시간 차원의 부재

`tenured: true`는 "지금 tenured"만 말할 뿐 **언제 받았는지**를 담지 못한다. "2020년 이후 tenure를 받은 교수는?", "이 교수는 심사 통과 전이었나 후였나?" 같은 질의는 boolean만으로 답할 수 없다. `tenureGrantedDate: date`를 추가하면 boolean은 사실상 `tenureGrantedDate IS NOT NULL`의 파생값이 되어 중복이 생긴다. 이 중복을 감수할지(질의 편의) 정규화할지(정합성)가 설계 판단 지점이다.

### 4.3 제도 자체가 없는 경우

- **국가별 차이:** tenure는 영미권 제도다. 한국의 정년보장(승진·재임용 심사 통과), 독일의 W2/W3 종신 임용, 영국의 permanent contract는 유사하지만 동일하지 않다. 다국적 데이터를 통합하면 boolean의 의미가 나라마다 미묘하게 달라진다.
- **기관별 차이:** 커뮤니티 칼리지, 영리 대학, 일부 주에서는 tenure 제도를 폐지했거나 애초에 없다. 이 경우 `false`인지 `null`(해당 없음)인지 구분이 필요해진다. **boolean에 null을 허용하면 사실상 3-값 논리**가 되어 `WHERE tenured = false`가 null 행을 놓치는 함정이 생긴다.

### 4.4 그 밖의 회색지대

- **명예교수(emeritus):** 퇴임했지만 tenured였던 사람. 현재 재직자가 아니므로 `true`로 두면 재직 교원 통계가 오염된다.
- **겸임·공동 임용(joint appointment):** A학과에서는 tenured, B학과에서는 겸임인 경우. tenure는 교수 개인이 아니라 **특정 학과/기관에 귀속**되므로, Professor 노드 위의 단일 속성이 아니라 `belongs_to` 관계의 속성으로 두는 게 더 정확할 수 있다.
- **정지·심사 중지(tenure clock stop):** 출산·질병 등으로 심사 시계가 멈춘 상태. 여전히 `false`지만 통상적 `false`와 맥락이 다르다.

---

## 5. 정리: 언제 boolean을 고를 것인가

| 판단 기준 | tenure의 경우 |
|---|---|
| 값 도메인이 정확히 둘인가? | 대체로 그렇다 (심사 결과는 승인/부결) |
| 중간값·정도(degree)가 의미 있나? | 아니다. 50% tenured는 존재하지 않음 |
| 값이 늘어날 가능성이 있나? | 낮다. 단, 상태 세분화 요구는 생길 수 있음 (§4.1) |
| 주 용도가 필터링·집계인가? | 그렇다. "tenured faculty만", "학과별 tenured 수" |
| "해당 없음"을 표현해야 하나? | 학습 모델 범위에서는 불필요, 실무에서는 쟁점 (§4.3) |

**핵심 원칙:** boolean은 현실의 이분성을 반영할 때만 정직하다. `tenured`는 승인/부결이라는 실제 심사 구조를 그대로 옮긴 것이라 정당하고, 덕분에 `tenured = true` 한 조건이 다중 홉 그래프 질의의 강력한 필터가 된다. 다만 "tenure-track 진행 중"처럼 **제도의 시간축이나 자격 구조를 물어야 하는 순간** 이분법은 깨지고, 그때는 enum이나 별도 속성으로 승격하는 것이 옳은 설계다.

---

## 관련 개념

- **Boolean properties** — yes/no 범주화로 필터링 (2단계 학습 목표)
- **Transitive queries** — `Professor → Course → Enrollment → Student` 다중 홉 탐색. `tenured` 필터와 결합해 위력을 발휘
- **타입 선택 대비** — `gpa`는 float(연속값·임계 질의), `credits`/`maxEnrollment`는 integer(개수·용량), `rank`/`level`은 string(다중 범주), `tenured`는 boolean(이분 범주)
