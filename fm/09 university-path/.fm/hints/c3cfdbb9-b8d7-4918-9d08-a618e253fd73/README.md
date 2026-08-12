# Course의 `maxEnrollment` 속성

## 질문

Course의 `maxEnrollment` 속성의 용도는?

## 답

강좌의 **최대 수강 인원**을 정수(integer)로 담아 **정원 계획(capacity planning)** 을 가능하게 한다.
실제 수강 건수(Enrollment count)와 비교하면 학과별 **충원율(enrollment rate)** 을 계산할 수 있다.

---

## 1. Course 엔티티 안에서의 위치

University System 온톨로지의 Course 엔티티는 다음과 같이 정의된다.

| Property | Type | Identifier? |
|---|---|---|
| `courseId` | string | ✓ |
| `title` | string | |
| `credits` | integer | |
| `level` | string | |
| `maxEnrollment` | integer | |

원문의 설명은 짧지만 핵심을 담고 있다.

> The `level` property (100, 200, 300, 400) indicates course difficulty and prerequisites.
> **The `maxEnrollment` integer enables capacity planning.**

즉 `maxEnrollment`는 "이 강좌에 최대 몇 명까지 등록할 수 있는가"를 나타내는 **상한값(capacity)** 이다.

## 2. 왜 정수(integer) 타입인가

학습 경로의 "What we learned"에서 속성 타입별 역할을 이렇게 정리한다.

- **Float 속성**(`Student.gpa`) → 집계 계산과 임계값(threshold) 비교
- **Integer 속성**(`Course.credits`, `Course.maxEnrollment`) → **정원(capacity)과 학습 부담(workload) 계획**
- **Boolean 속성**(`Professor.tenured`) → 예/아니오 범주 필터링

정원은 "37.5명" 같은 값이 존재할 수 없는 **셀 수 있는 양(countable)** 이므로 integer가 자연스럽다.
그리고 integer이기 때문에 `COUNT()` 결과와 **직접 산술 비교·나눗셈**이 가능하다. 이것이 문자열로
"30명 정원" 같이 적지 않고 정수 타입을 고른 실질적인 이유다.

## 3. 핵심 활용: 충원율(enrollment rate) 계산

`maxEnrollment` 하나만으로는 "정원"이라는 정적인 사실밖에 모른다.
가치는 **Enrollment 실적과 비교할 때** 나온다.

학습 경로의 마지막 단계(Department 추가 이후) "What the complete model enables" 표에 다음 항목이 있다.

| Question | Graph path |
|---|---|
| What is the enrollment rate for each department? | `Department → Course ← Enrollment` (count) / `Course.maxEnrollment` |

읽는 방법:

1. `Department -[:offers]-> Course` 로 학과가 개설한 강좌들을 모은다.
2. 각 Course에 대해 `Enrollment -[:for_course]-> Course` 를 역방향으로 타고 들어와 **실제 수강 건수**를 센다.
3. 그 합계를 `Course.maxEnrollment` 의 합계로 나눈다 → **학과별 충원율**.

```
충원율 = COUNT(Enrollment) / SUM(Course.maxEnrollment)
```

분자는 **그래프 탐색으로 세는 값**, 분모는 **엔티티에 저장된 속성값**이라는 점이 포인트다.
즉 `maxEnrollment`는 "실적과 대비할 기준선(denominator)"을 온톨로지 안에 심어두는 속성이다.

### GQL 형태의 예시

원문 스타일에 맞춘 의사 쿼리:

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)
RETURN d.name,
       COUNT(e) AS actual,
       SUM(c.maxEnrollment) AS capacity,
       COUNT(e) * 1.0 / SUM(c.maxEnrollment) AS enrollment_rate
ORDER BY enrollment_rate DESC
```

여기서 실제 수강 건수가 Course에 직접 붙어 있지 않고 **Enrollment junction entity**를 거쳐 세어진다는 점을
같이 기억해 두면 좋다. Student–Course는 다대다이고, 그 사이를 Enrollment가 grade/semester/status를 들고
연결한다.

## 4. 정원 계획(capacity planning)으로 답할 수 있는 질문들

`maxEnrollment`가 있으면 다음과 같은 운영 질문에 답할 수 있다.

- **초과·미달 감지**: `COUNT(Enrollment) > c.maxEnrollment` → 정원 초과 강좌, `< 0.5 * maxEnrollment` → 폐강 후보
- **분반 필요 판단**: 수요가 정원을 반복적으로 넘는 강좌는 섹션을 늘려야 한다
- **강의실 배정**: 정원에 맞는 크기의 강의실·조교 수를 산정
- **학과 자원 배분**: 학과별 충원율이 낮으면 커리큘럼 재편, 높으면 교원 충원 근거
- **`credits`와 결합**: `credits × maxEnrollment` 로 강좌가 만들어내는 총 학점 수요/교수 부담 추정

## 5. 헷갈리기 쉬운 포인트

- **`maxEnrollment`는 상한이지 현재값이 아니다.** 현재 몇 명이 듣는지는 Course에 저장되지 않는다.
  그것은 Enrollment 레코드를 세어서 얻는 **파생값(derived)** 이다. 변하는 값을 엔티티 속성으로 중복
  저장하지 않고, 변하지 않는 정책값(정원)만 속성으로 두는 것이 이 모델의 설계 의도다.
- **`level`과 혼동하지 말 것.** `level`(100/200/300/400)은 난이도·선수과목 수준이고,
  `maxEnrollment`는 인원 상한이다. 둘 다 Course의 속성이지만 목적이 다르다.
- **`credits`와도 다르다.** `credits`는 학점(= 학생 한 명의 학습 부담),
  `maxEnrollment`는 인원(= 강좌의 수용 규모)이다. 원문은 둘을 묶어
  "capacity and workload planning"이라 표현했는데, capacity ↔ `maxEnrollment`,
  workload ↔ `credits` 로 대응시켜 기억하면 된다.

## 6. 한 줄 요약

> `maxEnrollment` = 강좌 정원(정수 상한). 저장된 정원 ÷ 그래프에서 센 실제 Enrollment 수 →
> 정원 계획과 학과별 충원율 분석의 기준선.

## 참고 (출처)

- `../../assets/university-path.md`
  - "Academic Core" → Course 속성 표와 "The `maxEnrollment` integer enables capacity planning."
  - "Academic Core" → What we learned: "Integer properties (credits, maxEnrollment) enable capacity and workload planning"
  - "Department" 단계 → What the complete model enables:
    "What is the enrollment rate for each department? — Department → Course ← Enrollment (count) / Course.maxEnrollment"
