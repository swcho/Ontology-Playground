# Professor의 `rank` 속성 — 값과 의미

> **Q.** Professor의 `rank` 속성이 갖는 값과 의미는?
>
> **A.** Assistant, Associate, Full의 학문적 위계를 나타낸다. 조교수 → 부교수 → 정교수로 이어지는 정해진 순서를 갖는다.

---

## 1. 원문에서의 정의

University System 학습 경로 2단계(Faculty)에서 추가되는 `Professor` 엔티티의 스펙은 다음과 같다.

| Property | Type | Identifier? |
|---|---|---|
| `professorId` | string | ✓ |
| `name` | string | |
| **`rank`** | **string** | |
| `tenured` | boolean | |
| `officeHours` | string | |

원문 설명:

> The `rank` property (Assistant, Associate, Full) reflects academic hierarchy.
> The `tenured` boolean enables queries about job security and institutional investment.

그리고 "What we learned" 요약에서 다시 못 박는다.

> **Academic rank** follows a defined hierarchy (Assistant → Associate → Full)

즉 `rank`는 단순한 라벨(label)이 아니라 **정해진 서열(defined hierarchy)을 가진 값의 집합**이라는 점이 이 카드의 핵심이다.

---

## 2. 세 값의 실제 의미 (미국 tenure-track 체계)

`Assistant / Associate / Full`은 미국 대학의 **tenure-track(정년트랙) 3단계 직급**을 그대로 옮긴 것이다.

| 값 | 정식 명칭 | 통상적 위치 | tenure(정년보장) 상태 |
|---|---|---|---|
| `Assistant` | Assistant Professor | 신임 교원. 박사학위·박사후연구원을 마치고 처음 임용되는 단계 | 대개 **미보장** (tenure-track이지만 아직 tenure 없음) |
| `Associate` | Associate Professor | 임용 후 약 5~7년차의 **tenure 심사(tenure review)**를 통과하며 승진 | 대개 **보장됨** (tenure와 함께 승진하는 것이 관례) |
| `Full` | (Full) Professor | 부교수 상태에서 추가로 수년간 연구·교육·봉사 실적을 쌓아 승진하는 최고 직급 | 보장됨 |

승진의 실질적 의미:

- **Assistant → Associate**: 가장 결정적인 관문. 미국에서는 이 심사가 사실상 *up-or-out*(승진하지 못하면 대학을 떠나야 함)으로 운영되는 경우가 많다. 그래서 `rank`와 `tenured`는 통계적으로 강하게 상관된다.
- **Associate → Full**: 정년보장 여부가 아니라 **학문적 영향력·리더십**을 평가한다. 승진 기한이 정해져 있지 않아 부교수로 오래 머무는 경우도 흔하다. 학과장(`headOfDept`), 학술지 편집위원, 대형 과제 PI 등은 대체로 Full 등급에서 나온다.

### 한국 대학 직급과의 대응

| 미국 (`rank` 값) | 한국 직급 | 비고 |
|---|---|---|
| Assistant Professor | **조교수** | 통상 2~4년 단위 재임용 계약 |
| Associate Professor | **부교수** | 이 단계에서 **정년보장(tenure) 심사**를 받는 경우가 많음 |
| (Full) Professor | **정교수** | 최고 직급 |
| — | (전임강사) | 과거 조교수 아래 직급이었으나 2012년 고등교육법 개정으로 폐지되어 조교수로 통합 |

> 한국은 미국과 달리 "부교수 승진 = 정년보장"이 자동으로 성립하지 않는다. 대학에 따라 정년보장 심사 시점이 부교수 승진 때일 수도, 정교수 승진 때일 수도 있다. 그래서 이 온톨로지가 `rank`(직급)와 `tenured`(정년보장 여부)를 **별개의 두 속성으로 분리**한 설계는 현실을 잘 반영한 것이다.

### 3개 값이 커버하지 못하는 것들

실제 대학에는 tenure-track 밖의 교원 유형이 많다.

- **Adjunct / Lecturer / Instructor** — 시간강사, 강의전담교원 (비정년트랙)
- **Visiting Professor** — 초빙교수
- **Research Professor** — 연구교수 (강의 의무 없음)
- **Clinical Professor** — 임상교수 (의대·치대 등)
- **Professor Emeritus** — 명예교수 (퇴임 후)
- **Endowed Chair / Distinguished Professor** — 석좌교수 (Full 위의 명예 등급)

