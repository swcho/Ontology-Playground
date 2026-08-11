# HR System

Model an HR platform with employees, departments, positions, assignments, and performance reviews.

Source: content/learn/hr-system-path (4 articles merged)

---

# Scenario Overview

Meet the HR System scenario and the cross-functional questions your ontology must answer.

## The scenario

You are designing a **human resources ontology** for a growing organization. The business needs a shared model for:

- **Employees** and their lifecycle status
- **Departments** and budget ownership
- **Positions** and role hierarchy
- **Assignments** that place employees into departments and positions over time
- **Performance reviews** used for development and compensation discussions

Data currently lives across payroll tools, HRIS, spreadsheets, and manager notes.

## Why an ontology?

A question like **"Which departments have the highest number of senior employees rated outstanding in the last review cycle?"** crosses employee records, org structure, role definitions, and review outcomes.

With an ontology, this becomes a connected graph query instead of manual joins across disconnected systems.

## What we'll build

| Step | Entities in focus | What you'll learn |
|---|---|---|
| 1 | Employee, Department, Position | Organizational foundation and identifiers |
| 2 | + Assignment | Junction entity pattern for staffing history |
| 3 | + PerformanceReview | Review cycles, ratings, and people analytics |
| 4 | Complete model | End-to-end HR questions and graph reasoning |

By the end, you'll understand how to model a practical HR domain with clear governance-ready structure.

## Key concepts

- **Stable identifiers** for every entity
- **Junction entities** for many-to-many staffing scenarios
- **Temporal properties** (startDate, reviewDate) for time-aware analysis
- **Enum values** for controlled statuses and ratings

Let's start with the organization core.

---

# Organization Core

Define Employee, Department, and Position to model core organizational structure.

## Building the organizational backbone

Every HR ontology starts with three core entities:

- **Employee** — the person in your workforce
- **Department** — the business unit where work is organized
- **Position** — the role definition that describes responsibility and level

These three entities provide the minimum structure for hiring, reporting, and workforce planning.

## Entity design

### Employee

| Property | Type | Identifier? |
|---|---|---|
| `employeeId` | string | ✓ |
| `name` | string | |
| `hireDate` | date | |
| `employmentStatus` | enum | |
| `jobLevel` | enum | |

`employeeId` is a stable business identifier. Avoid using mutable attributes like email as the primary key.

### Department

| Property | Type | Identifier? |
|---|---|---|
| `departmentId` | string | ✓ |
| `name` | string | |
| `budget` | decimal | |
| `status` | enum | |

Department budgets allow resource planning and cost center analysis from the same graph.

### Position

| Property | Type | Identifier? |
|---|---|---|
| `positionId` | string | ✓ |
| `title` | string | |
| `level` | enum | |
| `salaryBand` | string | |

Position separates role definition from the person currently assigned to it.

## Why this separation matters

If you collapse these concepts into one "EmployeeProfile" entity, you lose flexibility for:

- historical staffing changes
- role transitions
- open positions that exist before a hire

Separate entities keep the model clean and extensible.

```quiz
Q: Why model Position as its own entity instead of storing role fields directly on Employee only?
- Because ontology tools require at least three entities
- Because Position is a reusable role definition that can exist independently of a specific employee [correct]
- To reduce the number of relationships
- To avoid using identifier properties
> Position represents the role itself (title, level, salary band), while Employee represents a person. Separating them supports open roles, transitions, and cleaner staffing analytics.
```

Next, we add Assignment to capture who filled which role, where, and when.

---

# Assignments

Add Assignment as a junction entity to model staffing history across employees, departments, and positions.

## The staffing history problem

An employee can move between departments or positions over time. A department can host many employees. A position can be filled by different people over time.

This is not a simple one-to-one structure.

## Assignment as a junction entity

Create **Assignment** to connect:

- `Employee` -> `Assignment` (one-to-many)
- `Assignment` -> `Department` (many-to-one)
- `Assignment` -> `Position` (many-to-one)

Assignment holds the context of the relationship.

### Assignment properties

| Property | Type | Identifier? |
|---|---|---|
| `assignmentId` | string | ✓ |
| `startDate` | date | |
| `endDate` | date | |
| `isPrimary` | boolean | |

With `startDate` and `endDate`, you can answer historical questions like:

- "Who was in Finance during Q2?"
- "Which employees changed departments this year?"

## Design pattern in action

This is the same general pattern used in many domains:

- Student-Course via Enrollment
- Customer-Product via Order line items
- Employee-Department-Position via Assignment

Use junction entities when relationships need their own attributes.

```quiz
Q: What is the main reason Assignment should be its own entity?
- It improves icon choices in the graph
- It carries relationship-specific attributes like startDate and endDate [correct]
- It removes the need for identifiers
- It prevents many-to-one relationships
> Assignment stores the context of staffing over time. Those properties belong to the relationship, not to Employee, Department, or Position alone.
```

Next, we add performance reviews to complete the HR analytics model.

---

# Complete HR Model

Add PerformanceReview and apply the full HR ontology to real workforce analytics questions.

## Completing the people analytics layer

The final entity is **PerformanceReview**. It connects evaluation outcomes to employees over review cycles.

Relationship:

- `Employee` -> `PerformanceReview` (one-to-many)

### PerformanceReview properties

| Property | Type | Identifier? |
|---|---|---|
| `reviewId` | string | ✓ |
| `reviewPeriod` | string | |
| `rating` | enum | |
| `reviewDate` | date | |

Now the ontology supports operational and strategic HR questions in one graph.

## Complete graph

*HR System ontology with 5 entities: Employee, Department, Position, Assignment, PerformanceReview.*

## Example graph questions

| Question | Graph path |
|---|---|
| Which departments have the most senior employees? | Department <- Assignment <- Employee (`jobLevel=senior`) |
| Which employees changed roles in the last year? | Employee -> Assignment (multiple records by date) -> Position |
| Which teams have many outstanding reviews? | Department <- Assignment <- Employee -> PerformanceReview (`rating=outstanding`) |
| Which assignments are no longer active? | Assignment (`endDate` set or `isPrimary=false`) |

## Key takeaways

1. Separate **person**, **org unit**, and **role** into distinct entities.
2. Use **Assignment** as a junction entity for time-aware staffing history.
3. Use **PerformanceReview** to attach measurable outcomes to workforce entities.
4. Keep identifiers stable and statuses controlled via enum values.

```quiz
Q: Which entity enables historical analysis of role and department changes over time?
- Employee
- Department
- Assignment [correct]
- PerformanceReview
> Assignment records start and end dates for a specific employee-department-position link. Without it, you cannot track staffing history cleanly.
```

You have completed the HR System path. Open the model in the [catalogue](#/catalogue/community/ravi-chandu/hr-system) or continue iterating in [designer](#/designer/community/ravi-chandu/hr-system).
