# `enrollDate`는 왜 date 타입인가

## 질문

Enrollment 엔티티의 속성 표를 보면 유독 하나만 타입이 다르다.

| Property | Type | Identifier? |
|---|---|---|
| `enrollmentId` | string | ✓ |
| `semester` | string | |
| `grade` | string | |
| `enrollDate` | **date** | |
| `status` | string | |

다섯 개 중 넷은 string인데 `enrollDate`만 date다. `"2024-09-03"`이라고 string으로 넣어도 사람 눈에는 똑같아 보이는데, 왜 굳이 별도 타입을 쓸까?

## 한 문장 답

**수강신청이 일어난 시점을 기록해 시간 기반 질의를 가능하게 하기 위해서다.** date로 선언하는 순간 범위 비교·정렬·날짜 산술이 **타입 차원에서 보장**되고, `semester` 같은 범주형 문자열이 표현할 수 없는 **연속적인 시간 축**이 생긴다.

## 1. date 타입이 string 날짜와 다른 점

"어차피 문자열도 정렬되잖아?"가 가장 흔한 반론이다. ISO 8601(`YYYY-MM-DD`)로만 저장하면 사전순 정렬이 시간순 정렬과 우연히 일치하기 때문이다. 하지만 그건 **우연**이고, 나머지는 전부 깨진다.

| 연산 | `date` 타입 | `string`으로 저장한 날짜 |
|---|---|---|
| 정렬 | 시간 순서로 보장 | ISO 형식일 때만 우연히 일치. `"9/3/2024"`가 하나라도 섞이면 붕괴 |
| 범위 비교 `>= X AND < Y` | 시간 비교 | 사전순 비교. `"2024-9-3"`(0 없는 월)은 `"2024-10-01"`보다 크게 나옴 |
| 날짜 산술 (`+30일`, `date2 - date1`) | 엔진이 지원 | 불가능. 파싱 → 계산 → 재포맷을 질의마다 수동으로 |
| 월/주/요일 추출 (`EXTRACT`, `DATE_TRUNC`) | 내장 함수 | 문자열 슬라이싱. 오프바이원 버그 온상 |
| 유효성 | `2024-02-31`은 저장 단계에서 거부 | 그냥 저장됨. 읽는 쪽에서 터짐 |
| 윤년·월말·타임존 | 캘린더 규칙이 타입에 내장 | 직접 구현 |
| 서로 다른 소스 통합 | 같은 date로 정규화 | SIS는 `2024-09-03`, LMS는 `03/09/2024`, HR은 epoch — 비교 불가 |

핵심은 **"할 수 있냐"가 아니라 "누가 보장하냐"**다. string으로도 위 연산을 흉내 낼 수 있지만, 그 정확성은 **데이터를 넣은 모든 시스템이 같은 포맷을 지켰다는 가정**에 의존한다. 이 시나리오의 데이터는 SIS·LMS·HR·학사계획 DB 네 곳에서 오므로 그 가정은 거의 확실히 깨진다. date 타입은 그 가정을 **스키마가 강제하는 계약**으로 승격시킨다.

> 온톨로지에서 타입 선언은 저장 포맷 지정이 아니라 **의미(semantics) 선언**이다. `enrollDate: date`는 "이 값은 캘린더 위의 한 점이며, 다른 시점과 순서·거리를 잴 수 있다"는 약속이다. `grade: string`은 그런 약속을 하지 않는다.

## 2. `semester`(string) vs `enrollDate`(date) — 범주 vs 연속 시간축

같은 Enrollment 안에 시간을 나타내는 속성이 **두 개** 있는데 타입이 다르다. 이건 중복이 아니라 **역할 분담**이다.

