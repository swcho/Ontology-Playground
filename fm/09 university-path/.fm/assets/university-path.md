# University System

Model an academic institution — students, courses, enrollments, professors, and departments.

Source: content/learn/university-path (4 articles merged)

---

# Scenario Overview

## The scenario

You are designing the data model for a **university management system**. The institution tracks:

- **Students** with their enrollment status, GPA, and academic standing
- **Courses** with credit hours, levels, and prerequisites
- **Enrollments** recording which students take which courses and their grades
- **Professors** teaching courses with their rank, tenure status, and office hours
- **Departments** organizing academic programs and housing faculty

Data lives across student information systems (SIS), learning management systems (LMS), human resources, and academic planning databases.

## Why an ontology?

An academic question like **"Which departments have professors teaching courses where over 50% of enrolled students scored below a C?"** crosses departmental records, faculty assignments, course offerings, and student grades.

With an ontology, this maps to: `Department → Professor → Course → Enrollment (grade < C) ← Student`.

## What we'll build

| Step | Entities | What you'll learn |
|---|---|---|
| 1 | Student, Course, Enrollment | Academic records, many-to-many through junction entities |
| 2 | + Professor | Faculty assignments, teaching relationships |
| 3 | + Department | Organizational structure, hierarchy |

By the end, you'll have a 5-entity, 6-relationship ontology covering the complete academic administration model.

## Key concepts

- **Junction entities** — Enrollment resolves the Student–Course many-to-many relationship
- **Academic hierarchies** — Departments organize professors and courses
- **Grade tracking** — letter grades and GPA as ontology properties
- **Temporal data** — semesters, enrollment dates, academic years

Let's start with the academic core.

---

# Academic Core

## The academic record foundation

Academic records revolve around a core question: *which students take which courses, and how do they perform?* Three entities answer this:

- **Student** — who is learning?
- **Course** — what is being taught?
- **Enrollment** — the record connecting a student to a course with a grade

## Defining the entities

### Student

| Property | Type | Identifier? |
|---|---|---|
| `studentId` | string | ✓ |
| `name` | string | |
| `gpa` | float | |
| `enrollmentYear` | integer | |
| `major` | string | |

The `gpa` property is a float — Grade Point Average ranges from 0.0 to 4.0. This aggregate metric enables academic standing queries and honor roll calculations.

### Course

| Property | Type | Identifier? |
|---|---|---|
| `courseId` | string | ✓ |
| `title` | string | |
| `credits` | integer | |
| `level` | string | |
| `maxEnrollment` | integer | |

The `level` property (100, 200, 300, 400) indicates course difficulty and prerequisites. The `maxEnrollment` integer enables capacity planning.

### Enrollment

| Property | Type | Identifier? |
|---|---|---|
| `enrollmentId` | string | ✓ |
| `semester` | string | |
| `grade` | string | |
| `enrollDate` | date | |
| `status` | string | |

Enrollment is a **junction entity** — it exists specifically to connect Students and Courses with additional context (grade, semester, status).

## Relationships

- **enrolls_in** — `Student` → `Enrollment` (one-to-many)
  A student has multiple enrollments across semesters.

- **for_course** — `Enrollment` → `Course` (many-to-one)
  Each enrollment is for one specific course.

> **Junction entity pattern:** When two entities have a many-to-many relationship with attributes, you create a junction entity. A student takes many courses. A course has many students. Enrollment sits between them, carrying the grade, semester, and status. This is one of the most common patterns in ontology design.

## The graph so far

*Student and Course connected through Enrollment — the classic junction entity pattern.*

## What we learned

- **Junction entities** (Enrollment) resolve many-to-many relationships with attributes
- **Float properties** (GPA) enable aggregate calculations and thresholds
- **Integer properties** (credits, maxEnrollment) enable capacity and workload planning
- The academic core follows Student → Enrollment → Course

```quiz
Q: Why is Enrollment modelled as a separate entity instead of a direct Student–Course relationship?
- To make the graph have more nodes
- Because Enrollment carries its own attributes (grade, semester, status) that don't belong to either Student or Course [correct]
- Ontologies require at least three entities
- Direct relationships between entities are not allowed
> A direct Student–Course relationship couldn't carry grade, semester, or status information. The junction entity pattern creates a first-class entity for the relationship itself, enabling queries like "What grade did this student get in this course this semester?" — which requires attributes on the connection, not on either endpoint.
```

Next, we'll add Professor to track faculty assignments.

---

# Faculty

## Adding faculty

Who teaches the courses? The **Professor** entity adds the teaching dimension — connecting faculty to courses and, transitively, to students.

Adding Professor enables:
- "Which professor teaches the most 400-level courses?"
- "What is the average GPA in Professor Smith's courses?"
- "Which tenured faculty teach introductory courses?"

