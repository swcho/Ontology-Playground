# Smart Manufacturing

Model an IoT-enabled factory — machines, sensors, work orders, parts, and quality checks.

Source: content/learn/manufacturing-path (4 articles merged)

---

# Scenario Overview

Meet the Smart Manufacturing system — an IoT-enabled factory that needs an ontology to connect machines, sensors, production, and quality control.

## The scenario

You are designing the data model for a **smart manufacturing facility**. The factory manages:

- **Machines** on the factory floor with maintenance schedules and operational status
- **Sensors** collecting real-time data — temperature, vibration, pressure readings
- **Work Orders** tracking production jobs with priorities and deadlines
- **Parts** representing components being manufactured with specifications and tolerances
- **Quality Checks** recording inspection results, pass/fail status, and defect codes

Data flows from IoT sensors, MES (Manufacturing Execution Systems), ERP platforms, and quality management databases.

## Why an ontology?

A production question like **"Which machines with abnormal sensor readings produced parts that failed quality checks last week?"** crosses IoT telemetry, production schedules, part tracking, and inspection records.

With an ontology, this maps to: `Machine → Sensor (reading > threshold)` and `Machine → Work-Order → Part → Quality-Check (passed=false)`.

## What we'll build

| Step | Entities | What you'll learn |
|---|---|---|
| 1 | Machine, Sensor | IoT relationships, telemetry hierarchies |
| 2 | + Work-Order, Part | Production tracking, manufacturing chains |
| 3 | + Quality-Check | Inspection loops, closing the production cycle |

By the end, you'll have a 5-entity, 5-relationship ontology covering sensor monitoring through quality assurance.

## Key concepts

- **IoT hierarchies** — machines own sensors, readings flow upward
- **Production chains** — work orders produce parts
- **Quality loops** — inspections feed back into production decisions
- **Operational status** — real-time state tracking (running, idle, maintenance)

Let's start with the factory floor.

---

# Factory Floor

Define Machine and Sensor — the IoT foundation that monitors factory equipment in real time.

## The IoT foundation

Every smart factory starts with two concepts:

- **Machine** — what equipment is on the factory floor?
- **Sensor** — what data is it generating?

Machines and sensors form the telemetry backbone. Before tracking production or quality, you need to know what's running and what it's reporting.

## Defining the entities

### Machine

| Property | Type | Identifier? |
|---|---|---|
| `machineId` | string | ✓ |
| `name` | string | |
| `type` | string | |
| `status` | string | |
| `installDate` | date | |

The `status` property tracks operational state — `running`, `idle`, `maintenance`, or `offline`. This enables real-time dashboards and maintenance scheduling.

### Sensor

| Property | Type | Identifier? |
|---|---|---|
| `sensorId` | string | ✓ |
| `type` | string | |
| `unit` | string | |
| `lastReading` | float | |
| `threshold` | float | |

The `threshold` property defines the alert boundary. When `lastReading` exceeds `threshold`, the system triggers an alarm. This pattern is fundamental to predictive maintenance.

## Relationships

- **monitors** — `Sensor` → `Machine` (many-to-one)
  Multiple sensors monitor the same machine — one for temperature, another for vibration, etc.

> **Ownership hierarchy:** In IoT ontologies, sensors belong to machines. The direction matters: sensors monitor machines, not the other way around. This parent-child hierarchy is how IoT platforms organize telemetry data.

## The graph so far

<ontology-embed id="official/manufacturing-step-1" height="300px"></ontology-embed>

*A simple but meaningful start: machines monitored by sensors.*

## What we learned

- **IoT hierarchies** use parent-child relationships (Sensor → Machine)
- **Status properties** enable real-time operational tracking
- **Threshold properties** power predictive maintenance alerts
- Even two entities can form a useful telemetry backbone

```quiz
Q: Why does the Sensor entity have both lastReading and threshold properties?
- To store backup values in case one is wrong
- The threshold defines the alert boundary — when lastReading exceeds it, the system triggers an alarm for predictive maintenance [correct]
- Both values are required by all IoT standards
- The threshold is used to calculate the sensor's accuracy
> The threshold pattern is fundamental to predictive maintenance. By comparing the current reading against a known safe boundary, the system can automatically detect anomalies and alert operators before equipment failure occurs.
```

Next, we'll add production tracking with Work Orders and Parts.

---

# Production Tracking

Add Work-Order and Part to track what's being produced — connecting machines to their manufacturing output.

## From monitoring to producing

Sensors tell us *how* machines are performing, but we also need to know *what* they're producing. **Work-Order** and **Part** entities add production tracking to the factory model.

Adding production tracking enables:
- "Which machine is producing the most parts this shift?"
- "How many work orders are behind schedule?"
- "What parts are currently being manufactured on CNC-01?"

## Work-Order entity

| Property | Type | Identifier? |
|---|---|---|
| `workOrderId` | string | ✓ |
| `priority` | string | |
| `status` | string | |
| `startDate` | date | |
| `dueDate` | date | |

