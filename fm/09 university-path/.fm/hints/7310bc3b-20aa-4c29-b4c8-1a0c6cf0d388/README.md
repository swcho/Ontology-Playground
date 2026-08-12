# 학사 기록의 근본 질문과 세 엔티티

## 질문

학사 기록(academic record)의 근본 질문은 무엇이며, 어떤 엔티티들이 답하는가?

## 답

**"어떤 학생이 어떤 강좌를 듣고 어떤 성과를 내는가?"**
(*which students take which courses, and how do they perform?*)

이 질문에 **Student**, **Course**, **Enrollment** 세 엔티티가 답한다.

| 엔티티 | 담당하는 물음 | 역할 |
|---|---|---|
| **Student** | 누가 배우는가? (who is learning?) | 학습 주체 |
| **Course** | 무엇을 가르치는가? (what is being taught?) | 교육 대상(교과) |
| **Enrollment** | 어떤 성과를 냈는가? | 학생과 강좌를 성적과 함께 잇는 기록 |

---

## 왜 이 질문이 "근본"인가

대학 시스템 온톨로지는 최종적으로 Student, Course, Enrollment, Professor, Department의
**5 엔티티 / 6 관계**로 완성된다. 하지만 학습 경로는 이 5개를 한 번에 늘어놓지 않고
3단계로 쌓아 올린다.

| Step | 추가 엔티티 | 누적 | 핵심 개념 |
|---|---|---|---|
| 1 | Student, Course, Enrollment | 3 | 정션 엔티티, 다대다 |
| 2 | Professor | 4 | 전이적 질의, 불리언 속성 |
| 3 | Department | 5 | 조직 계층, 허브 엔티티 |

Step 1의 세 엔티티가 **학사 코어(academic core)** 다. 교수(Professor)나 학과(Department)가
없어도 "누가 무엇을 듣고 어떤 성적을 받았는가"는 성립한다. 반대로 Enrollment가 없으면
Professor도 Department도 성적 데이터에 도달할 수 없다. 그래서 이 세 엔티티가
**모델의 최소 완결 단위**이자 근본 질문의 답이 된다.

기억법: **누가(Student) - 무엇을(Course) - 어떻게 됐나(Enrollment)**.

---

## 각 엔티티 상세

### Student — 누가 배우는가

| Property | Type | Identifier? |
|---|---|---|
| `studentId` | string | ✓ |
| `name` | string | |
| `gpa` | float | |
| `enrollmentYear` | integer | |
| `major` | string | |

- `gpa`가 **float**인 이유: 평점은 0.0~4.0의 연속값이다. 이 집계 지표 덕분에
  "학사경고 대상", "우등생 명단(honor roll)" 같은 **임계값 기반 질의**가 가능해진다.
- `enrollmentYear`는 integer로 학년/입학 코호트 분석에 쓰인다.

### Course — 무엇을 가르치는가

| Property | Type | Identifier? |
|---|---|---|
| `courseId` | string | ✓ |
| `title` | string | |
| `credits` | integer | |
| `level` | string | |
| `maxEnrollment` | integer | |

- `level`(100, 200, 300, 400)은 강좌 난이도와 선수과목 체계를 나타낸다.
- `maxEnrollment`(integer)는 **정원 계획(capacity planning)** 용도다.
  실제 수강 인원(Enrollment 개수)과 나눠서 학과별 충원율을 계산할 수 있다.
- `credits`(integer)는 학점·이수 부담(workload) 계산에 쓰인다.

### Enrollment — 둘을 성적과 함께 잇는 기록

| Property | Type | Identifier? |
|---|---|---|
| `enrollmentId` | string | ✓ |
| `semester` | string | |
| `grade` | string | |
| `enrollDate` | date | |
| `status` | string | |

Enrollment는 **정션 엔티티(junction entity)** 다. Student와 Course를 잇되,
그 연결 자체에만 속하는 부가 정보(grade, semester, status)를 실어 나르기 위해 존재한다.

---

## 관계 (Relationships)

- **enrolls_in** — `Student` → `Enrollment` (one-to-many)
  한 학생은 여러 학기에 걸쳐 여러 수강 기록을 가진다.