학습 경로에서는 모델을 단순하게 유지하려고 tenure-track 3단계만 다룬다. **실무 온톨로지로 확장할 때는 이 값 집합이 부족하다**는 점을 인지해야 한다. 특히 Emeritus나 Adjunct는 "3단계 위계" 위에 깔끔하게 얹히지 않아서, 아래 §3의 순서 모델링을 곧바로 깨뜨린다.

---

## 3. `rank`를 "순서 있는 범주(ordinal)"로 다룰 때의 모델링 함의

이 카드가 정말로 묻는 것은 값 3개의 암기가 아니라, **왜 "정해진 순서를 갖는다"는 말을 굳이 강조하는가**이다.

### 3-1. 척도의 종류

| 척도 | 정의 | 가능한 연산 | 예 |
|---|---|---|---|
| **Nominal**(명목형) | 구별만 가능, 순서 없음 | `=`, `≠`, 그룹핑 | `Department.name`, `Course.title` |
| **Ordinal**(순서형) | 순서는 있지만 간격은 의미 없음 | `=`, `<`, `>`, 정렬, 중앙값, MIN/MAX | **`Professor.rank`**, `Enrollment.grade`(A>B>C>D>F), 학년 |
| **Interval / Ratio**(등간/비율형) | 간격·비율이 의미를 가짐 | `+`, `-`, `×`, 평균 | `Student.gpa`, `Course.credits`, `Department.budget` |

`rank`는 명확히 **ordinal**이다. 같은 University 온톨로지 안의 `Enrollment.grade`(A~F)와 동일한 성격이며, 원문의 GQL 예제가 `WHERE e.grade IN ['C','D','F']`처럼 **열거로 우회**하는 것도 문자열 ordinal의 전형적 증상이다.

### 3-2. 함의 ① — 비교·정렬 연산이 "의미를 갖는다"

nominal이라면 "이 교수가 저 교수보다 높다"는 질문 자체가 성립하지 않는다. ordinal이기 때문에 다음 질의가 정당해진다.

- "각 학과에서 **가장 높은 직급**의 교수는 누구인가?" → `MAX(rank)`
- "**부교수 이상**이 담당하는 400-level 과목 비율은?" → `rank >= Associate`
- "학과별 직급 분포(피라미드)는 어떻게 되는가?" → 정렬된 축을 가진 히스토그램
- "조교수가 담당하는 강의의 평균 학점과 정교수의 그것을 비교하면?" → 순서 축을 따른 추세 분석

### 3-3. 함의 ② — `string` 타입만으로는 순서가 보장되지 않는다

원문 스펙에서 `rank`의 타입은 그냥 `string`이다. 여기에 세 가지 위험이 있다.

1. **표기 흔들림**: `Full` / `Full Professor` / `Professor` / `정교수` / `PROF`가 섞여 들어오면 조인·집계가 조용히 깨진다. HR 시스템과 SIS의 코드값이 다른 것은 흔한 일이다.
2. **사전순 정렬의 함정**: 우연히도 `Assistant < Associate < Full`은 알파벳 순서와 서열 순서가 **일치한다**(`Assi` < `Asso` < `Full`). 그래서 `ORDER BY rank`가 "잘 동작하는 것처럼" 보인다. 그러나 이건 **순전한 우연**이다. `Emeritus`, `Adjunct`, `Distinguished`를 추가하거나 한국어 표기를 쓰는 순간 정렬은 무의미해진다. 사전순 정렬에 의존하는 코드는 이 시점에 조용히 잘못된 답을 낸다.
3. **오타 무방비**: `Assistent`, `Assoc.` 같은 값이 들어와도 DB가 막아주지 않는다.

### 3-4. 함의 ③ — 실무에서의 대응 패턴

| 방식 | 설명 | 장점 | 단점 |
|---|---|---|---|
| **Enum / 제약 있는 값 집합** | `rank ∈ {Assistant, Associate, Full}`을 스키마 수준에서 강제 | 오타·표기 흔들림 차단, 도구가 UI 드롭다운 생성 가능 | 순서 자체는 여전히 암묵적 |
| **정수 순위 필드 병행** | `rank`(표시용 문자열) + `rankLevel`(1, 2, 3) | 비교·정렬·집계가 자명해짐 | 두 필드의 동기화 책임 발생 |
| **Rank를 별도 엔티티로 승격** | `Professor --has_rank--> Rank(rankId, label, level, isTenureTrack)` | 다국어 라벨, 비정년트랙 직급, 순서 메타데이터를 모두 수용 | 모델 복잡도 증가, 조인 1홉 추가 |
| **온톨로지 계층 관계** | RDF/OWL이라면 `skos:broader`나 전용 `precedes` 관계로 순서를 **관계로** 표현 | 기계가 순서를 추론 가능 | 표현이 무거움 |

