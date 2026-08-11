# MRN(Medical Record Number)이란 무엇이며 온톨로지에서 어떤 역할을 하는가?

## 한 줄 답

**MRN은 병원의 내부 식별자(hospital's internal identifier)다.** Healthcare 온톨로지에서 식별자 역할은 `patientId`가 담당하고, `mrn`은 **EHR 시스템에 매핑되는 도메인 고유 속성(domain-specific property)** 으로 나란히 공존한다.

---

## 원문 근거

학습 경로의 `Care Delivery` 단계에서 정의한 **Patient** 엔티티:

| Property | Type | Identifier? |
|---|---|---|
| `patientId` | string | ✓ |
| `mrn` | string | |
| `dateOfBirth` | date | |
| `bloodType` | string | |
| `allergies` | string | |

> The `mrn` (Medical Record Number) is the hospital's internal identifier. The `patientId` is used as the ontology identifier, while `mrn` is a domain-specific property that maps to the EHR system.

그리고 이 단계의 **What we learned** 에 핵심 원칙이 명시되어 있다.

> **Domain-specific identifiers** (MRN) coexist with ontology identifiers (patientId)

즉 이 카드가 묻는 것은 "MRN의 정의" 하나가 아니라, **식별자가 두 개 존재할 때 각각의 역할 분담**이다.

---

## MRN이란 (실무 관점)

- **정의**: 특정 병원(또는 병원 네트워크)이 환자 한 명의 진료기록에 부여하는 내부 번호. 차트 번호, 등록번호 등으로도 불린다.
- **발급 주체**: 병원 자신. 국가나 표준화 기구가 아니다.
- **핵심 성질 — 전역 고유하지 않다(not globally unique)**: A 병원의 MRN `12345`와 B 병원의 MRN `12345`는 **아무 관계가 없는 서로 다른 환자**다. MRN은 "발급 기관 + 번호"의 쌍으로만 의미가 성립한다.
- **불안정할 수 있다**: 같은 환자가 응급실·외래에서 중복 등록되어 MRN이 두 개 생기거나(duplicate), 나중에 병합(merge)되면서 한쪽 MRN이 폐기·별칭 처리될 수 있다. 병원 인수·합병 시 번호 체계 자체가 재부여되기도 한다.
- **그래서 EMPI가 필요하다**: 여러 시스템(EHR, 검사, 청구)의 MRN들을 매칭·중복제거해 환자 1명에 대한 **상위(enterprise) 단일 ID**를 만들고, 각 시스템의 MRN을 그 아래에 매핑해 두는 것이 EMPI(Enterprise Master Patient Index)의 일이다.

### 온톨로지의 `patientId` ≒ EMPI의 상위 ID

이 구조가 온톨로지 설계와 정확히 같은 모양이다.

```
patientId (온톨로지 식별자, 시스템 중립·안정·전역 고유)
   │
   ├── mrn            → 병원 EHR 시스템의 레코드로 조인
   ├── (insuranceId)  → 청구 시스템
   └── (labPatientId) → 검사 시스템
```

- `patientId`: **그래프 내부의 정체성**. 관계(`has_appointment`, `diagnosed_with` 등)가 붙는 앵커이자 조인 키. 절대 바뀌지 않아야 한다.
- `mrn`: **외부 시스템으로 나가는 포인터**. 소스 데이터를 온톨로지에 파이프라인으로 태울 때 EHR 레코드와 맞추는 열쇠이고, 임상 사용자가 "차트 번호로 찾아주세요"라고 할 때 필요한 검색 속성이다.

---

## 왜 MRN을 식별자로 쓰지 않는가

MRN을 온톨로지 식별자로 승격시키면 다음이 깨진다.

| 문제 | 설명 |
|---|---|
| **충돌** | 여러 병원 데이터를 통합하면 MRN이 겹친다. 서로 다른 환자가 같은 노드로 합쳐질 수 있다. |
| **불변성 위반** | 중복 병합·번호 재부여로 MRN이 바뀌면, 그 값을 참조하던 모든 관계(Appointment, Diagnosis, Prescription)의 링크가 끊긴다. |
| **시스템 종속** | EHR을 교체하면 MRN 체계가 함께 바뀐다. 온톨로지가 특정 벤더에 묶인다. |
| **결측 허용 불가** | 원문 표에서 `mrn`은 식별자가 아니므로 값이 없어도 된다(외부 유입 환자, 아직 EHR 미등록 등). 식별자는 항상 있어야 한다. |

이것이 이 학습 경로가 다른 단계에서 보여주는 식별자 선택 감각과도 일관된다. `Diagnosis`는 `diagnosisId`를 식별자로 쓰고 `icdCode`는 (표준 코드지만) 속성으로 둔다 — ICD 코드는 같은 질환을 가진 수천 명이 공유하므로 애초에 식별자가 될 수 없다. 반대로 `Prescription`은 `rxNumber`를 **식별자로** 채택한다 — 약국 표준으로 처방 1건당 1개가 부여되어 고유성이 성립하기 때문이다.

> 즉 규칙은 "도메인 코드는 무조건 속성"이 아니라, **엔티티 1개를 안정적·고유하게 가리키는가**를 보고 식별자를 정하는 것이다. MRN은 병원 범위에서만 고유해서 탈락한다.

---

## 표준에서의 동일한 패턴 (HL7 FHIR)

FHIR도 정확히 같은 분리를 강제한다.

- `Patient.id` — 서버 내부의 리소스 논리 ID. 온톨로지의 `patientId`에 대응.
- `Patient.identifier[]` — 업무 식별자 목록. MRN은 여기에 들어간다.
  - `type` = 코드 **`MR`** (Medical record number, ValueSet `identifier-type`)
  - `system` = 그 번호를 발급한 기관의 네임스페이스 URI
  - `value` = 실제 번호
  - `assigner` = 발급 기관 참조

FHIR 가이드는 "MRN을 리소스의 `id`로 쓰지 말고 `identifier` 목록에서 관리하라"고 명시한다. `system` 없이 `value`만 있는 MRN은 의미가 불완전하다는 점이 바로 위에서 말한 "전역 고유하지 않음"의 표준 레벨 표현이다.

참고로 미국에는 전국 단위 환자 고유번호(national patient identifier)가 법으로 막혀 있어 MRN + EMPI 매칭에 의존한다. 한국은 주민등록번호가 사실상 그 역할을 하지만, 개인정보 취급 부담 때문에 온톨로지 식별자로 직접 쓰는 것은 권장되지 않고 별도 대체키(`patientId`)를 두는 편이 안전하다.

---

## 정리 (암기 포인트)

1. **MRN = 병원 내부 식별자.** 발급 주체가 병원이고, 병원 범위 안에서만 고유하다.
2. **온톨로지 식별자는 `patientId`.** 관계가 붙는 앵커이므로 안정적이고 시스템 중립이어야 한다.
3. **`mrn`은 도메인 고유 속성으로 공존한다.** EHR 시스템으로 매핑하는 조인 키 겸 검색 속성.
4. 이 "도메인 식별자 ↔ 온톨로지 식별자 공존" 패턴은 EMPI, FHIR `Patient.identifier`(type `MR`)와 같은 발상이다.