| | `semester` (string) | `enrollDate` (date) |
|---|---|---|
| 성격 | **범주형(categorical)** — `"Fall 2024"` 같은 라벨 | **연속형(continuous)** — 캘린더 위의 한 점 |
| 값의 개수 | 유한하고 적음 (학기 수만큼) | 사실상 무한 |
| 자연스러운 연산 | 그룹핑, 동등 비교(`=`), 필터 | 범위, 정렬, 차이 계산, 시계열 |
| 정렬 | **불가능** — `"Fall 2024" < "Spring 2024"`는 사전순이라 봄이 가을보다 뒤로 감 | 정확 |
| 답할 수 있는 질문 | "이번 학기 수강생 수는?" | "수강신청 오픈 후 며칠 만에 정원이 찼나?" |
| 비유 | 서랍 이름 | 서랍 안에서의 위치 |

`semester`는 **학사 행정의 단위**다. 성적 산출, 등록금 부과, 졸업요건 판정은 모두 학기 단위로 이뤄지므로 `WHERE e.semester = 'Fall 2024'` 같은 그룹핑 키가 반드시 필요하다. 하지만 학기는 **덩어리**라서 그 안에서 벌어진 일의 순서를 모른다.

`enrollDate`는 **학기라는 덩어리를 쪼개 들어가는 축**이다. 같은 `"Fall 2024"` 안에서도 오픈 첫날 신청한 학생과 마감 직전에 신청한 학생은 행동이 다르고, 그 차이는 date가 있어야만 보인다.

즉 두 속성은 **해상도(granularity)가 다른 두 개의 시간 표현**이다. 하나로 합칠 수 없다.

- `semester`만 있으면 → 학기 내부의 순서·속도를 전부 잃는다.
- `enrollDate`만 있으면 → "가을학기"라는 행정 단위를 매번 날짜 범위로 하드코딩해야 하고, 학기 경계가 해마다 바뀌므로 질의가 깨진다.

## 3. date이기 때문에 가능해지는 질의들

### (a) 수강신청 오픈 후 경과일 — 신청 속도 분석

가을학기 신청 오픈일이 `2024-08-01`이라 할 때, 과목별로 학생들이 평균 며칠 만에 신청했는지:

```gql
MATCH (c:Course)<-[:for_course]-(e:Enrollment)
WHERE e.semester = 'Fall 2024'
RETURN c.title,
       AVG(e.enrollDate - DATE '2024-08-01') AS avg_days_to_enroll,
       MIN(e.enrollDate) AS first_signup,
       COUNT(e) AS total
ORDER BY avg_days_to_enroll ASC
```

`avg_days_to_enroll`이 작을수록 **인기 과목**이다. 여기서 `e.enrollDate - DATE '2024-08-01'`이라는 **뺄셈**이 핵심인데, string이었다면 이 표현식 자체가 성립하지 않는다.

### (b) 정원 소진 속도 — `maxEnrollment`와의 결합

Course에는 `maxEnrollment`(integer)가 있다. `enrollDate`로 정렬해 누적 카운트를 내면 "정원이 언제 찼는가"를 알 수 있다.

```gql
MATCH (c:Course)<-[:for_course]-(e:Enrollment)
WHERE e.semester = 'Fall 2024'
WITH c, e ORDER BY e.enrollDate ASC
WITH c, COLLECT(e.enrollDate) AS dates
RETURN c.title, c.maxEnrollment, dates[c.maxEnrollment - 1] AS date_full
```

`ORDER BY e.enrollDate`가 **시간순임이 보장**되어야 이 계산이 의미를 갖는다.

### (c) 창구 개설 이후 7일 이내 신청 vs 이후 신청의 성적 차이

```gql
MATCH (s:Student)-[:enrolls_in]->(e:Enrollment)-[:for_course]->(c:Course)
WHERE e.enrollDate >= DATE '2024-08-01' AND e.enrollDate < DATE '2024-08-08'
RETURN c.title, e.grade, COUNT(*) 
```

**반개구간(`>=` … `<`)** 패턴은 date 타입의 전형적 관용구다. 경계일 중복·누락 없이 기간을 자를 수 있다.

### (d) 늦은 신청과 학업 성과의 상관

