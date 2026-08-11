# Healthcare System

Model a patient care system — patients, providers, appointments, diagnoses, and prescriptions.

Source: content/learn/healthcare-path (4 articles merged)

---

# Scenario Overview

Meet the Healthcare System — a patient care platform that needs an ontology to connect patients, providers, diagnoses, and treatments.

## The scenario

You are designing the data model for a **healthcare management system**. The hospital network tracks:

- **Patients** with medical records, blood types, and allergy information
- **Providers** (doctors, specialists) with licenses and departmental affiliations
- **Appointments** scheduling patient visits with specific providers
- **Diagnoses** recording medical conditions with ICD codes and severity levels
- **Prescriptions** tracking medication orders, dosages, and refills

Data is spread across electronic health records (EHR), scheduling systems, pharmacy databases, and billing platforms.

## Why an ontology?

A clinical question like **"Which patients diagnosed with severe conditions by cardiology providers still have prescriptions with zero refills remaining?"** crosses patient records, diagnosis history, provider specialties, and pharmacy data.

With an ontology, this maps to: `Patient → Diagnosis (severity=severe) ← Provider (specialty=Cardiology)` and `Diagnosis → Prescription (refillsRemaining=0)`.

## What we'll build

| Step | Entities | What you'll learn |
|---|---|---|
| 1 | Patient, Provider, Appointment | Core clinical entities, scheduling relationships |
| 2 | + Diagnosis | Medical conditions, multi-source relationships |
| 3 | + Prescription | Treatment chain, completing the care cycle |

By the end, you'll have a 5-entity, 6-relationship ontology covering the complete patient care journey from appointment to treatment.

## Key concepts

- **Clinical workflows** — appointment scheduling, diagnosis, treatment
- **Shared relationships** — both Patient and Provider connect to Appointment
- **Care chains** — Patient → Diagnosis → Prescription
- **Standardized identifiers** — MRN (Medical Record Number), ICD codes, Rx numbers

Let's start with the care delivery foundation.

---

# Care Delivery

Define Patient, Provider, and Appointment — the core entities that power healthcare scheduling and care delivery.

## The care delivery foundation

Healthcare delivery revolves around three concepts:

- **Patient** — who is receiving care?
- **Provider** — who is delivering care?
- **Appointment** — when and where does the care happen?

These three entities capture the scheduling and delivery of healthcare. Every diagnosis and treatment flows from an appointment.

## Defining the entities

### Patient

| Property | Type | Identifier? |
|---|---|---|
| `patientId` | string | ✓ |
| `mrn` | string | |
| `dateOfBirth` | date | |
| `bloodType` | string | |
| `allergies` | string | |

The `mrn` (Medical Record Number) is the hospital's internal identifier. The `patientId` is used as the ontology identifier, while `mrn` is a domain-specific property that maps to the EHR system.

### Provider

| Property | Type | Identifier? |
|---|---|---|
| `providerId` | string | ✓ |
| `name` | string | |
| `specialty` | string | |
| `licenseNumber` | string | |
| `department` | string | |

The `specialty` and `department` properties enable filtering providers by clinical domain — essential for referral and routing queries.

### Appointment

| Property | Type | Identifier? |
|---|---|---|
| `appointmentId` | string | ✓ |
| `scheduledTime` | datetime | |
| `duration` | integer (minutes) | |
| `type` | string | |
| `status` | string | |

The `duration` property uses an integer with a minutes unit — enabling scheduling calculations and utilization analysis.

## Relationships

- **has_appointment** — `Patient` → `Appointment` (one-to-many)
  A patient can have many appointments over time.

- **sees** — `Provider` → `Appointment` (one-to-many)
  A provider handles many appointments.

> **Shared entity pattern:** Appointment connects to *both* Patient and Provider. It's the meeting point where two independent entities interact. This pattern is common whenever two actors participate in the same event.

## The graph so far

*Patient and Provider both connect to Appointment — the meeting point of care delivery.*

## What we learned

- **Shared entities** (Appointment) connect two independent actors (Patient, Provider)
- **Duration properties** use integers with units (minutes, hours, days)
- **Domain-specific identifiers** (MRN) coexist with ontology identifiers (patientId)
- The scheduling triangle (Patient–Appointment–Provider) is the healthcare foundation

```quiz
Q: Why is Appointment connected to both Patient and Provider instead of just one?
- To make the graph look more complete
- Because Appointment is a shared entity — it represents the interaction point between the two actors [correct]
- Because every entity must have at least two relationships
- Because Patient and Provider have the same properties
> An appointment is inherently a collaborative event involving both a patient and a provider. Modelling both relationships captures the full scheduling picture and enables queries from either perspective: "When is the patient's next visit?" or "How many patients does this provider see per day?"
```

Next, we'll add Diagnosis to track medical conditions.

---

# Diagnoses

Add Diagnosis to track medical conditions — connecting patients to their clinical findings and providers to their assessments.

## Recording clinical findings

An appointment produces clinical findings — what condition does the patient have? The **Diagnosis** entity captures these findings with standardized coding.