## Professor entity

| Property | Type | Identifier? |
|---|---|---|
| `professorId` | string | ✓ |
| `name` | string | |
| `rank` | string | |
| `tenured` | boolean | |
| `officeHours` | string | |

The `rank` property (Assistant, Associate, Full) reflects academic hierarchy. The `tenured` boolean enables queries about job security and institutional investment.

## New relationships

- **teaches** — `Professor` → `Course` (one-to-many)
  A professor teaches one or more courses per semester.

- **advises** — `Professor` → `Student` (one-to-many)
  A professor advises students in their academic program.

> **Transitive queries:** With Professor → Course ← Enrollment ← Student, you can now ask questions that cross the teaching relationship: "Which students are taking courses from tenured professors?" This requires traversing Professor → Course → Enrollment → Student.

## The growing graph

*Professor joins with teaching and advising relationships. The diff highlights what's new.*

## What we learned

- **Boolean properties** (tenured) create yes/no categorizations for filtering
- **Transitive queries** traverse multiple relationships to connect distant entities
- **Academic rank** follows a defined hierarchy (Assistant → Associate → Full)
- The graph now supports both student-centric and faculty-centric queries

```quiz
Q: What does a transitive query across the university ontology look like?
- Querying a single entity's properties
- Traversing multiple relationships like Professor → Course → Enrollment → Student to connect distant entities [correct]
- Looking up a professor by their ID
- Counting the number of courses in the system
> Transitive queries are one of the greatest strengths of graph-based ontologies. By traversing Professor → Course → Enrollment → Student, you can answer questions like "Which students are in tenured professors' classes?" — connecting entities that have no direct relationship but are linked through intermediate nodes.
```

Next, we'll add Department to organize the academic structure.

---

# Complete University Model

## Organizational structure

Universities are organized into **Departments** — administrative units that house faculty, offer courses, and grant degrees. Adding Department creates the organizational hierarchy that ties everything together.

## Department entity

| Property | Type | Identifier? |
|---|---|---|
| `departmentId` | string | ✓ |
| `name` | string | |
| `building` | string | |
| `budget` | float | |
| `headOfDept` | string | |

The `budget` float enables resource allocation queries. The `headOfDept` property references a professor who leads the department — a self-referential pattern common in organizational hierarchies.

## New relationships

- **belongs_to** — `Professor` → `Department` (many-to-one)
  Professors are affiliated with a department.

- **offers** — `Department` → `Course` (one-to-many)
  Departments offer courses as part of their academic programs.

> **Organizational hierarchy:** Department sits at the top of the university ontology. It connects downward to both Professor (faculty) and Course (curriculum). This hub position makes Department ideal for aggregate queries: "department-level statistics."

## The complete graph

*The complete University ontology: 5 entities, 6 relationships. Department organizes both faculty and curriculum.*

## What the complete model enables

| Question | Graph path |
|---|---|
| Which departments have the highest average student GPA? | Department → Course ← Enrollment ← Student (avg GPA) |
| Which professors teach outside their department's courses? | Professor → Department vs Professor → Course → Department |
| What is the enrollment rate for each department? | Department → Course ← Enrollment (count) / Course.maxEnrollment |
| Which departments have the most tenured faculty? | Department ← Professor (tenured=true, count) |

## GQL query example

Find departments where students are struggling (average grade below B):

```gql
MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
WHERE e.grade IN ['C', 'D', 'F']
RETURN d.name, c.title, COUNT(e) AS struggling_count
ORDER BY struggling_count DESC
```

## What we built

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | Student, Course, Enrollment | 3 | Junction entities, many-to-many |
| 2 | Professor | 4 | Transitive queries, boolean properties |
| 3 | Department | 5 | Organizational hierarchy, hub entities |

## Key takeaways

1. **Junction entities** (Enrollment) resolve many-to-many relationships with attributes
2. **Transitive queries** unlock insights by traversing multi-hop paths
3. **Boolean properties** (tenured) enable categorical filtering
4. **Organizational hierarchies** (Department) provide aggregate grouping
5. **Hub entities** (Department) connect multiple branches of the ontology

```quiz
Q: Why is Department considered a "hub entity" in the university ontology?
- Because it has the most properties
- Because it connects to both Professor and Course, sitting at the top of the organizational hierarchy [correct]
- Because it was added last
- Because hub entities must have a budget property
> Department connects downward to both Professor (via belongs_to) and Course (via offers). This dual connection makes it the organizational hub — ideal for aggregate queries that combine faculty and curriculum data at the departmental level.
```

You've completed the University System learning path! Load any step from the [catalogue](#/catalogue) to explore it interactively.