Work orders have both `startDate` and `dueDate` — enabling schedule adherence calculations. Combined with `priority`, this powers production planning queries.

## Part entity

| Property | Type | Identifier? |
|---|---|---|
| `partId` | string | ✓ |
| `name` | string | |
| `material` | string | |
| `weight` | float | |
| `tolerance` | float | |

The `tolerance` property defines acceptable manufacturing deviation. Parts with tighter tolerances need higher-precision machines — a key production planning constraint.

## New relationships

- **assigned_to** — `Work-Order` → `Machine` (many-to-one)
  Work orders are assigned to specific machines for production.

- **produces** — `Work-Order` → `Part` (one-to-many)
  A work order produces one or more parts.

- **has_part** — `Machine` → `Part` (one-to-many)
  A machine produces parts (the output perspective).

> **Production chain:** The chain `Machine ← Work-Order → Part` connects equipment to output through a scheduling entity. This is similar to how Appointment connects Patient and Provider in healthcare — the middle entity represents the event.

## The growing graph

<ontology-embed id="official/manufacturing-step-2" diff="official/manufacturing-step-1" height="400px"></ontology-embed>

*Work-Order and Part join the graph, adding production tracking to the IoT foundation. The diff shows what's new.*

## What we learned

- **Production chains** connect equipment to output through scheduling entities (Work-Order)
- **Dual date properties** (startDate/dueDate) enable schedule adherence tracking
- **Tolerance properties** encode manufacturing precision requirements
- The factory model now covers both monitoring (sensors) and production (work orders)

```quiz
Q: What does the tolerance property represent on the Part entity?
- The maximum number of parts that can be defective
- The acceptable manufacturing deviation — parts outside tolerance need higher-precision machines [correct]
- The time allowed to manufacture the part
- The temperature range the part can withstand
> Tolerance defines how much a part's actual dimensions can deviate from specifications. Tighter tolerances require higher-precision machines and more careful quality control — making this a key constraint in production planning.
```

Next, we'll add Quality-Check to close the production loop.

---

# Complete Factory Model

Add Quality-Check to complete the manufacturing ontology — closing the loop from production to inspection.

## Closing the quality loop

Manufacturing doesn't end when a part is produced — it must be inspected. **Quality-Check** closes the production cycle by verifying that parts meet specifications.

## Quality-Check entity

| Property | Type | Identifier? |
|---|---|---|
| `checkId` | string | ✓ |
| `inspector` | string | |
| `checkDate` | date | |
| `passed` | boolean | |
| `defectCode` | string | |

The `passed` boolean is the critical property — it determines whether a part ships or gets reworked. The `defectCode` property categorizes failures for root cause analysis.

## New relationship

- **inspects** — `Quality-Check` → `Part` (many-to-one)
  Each quality check inspects a specific part. A part may undergo multiple inspections (initial check, re-check after rework).

> **Feedback loop:** When a quality check fails, the production chain reverses: `Quality-Check (passed=false) → Part → Work-Order → Machine`. This feedback loop is how smart factories identify problematic machines and improve production quality over time.

## The complete graph

<ontology-embed id="official/manufacturing-step-3" diff="official/manufacturing-step-2" height="500px"></ontology-embed>

*The complete Smart Manufacturing ontology: 5 entities, 5 relationships. Quality-Check closes the feedback loop from inspection back to production.*

## What the complete model enables

| Question | Graph path |
|---|---|
| Which machines produce parts that fail inspection? | Machine → Part ← Quality-Check (passed=false) |
| Which sensors were abnormal when defective parts were produced? | Sensor → Machine → Part ← Quality-Check (passed=false) |
| What is the defect rate by work order priority? | Work-Order (priority) → Part ← Quality-Check |
| Which parts need re-inspection? | Part ← Quality-Check (passed=false, count > 1) |

## GQL query example

Correlate sensor anomalies with quality failures:

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

## What we built

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | Machine, Sensor | 2 | IoT hierarchy, telemetry |
| 2 | Work-Order, Part | 4 | Production chains, tolerances |
| 3 | Quality-Check | 5 | Feedback loops, inspection |

## Key takeaways

1. **IoT hierarchies** organize sensors under machines for telemetry aggregation
2. **Production chains** connect equipment to output through scheduling entities
3. **Quality feedback loops** enable root cause analysis across the production chain
4. **Threshold-based alerts** power predictive maintenance
5. **Boolean properties** (passed) create clear decision points in the workflow

```quiz
Q: How does Quality-Check create a feedback loop in the manufacturing ontology?
- It connects directly to Machine
- A failed check traces back through Part → Work-Order → Machine, identifying the source of defects [correct]
- It loops back to the Sensor entity
- Quality checks don't create feedback loops
> When a quality check fails, the path Quality-Check → Part → Work-Order → Machine traces the defect back to its source. This feedback loop is fundamental to continuous improvement in smart manufacturing — identifying which machines, work orders, or conditions produce defective parts.
```

You've completed the Smart Manufacturing learning path! Load any step from the [catalogue](#/catalogue) to explore it interactively.