```gql
MATCH (s:Student)-[:enrolls_in]->(e:Enrollment)-[:for_course]->(c:Course)
      <-[:offers]-(d:Department)
WHERE e.grade IN ['D', 'F']
RETURN d.name, AVG(e.enrollDate - DATE '2024-08-01') AS avg_lateness
ORDER BY avg_lateness DESC
```

"학점을 못 받은 학생들은 신청을 늦게 하는 경향이 있는가?" — 조기 경보 지표로 쓰일 수 있는 질문이며, 학습 경로가 소개한 `Department → Course ← Enrollment` 경로에 **시간 축을 한 겹 더 얹은** 형태다.

### (e) 학기 간 재수강 간격

한 학생이 같은 과목을 다시 들었을 때 그 사이 간격:

```gql
MATCH (s:Student)-[:enrolls_in]->(e1:Enrollment)-[:for_course]->(c:Course),
      (s)-[:enrolls_in]->(e2:Enrollment)-[:for_course]->(c)
WHERE e1.enrollDate < e2.enrollDate
RETURN s.name, c.title, e2.enrollDate - e1.enrollDate AS gap_days
```

`semester`만 있었다면 `"Fall 2024"`와 `"Spring 2025"` 사이의 간격을 계산할 방법이 없다.

## 4. 학습 경로가 말하는 "temporal data"의 세 축

Scenario Overview의 Key concepts에 이렇게 적혀 있다.

> **Temporal data** — semesters, enrollment dates, academic years

이 세 가지는 서로 다른 엔티티에 흩어져 있고 타입도 전부 다르다. 이게 이 모델의 시간 설계 전체다.

| 축 | 속성 | 엔티티 | 타입 | 해상도 | 역할 |
|---|---|---|---|---|---|
| Academic year | `enrollmentYear` | Student | integer | 년 | **코호트(cohort)** — 입학 연도로 학생 세대를 가름. "24학번" |
| Semester | `semester` | Enrollment | string | 학기 | **행정 단위** — 성적 산출·등록금·졸업요건의 그룹핑 키 |
| Enrollment date | `enrollDate` | Enrollment | date | 일 | **정밀 시점** — 순서, 간격, 속도 |

세 축이 어떻게 다른 질문을 담당하는지:

- `enrollmentYear`(integer) → "2021학번 학생들의 4년 뒤 평균 GPA는?" · "학번별 전공 분포 변화" · 연 단위 산술 가능(`2025 - s.enrollmentYear = 재학연차`)
- `semester`(string) → "Fall 2024에 개설된 400단계 과목의 수강생 수" · 학기별 집계
- `enrollDate`(date) → "신청 오픈 후 며칠 만에?" · 학기 내부의 흐름

**해상도가 굵은 것부터 가는 것 순서로 년 → 학기 → 일**이며, 각 축은 그 아래 축이 못 하는 일을 한다. 세 축이 다 있어야 "21학번 학생들이 Fall 2024 학기에 신청을 예년보다 빨리 했는가" 같은 교차 질의가 가능해진다.

> 타입 선택은 해상도 선택이다. `enrollmentYear`가 date가 아니라 integer인 이유도 같은 논리다 — 입학 "연도"는 날짜 정밀도가 필요 없고, 정수면 산술(재학연차 계산)과 정렬이 둘 다 되므로 충분하다. 반대로 `enrollDate`를 integer(연도)로 낮추면 학기 내부 정보가 통째로 사라진다.

## 5. 이 모델의 한계 — 시점이 하나뿐이다

`enrollDate`는 이 온톨로지 전체에서 **유일한 date 속성**이다. 즉 Enrollment의 생애에서 **"시작" 한 점만 기록**되고, 나머지는 전부 관측되지 않는다.

Enrollment에는 `status`(string)가 있는데, 이 값은 `enrolled` → `dropped` / `completed` 같이 **변한다**. 그런데 **언제 변했는지를 담을 자리가 없다.** 그래서 다음 시점들이 모델에 부재한다.