학습 경로 단계에서는 첫 번째(사실상 문자열 + 관례)로 충분하지만, "정해진 순서를 갖는다"는 서술은 **실무에서는 2~4번 중 하나로 명시화해야 한다**는 신호로 읽으면 된다.

### 3-5. 함의 ④ — 시간에 따라 변하는 값

`rank`는 **현재 시점의 스냅샷**이다. 승진은 사건(event)이므로 "2019년에 조교수였던 사람이 지금 부교수"라는 이력은 단일 문자열 필드로 표현할 수 없다. 필요하다면 `Enrollment`가 Student–Course의 many-to-many를 풀어낸 것과 같은 방식으로, **`Appointment`/`Promotion` 같은 junction·이벤트 엔티티**(professorId, rank, startDate, endDate)를 두어야 한다. 이 학습 경로가 가르친 "junction entity" 패턴이 그대로 재사용되는 지점이다.

### 3-6. 함의 ⑤ — `rank`와 `tenured`는 독립이 아니다

두 속성은 서로 다른 축이지만 **강한 상관**이 있다.

- `rank=Full` 이면서 `tenured=false` → 거의 대부분 데이터 오류이거나, 비정년트랙 특수 직급.
- `rank=Assistant` 이면서 `tenured=true` → 매우 이례적. 검증 대상.

즉 두 속성 사이에 **무결성 규칙(integrity constraint)**을 걸 수 있다. 온톨로지가 단순한 스키마를 넘어 "도메인 지식"을 담는다는 것은 이런 규칙까지 표현한다는 뜻이다.

---

## 4. 질의 예시

```gql
-- 학과별 정교수 수
MATCH (p:Professor)-[:belongs_to]->(d:Department)
WHERE p.rank = 'Full'
RETURN d.name, COUNT(p) AS full_professors
ORDER BY full_professors DESC
```

```gql
-- 조교수가 담당하는 400-level 과목 (신임 교원의 고학년 강의 부담 점검)
MATCH (p:Professor)-[:teaches]->(c:Course)
WHERE p.rank = 'Assistant' AND c.level >= 400
RETURN p.name, COUNT(c) AS advanced_courses
ORDER BY advanced_courses DESC
```

```gql
-- 정년보장 여부와 직급이 불일치하는 레코드 탐지 (데이터 품질 점검)
MATCH (p:Professor)
WHERE (p.rank = 'Full'      AND p.tenured = false)
   OR (p.rank = 'Assistant' AND p.tenured = true)
RETURN p.professorId, p.name, p.rank, p.tenured
```

> `rank >= 'Associate'` 같은 표현을 쓰고 싶어질 텐데, 문자열 비교에 의존하는 순간 §3-3의 사전순 함정을 밟는다. `IN ['Associate','Full']`로 열거하거나 `rankLevel >= 2`를 쓰는 편이 안전하다.

---

## 5. 자주 하는 실수

- ❌ "rank는 그냥 이름표다" → **아니다.** 순서가 있는 ordinal이고, 그래서 비교·정렬 질의가 성립한다.
- ❌ "Full = 정년보장" → 별개 속성. 상관은 높지만 논리적 함의는 아니며, 그래서 `tenured` boolean이 따로 존재한다.
- ❌ "Associate가 최고 직급" → Full이 최고. `Associate`(부교수)는 중간 단계다. Associate가 "연관/부"라는 뜻이라 헷갈리기 쉽다.
- ❌ "ORDER BY rank 하면 서열대로 나온다" → 이 세 값에서만 우연히 맞는다. 값이 늘면 깨진다.
- ❌ "전임강사도 넣어야 한다" → 한국 기준 2012년 폐지된 직급이며, 이 모델은 미국 tenure-track 3단계를 따른다.

---

## 6. 한 줄 정리

`rank`는 **Assistant(조교수) → Associate(부교수) → Full(정교수)**라는 미국 tenure-track 3단계 학문적 위계를 담는 속성으로, 단순 분류(nominal)가 아니라 **정해진 순서를 갖는 범주(ordinal)**이기 때문에 비교·정렬·분포 질의가 의미를 가지며, 타입이 `string`인 만큼 실무에서는 값 집합 제약이나 순위 필드로 그 순서를 명시화해 주어야 한다.