Adding Diagnosis enables:
- "Which patients have been diagnosed with diabetes?"
- "Which provider identified the most severe conditions last quarter?"
- "What are the most common diagnoses by department?"

## Diagnosis entity

| Property | Type | Identifier? |
|---|---|---|
| `diagnosisId` | string | ✓ |
| `icdCode` | string | |
| `description` | string | |
| `severity` | string | |
| `diagnosedDate` | date | |

The `icdCode` property holds the standardized ICD (International Classification of Diseases) code — a globally recognized coding system. This makes the ontology interoperable with insurance, billing, and research systems.

## New relationships

- **diagnosed_with** — `Patient` → `Diagnosis` (one-to-many)
  A patient can have multiple diagnoses over their medical history.

- **diagnoses** — `Provider` → `Diagnosis` (one-to-many)
  A provider records diagnoses based on their clinical assessment.

> **Dual authorship:** Diagnosis connects to both Patient (who has the condition) and Provider (who identified it). This dual connection enables both patient-centric views ("all of my conditions") and provider-centric views ("all conditions I've identified").

## The growing graph

*Diagnosis joins the graph with connections to both Patient and Provider. The diff highlights what's new.*

## What we learned

- **Standardized codes** (ICD) make ontologies interoperable with external systems
- **Dual-connected entities** (Patient → Diagnosis ← Provider) capture both perspectives
- **Severity properties** enable risk stratification and clinical prioritization
- The graph now supports both scheduling queries (via Appointment) and clinical queries (via Diagnosis)

```quiz
Q: Why is the ICD code property important for the Diagnosis entity?
- It makes the diagnosis identifier shorter
- It provides a globally standardized coding system that enables interoperability with insurance, billing, and research systems [correct]
- ICD codes are required by all ontology formats
- It prevents duplicate diagnoses from being recorded
> ICD (International Classification of Diseases) codes are the universal standard for classifying medical conditions. Including them in the ontology enables interoperability — the same code means the same condition across EHRs, insurance claims, clinical trials, and public health systems.
```

Next, we'll add Prescription to complete the treatment chain.

---

# Complete Care Model

Add Prescription to complete the healthcare ontology — connecting diagnoses to treatments and closing the care cycle.

## The treatment chain

The final piece of the healthcare puzzle is **Prescription** — the treatment response to a diagnosis. This closes the care cycle: appointment → diagnosis → treatment.

## Prescription entity

| Property | Type | Identifier? |
|---|---|---|
| `rxNumber` | string | ✓ |
| `medication` | string | |
| `dosage` | string | |
| `frequency` | string | |
| `refillsRemaining` | integer | |

The identifier is `rxNumber` (prescription number) — a pharmacy-standard identifier. The `refillsRemaining` integer enables refill tracking and medication adherence monitoring.

## New relationships

- **treated_by** — `Diagnosis` → `Prescription` (one-to-many)
  A diagnosis can lead to multiple prescriptions (e.g., multiple medications for the same condition).

- **prescribes** — `Provider` → `Prescription` (one-to-many)
  A provider writes prescriptions for their patients.

> **Care chain:** The complete path is now `Patient → Diagnosis → Prescription`, with `Provider` connecting at every stage (sees appointments, makes diagnoses, writes prescriptions). This reflects the real clinical workflow.

## The complete graph

*The complete Healthcare ontology: 5 entities, 6 relationships. The care chain flows from Patient through Diagnosis to Prescription.*

## What the complete model enables

| Question | Graph path |
|---|---|
| Which patients need prescription refills? | Patient → Diagnosis → Prescription (refillsRemaining=0) |
| Which providers prescribe the most medications? | Provider → Prescription (count) |
| Which severe diagnoses have no treatment yet? | Diagnosis (severity=severe) with no → Prescription |
| Which specialists diagnose conditions they also prescribe for? | Provider → Diagnosis AND Provider → Prescription |

## GQL query example

Find patients with severe diagnoses whose prescriptions are running out:

```gql
MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
```

## What we built

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | Patient, Provider, Appointment | 3 | Shared entities, scheduling |
| 2 | Diagnosis | 4 | Standardized codes, dual connections |
| 3 | Prescription | 5 | Care chains, treatment tracking |

## Key takeaways

1. **Shared entities** (Appointment, Diagnosis) connect multiple actors
2. **Standardized codes** (ICD, Rx) enable cross-system interoperability
3. **Care chains** (Patient → Diagnosis → Prescription) model clinical workflows
4. **Provider connects at every stage** — reflecting the central role in healthcare delivery
5. **Integer properties** (refillsRemaining, duration) enable operational queries

```quiz
Q: How does the Provider entity connect across the complete healthcare ontology?
- Provider only connects to Appointment
- Provider connects to Appointment, Diagnosis, and Prescription — reflecting their role at every stage of care [correct]
- Provider connects to Patient directly
- Provider connects to Prescription only
> Provider is the most connected entity in this ontology — they see appointments, make diagnoses, and write prescriptions. This reflects the real-world workflow where healthcare providers are involved at every stage of the care delivery chain.
```

You've completed the Healthcare System learning path! Load any step from the [catalogue](#/catalogue) to explore it interactively.
