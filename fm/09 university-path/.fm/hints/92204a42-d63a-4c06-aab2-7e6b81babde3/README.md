# University System 학습 경로가 모델링하는 대상

## 질문

University System 학습 경로가 모델링하는 대상은 무엇인가?

## 정답

**학생(Student), 강좌(Course), 수강신청(Enrollment), 교수(Professor), 학과(Department)를 연결하는 대학 관리 시스템(university management system)의 데이터 모델**이다. 학사 행정 전반을 온톨로지로 표현하는 것이 목표다.

---

## 1. 시나리오 한 줄 요약

> "당신은 **대학 관리 시스템(university management system)**의 데이터 모델을 설계하고 있다."

즉, 이 학습 경로의 대상은 특정 앱이나 특정 데이터베이스 테이블이 아니라 **학사 행정(academic administration) 도메인 전체**다. 최종 산출물은 **엔티티 5개 · 관계 6개**로 구성된 온톨로지다.

## 2. 대학이 추적하는 다섯 가지 대상

원문이 명시한, 이 기관이 추적(track)하는 항목은 다음과 같다.

| 대상 | 무엇을 추적하는가 |
|---|---|
| **Students** | 등록 상태(enrollment status), GPA, 학사 경고/우등 등 academic standing |
| **Courses** | 학점(credit hours), 난이도 레벨(level), 선수과목(prerequisites) |
| **Enrollments** | 어떤 학생이 어떤 강좌를 수강하는지 + 그 성적(grade) |
| **Professors** | 담당 강좌, 직급(rank), 정년보장 여부(tenure), 오피스아워 |
| **Departments** | 학위 프로그램 조직, 교수진 소속 관리 |

## 3. 데이터가 흩어져 있는 곳 (왜 온톨로지가 필요한가)

이 데이터들은 하나의 시스템에 모여 있지 않고 여러 시스템에 분산되어 있다.

- **SIS** (Student Information System, 학사정보시스템)
- **LMS** (Learning Management System, 학습관리시스템)
- **HR** (인사 시스템 — 교수 정보)
- **Academic planning databases** (학사 기획 DB)

이 사일로를 가로지르는 질문이 온톨로지의 존재 이유다. 원문의 대표 질문:

> **"수강생의 50% 이상이 C 미만을 받은 강좌를 가르치는 교수가 소속된 학과는 어디인가?"**

이 질문은 학과 기록 + 교수 배정 + 강좌 개설 + 학생 성적을 동시에 건드린다. 온톨로지로 표현하면 단 한 줄의 그래프 경로가 된다.

```
Department → Professor → Course → Enrollment (grade < C) ← Student
```

## 4. 3단계로 쌓아 올리는 모델

| 단계 | 추가 엔티티 | 누적 | 핵심 개념 |
|---|---|---|---|
| 1 | Student, Course, Enrollment | 3 | 정션 엔티티, 다대다 해소 |
| 2 | + Professor | 4 | 이행적(transitive) 질의, 불리언 속성 |
| 3 | + Department | 5 | 조직 계층, 허브 엔티티 |

### 최종 관계 6개

| 관계 | 방향 | 카디널리티 |
|---|---|---|
| `enrolls_in` | Student → Enrollment | 1:N |
| `for_course` | Enrollment → Course | N:1 |
| `teaches` | Professor → Course | 1:N |
| `advises` | Professor → Student | 1:N |
| `belongs_to` | Professor → Department | N:1 |
| `offers` | Department → Course | 1:N |

## 5. 이 경로가 가르치는 핵심 개념 4가지

- **Junction entities (정션 엔티티)** — Enrollment가 Student–Course의 다대다 관계를 해소한다. 학생은 여러 강좌를 듣고 강좌는 여러 학생을 받는데, 그 "연결 자체"에 grade·semester·status라는 속성이 붙기 때문에 관계를 일급 엔티티로 승격시킨다.
- **Academic hierarchies (학사 계층)** — Department가 교수와 강좌를 조직한다. Department는 아래로 Professor(`belongs_to`)와 Course(`offers`) 양쪽에 연결되는 **허브 엔티티**여서 학과 단위 집계 질의의 기준점이 된다.
- **Grade tracking (성적 추적)** — 문자 성적(letter grade)과 GPA를 온톨로지 속성으로 다룬다. GPA는 float(0.0~4.0)라 임계값·평균 질의가 가능하다.
- **Temporal data (시간 데이터)** — semester, enrollDate, academic year 등 시점 정보를 모델에 포함한다.

## 6. 완성 모델이 답할 수 있는 질문 예시

| 질문 | 그래프 경로 |
|---|---|
| 평균 학생 GPA가 가장 높은 학과는? | Department → Course ← Enrollment ← Student |
| 자기 학과 밖 강좌를 가르치는 교수는? | Professor → Department vs Professor → Course → Department |
| 학과별 수강률은? | Department → Course ← Enrollment (count) / Course.maxEnrollment |
| 정년보장 교수가 가장 많은 학과는? | Department ← Professor (tenured=true, count) |

GQL 예시 (성적이 부진한 학과 찾기):

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

## 7. 암기 포인트

- 대상 = **대학 관리 시스템의 데이터 모델** (특정 대학·특정 DB가 아니라 학사 행정 도메인)
- 엔티티 = **Student, Course, Enrollment, Professor, Department** (5개)
- 관계 = **6개**
- 한 문장 요약: *"학생·강좌·수강신청·교수·학과를 잇는 학사 행정 온톨로지."*

## 8. 흔한 오답과 구분

- ❌ "학생 성적 관리 시스템" — Enrollment/성적은 5개 중 하나일 뿐, 교수·학과까지 포함하는 전체 행정 모델이다.
- ❌ "LMS(학습관리시스템) 설계" — LMS는 데이터 출처 중 하나이고, 모델링 대상은 그 위를 가로지르는 통합 온톨로지다.
- ❌ "강의 시간표 스케줄링" — 시간표 최적화가 아니라 개체·관계의 의미 구조 표현이 목적이다.