- **for_course** — `Enrollment` → `Course` (many-to-one)
  각 수강 기록은 정확히 하나의 강좌를 가리킨다.

즉 학사 코어의 경로는 **Student → Enrollment → Course** 다.
(Student와 Course 사이에 직접 간선이 없다는 점이 핵심이다.)

```
  Student ──enrolls_in──▶ Enrollment ──for_course──▶ Course
   누가 배우나            성적/학기/상태            무엇을 가르치나
```

---

## 왜 Enrollment를 별도 엔티티로 만드는가 (정션 엔티티 패턴)

> 두 엔티티가 **속성을 가진 다대다 관계**를 맺을 때는 정션 엔티티를 만든다.
> 한 학생은 여러 강좌를 듣고, 한 강좌는 여러 학생을 받는다. Enrollment가 그 사이에서
> 성적, 학기, 상태를 짊어진다. 온톨로지 설계에서 가장 흔한 패턴 중 하나다.

Student–Course를 직접 연결하면 안 되는 이유:

1. **성적을 놓을 자리가 없다.** `grade`는 학생의 속성도(과목마다 다르므로),
   강좌의 속성도(학생마다 다르므로) 아니다. 오직 "그 학생의 그 수강"에만 속한다.
2. **재수강을 구분할 수 없다.** 같은 학생이 같은 강좌를 다른 학기에 다시 들으면
   직접 관계로는 두 사건이 겹쳐 버린다. `semester` + `enrollmentId`가 이를 분리한다.
3. **상태 추적이 불가능하다.** 수강신청/철회(withdrawn)/완료 같은 `status` 전이는
   연결 자체가 1급 엔티티일 때만 기록·질의할 수 있다.

핵심 요지: **관계 자체를 1급 엔티티로 승격**시켜야
"이 학생이 이 강좌를 이번 학기에 들어 무슨 성적을 받았나?"에 답할 수 있다.
이 질문의 답은 양쪽 끝점이 아니라 **연결 위에 있는 속성**이기 때문이다.

---

## 이 코어가 이후 단계를 떠받친다

Step 2에서 Professor(teaches → Course, advises → Student),
Step 3에서 Department(offers → Course, ← belongs_to Professor)가 붙는데,
이들이 성적 데이터에 닿는 경로는 전부 Enrollment를 통과한다.

- 전이적 질의: `Professor → Course ← Enrollment ← Student`
  → "종신교수의 수업을 듣는 학생은 누구인가?"
- 학과 단위 집계: `Department → Course ← Enrollment ← Student`
  → "평균 GPA가 가장 높은 학과는?"

경로에 나타나는 화살표 방향(`←`)에 주의할 것. Enrollment가 Course를 가리키므로
Course에서 Enrollment로 갈 때는 관계를 **역방향으로 순회**한다.

전체 학습 경로가 던지는 동기 질문 —
*"등록 학생의 50% 이상이 C 미만을 받은 강좌를 가르치는 교수가 있는 학과는?"* —
역시 `Department → Professor → Course → Enrollment(grade < C) ← Student`로 풀린다.

GQL 예시:

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

---

## 자주 하는 실수

- **"세 엔티티"를 Student, Course, Professor로 착각** — Professor는 Step 2에서
  추가되는 교수진 차원이다. 학사 기록 코어에는 들어가지 않는다.
- **Enrollment를 단순 관계(edge)로 취급** — 속성을 가진 1급 엔티티다.
- **grade를 Student나 Course에 올려두기** — 어느 쪽에도 속하지 않는 속성이다.
- **엔티티가 세 개여야 한다는 규칙이 있다고 오해** — 정션 엔티티가 필요한 이유는
  개수 규칙이 아니라 **연결에 속성이 있기 때문**이다.

---

## 한 줄 요약

학사 기록의 근본 질문은 "어떤 학생이 어떤 강좌를 듣고 어떤 성과를 내는가"이며,
Student(누가) · Course(무엇을) · Enrollment(성적을 실은 연결 기록)가
`Student → Enrollment → Course` 형태로 이에 답한다.