| 없는 시점 | 답할 수 없게 되는 질문 |
|---|---|
| **drop date** (수강철회일) | "철회는 주로 학기 몇 주차에 몰리나?" · "환불 마감 전 철회 vs 후 철회" · "중간고사 직후 철회율" |
| **성적 확정일** (grade finalization) | "성적 입력이 마감보다 늦은 교수는?" · "성적 정정이 언제 있었나" |
| **add/swap date** | 정정기간 중의 과목 교체 이력 |
| **완료일** | 실제 이수 완료 시점 (`semester`로 근사할 뿐) |
| Course의 개설/폐강일 | 과목 커리큘럼 변경 이력 |
| Professor의 임용일·정년 취득일 | `tenured`는 boolean이라 **언제부터** 정년보장인지 모름 |

이 부재의 구조적 성격은 이렇다. **`status`는 현재 상태(current state)만 저장하는 스냅샷이고, 그 상태로 언제 전이했는지에 대한 이력(history)이 없다.** `enrollDate`가 있어서 "언제 시작했나"는 알지만, "언제 끝났나 / 언제 바뀌었나"는 모른다.

실무 모델이라면 보통 이렇게 확장한다.

1. **속성 추가** — Enrollment에 `dropDate: date`, `completionDate: date`, `gradeFinalizedAt: date`를 나란히 둔다. 가장 간단하지만 상태가 늘어날 때마다 컬럼이 늘어난다.
2. **상태 전이 엔티티로 승격** — `EnrollmentEvent(eventType, occurredAt: date)`를 만들어 Enrollment에 매단다. Enrollment 자체가 Student–Course를 junction으로 승격시킨 것과 **정확히 같은 논리**의 한 단계 더 나아간 적용이다. 상태 변화에 부가 정보(사유, 승인자)가 붙는 순간 이 방식이 필요해진다.
3. **유효 기간(bitemporal)** — `validFrom` / `validTo`를 두어 각 레코드가 언제 사실이었는지를 기록.

학습 경로의 모델이 1번조차 하지 않은 건 **의도적 단순화**다. 이 경로의 학습 목표는 junction entity 패턴과 transitive query이지 temporal modeling이 아니므로, "시간 축이 필요하다"는 사실만 `enrollDate` 하나로 보여주고 넘어간다. 하지만 카드 답안이 말하는 "시간 기반 질의"의 실제 범위는 **신청 시점을 기준으로 한 질의에 한정**된다는 점을 정확히 알아두는 것이 이 한계 인식의 핵심이다.

## 6. 한 장 요약

```
                    시간 해상도
   굵음  ┌──────────────────────────────────────┐
         │ Student.enrollmentYear   integer  년 │ ← 코호트
         ├──────────────────────────────────────┤
         │ Enrollment.semester      string  학기│ ← 행정 단위 (범주형, 정렬 불가)
         ├──────────────────────────────────────┤
         │ Enrollment.enrollDate    date     일 │ ← 정밀 시점 (연속형, 산술 가능)
   가늚  └──────────────────────────────────────┘
                          ↓
              (없음) drop date, 성적 확정일 …
                     상태 전이 이력 = 모델의 공백
```

- `enrollDate`가 date인 이유: 수강신청 **시점**을 기록해 **범위 비교·정렬·날짜 산술**을 타입 차원에서 보장하기 위해서다.
- string 날짜와의 차이는 "가능/불가능"이 아니라 **보장의 주체**다. date는 스키마가 보장하고, string은 데이터 입력자를 믿는 것이다. 다중 소스 통합 환경에서 이 차이는 치명적이다.
- `semester`(범주)와 `enrollDate`(연속)는 **역할이 다른 두 시간 표현**이며, `enrollmentYear`까지 합쳐 년·학기·일의 세 축을 이룬다.
- 단, 이 모델의 date는 `enrollDate` 하나뿐이라 **시작 시점만** 있고 철회·성적확정 같은 이후 전이 시점은 표현되지 않는다.
