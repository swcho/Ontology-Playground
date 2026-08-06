# Ontology Fundamentals

From first principles to hands-on design — everything you need to understand and build ontologies for Microsoft Fabric IQ.

Source: content/learn/ontology-fundamentals (6 articles merged)

---

# What is an Ontology?

> A beginner-friendly introduction to ontologies — what they are, why they matter, and how they help us model the real world as connected data.

## Thinking in graphs

Imagine you're describing a coffee shop. You'd talk about **things** — stores, products, customers, orders — and the **connections** between them: a customer *places* an order, an order *contains* products, a store *stocks* products.

An **ontology** is a formal way of describing exactly that: the types of things in a domain and how they relate to each other. It's a blueprint for your data — not the data itself, but the *shape* of the data.

## Entities, properties, and relationships

Every ontology is built from three building blocks:

| Concept | What it means | Example |
|---------|--------------|---------|
| **Entity type** | A category of thing | `Customer`, `Product`, `Store` |
| **Property** | A fact about an entity | `Customer.name`, `Product.price` |
| **Relationship** | A connection between entities | `Customer → places → Order` |

Properties have **types** — text, numbers, dates, booleans — and every entity needs at least one **identifier property** (like a customer ID) that uniquely distinguishes each instance.

## Why ontologies matter

Without an ontology, your data is just tables and columns. With one, a system can understand that "revenue" is the sum of `Order.totalAmount` grouped by `Store.city` — because the ontology tells it how those concepts connect.

This is the foundation of **semantic data models**: instead of writing SQL by hand, you describe what you want in plain language and the system uses the ontology to generate the right query.

<ontology-embed id="official/cosmic-coffee" height="400px"></ontology-embed>

*The Fourth Coffee ontology above models a coffee shop chain. Click any node to inspect its properties, or click an edge to see the relationship details.*

## From concept to code

Ontologies are typically represented in **RDF/OWL** — an XML-based standard for describing classes, properties, and relationships. You don't need to write XML by hand, though: tools like the [Ontology Designer](#/designer) let you build one visually and export valid RDF.

## Key takeaways

- An ontology defines the **types of things** in a domain and **how they relate**
- It's a schema, not data — it describes the shape, not the content
- It enables semantic querying: ask questions in natural language, get structured answers
- The standard format is **RDF/OWL**, but you can also work with JSON representations

```quiz
Q: Which of the following is NOT a building block of an ontology?
- Entity type
- Property
- SQL query [correct]
- Relationship
> Ontologies are built from entity types, properties, and relationships. SQL queries are how you retrieve data — they are not part of the ontology definition itself.
```

```quiz
Q: What is the purpose of an identifier property?
- To store the entity's colour
- To uniquely distinguish each instance of an entity [correct]
- To connect two entities together
- To define the data format
> An identifier property (like a customer ID) uniquely identifies each instance within an entity type, allowing the system to count, group, and join correctly.
```

Ready to see how RDF works under the hood? Continue to the next article.

---

# Understanding RDF and OWL

> Learn how ontologies are represented in RDF/OWL — the standard language for describing classes, properties, and relationships on the semantic web.

## What is RDF?

**RDF** (Resource Description Framework) is a W3C standard for describing information as a graph of connected resources. Everything in RDF is expressed as **triples**: subject → predicate → object.

```
:Customer  rdf:type       owl:Class .
:name      rdf:type       owl:DatatypeProperty .
:name      rdfs:domain    :Customer .
:name      rdfs:range     xsd:string .
```

The triple above says: "There is a class called Customer, and it has a property called name, which is a string."

## OWL builds on RDF

**OWL** (Web Ontology Language) extends RDF with richer modelling — cardinality constraints, class hierarchies, and logical axioms. For ontology design, the key OWL constructs are:

| OWL concept | Maps to | Example |
|-------------|---------|---------|
| `owl:Class` | Entity type | `Customer`, `Product` |
| `owl:DatatypeProperty` | Property with a primitive value | `name` (string), `price` (decimal) |
| `owl:ObjectProperty` | Relationship between entities | `placedBy` (Order → Customer) |
| `rdfs:domain` / `rdfs:range` | Which entity a property belongs to / its type | `price` belongs to `Product`, type `xsd:decimal` |

## Namespaces keep things unambiguous

Every resource in RDF has a globally unique **URI**. To avoid writing long URIs everywhere, RDF/XML uses **namespace prefixes**:

```xml
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns="https://mycompany.com/ontology/">
```

The `xmlns=` default namespace means that `<owl:Class rdf:about="Customer">` is really `https://mycompany.com/ontology/Customer`.

## Reading an RDF/OWL file

Here's a minimal ontology with one entity type and one property:

```xml
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
         xmlns="https://example.com/shop/">

  <!-- Entity type: Product -->
  <owl:Class rdf:about="Product">
    <rdfs:label>Product</rdfs:label>
  </owl:Class>

  <!-- Property: productName (string, identifier) -->
  <owl:DatatypeProperty rdf:about="productName">
    <rdfs:domain rdf:resource="Product"/>
    <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    <rdfs:label>productName</rdfs:label>
  </owl:DatatypeProperty>
</rdf:RDF>
```

The Ontology Playground can import files like this directly — or you can design visually and export to RDF.

<ontology-embed id="official/ecommerce" height="400px"></ontology-embed>

*The E-Commerce ontology shows a richer example with multiple entity types and object properties connecting them.*

## JSON vs RDF — when to use which

| | JSON | RDF/OWL |
|---|------|---------|
| **Human readability** | Easy to read and edit | Verbose but precise |
| **Tooling** | Any text editor | Semantic web tools, SPARQL endpoints |
| **Interoperability** | Application-specific | W3C standard, universally understood |
| **Best for** | Quick prototyping, app configs | Formal data models, cross-system integration |

The Ontology Playground supports both formats: design in the visual editor, export as JSON for quick use or RDF/OWL for formal publication.

## Key takeaways

- RDF represents knowledge as **subject → predicate → object** triples
- OWL adds classes, data properties, and object properties on top of RDF
- Namespaces keep URIs short and unambiguous
- The Playground imports and exports standard RDF/OWL — no hand-coding required

```quiz
Q: In RDF, information is expressed as:
- Tables with rows and columns
- JSON key-value pairs
- Subject → predicate → object triples [correct]
- Binary data streams
> RDF uses triples — three-part statements where a subject is connected to an object through a predicate — to describe information as a graph of connected resources.
```

```quiz
Q: What does owl:ObjectProperty represent?
- A property with a primitive value like a string
- A relationship between two entity types [correct]
- The namespace of an ontology
- A constraint on data types
> In OWL, an ObjectProperty defines a relationship between two classes (entity types), such as "placedBy" connecting Order to Customer. DatatypeProperty is used for primitive values.
```

---

# Microsoft Fabric IQ Ontology Concepts

> How Microsoft Fabric uses ontologies to power natural-language queries over structured data — entity types, identifier properties, relationships, and cardinality.

## What is Fabric IQ?

**Microsoft Fabric** is a unified analytics platform that brings together data engineering, data science, real-time analytics, and business intelligence. **IQ** is a Fabric capability that lets users ask questions in **natural language** and get answers from structured data — no SQL required.

The key ingredient is an **ontology**: a formal description of entity types, their properties, and relationships. IQ reads the ontology, understands the shape of your data, and translates plain-English questions into the correct queries.

## How IQ uses ontologies

When a user asks *"What were last month's total sales by region?"*, IQ needs to know:

1. **Entity types** — `Order`, `Store`, `Region`
2. **Properties** — `Order.totalAmount`, `Order.date`, `Store.region`
3. **Relationships** — `Order` → `placedAt` → `Store`, `Store` → `locatedIn` → `Region`
4. **Identifier properties** — which fields uniquely identify each entity (e.g. `Order.orderId`)

The ontology provides all four. Without it, IQ can't distinguish a "store" from a "product" or know how to join them.

## Entity types

An entity type is a category of business object. In Fabric IQ, each entity type:

- Has a **name** and optional **description**
- Contains one or more **properties** (typed columns)
- Must have at least one **identifier property** that uniquely identifies instances

Think of it as a table definition: `Customer(customerId, name, email, tier)`.

## Properties and types

Each property has a data type:

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | Customer name, product SKU |
| `integer` | Whole number | Quantity, year |
| `decimal` | Fractional number | Price, rating |
| `date` | Calendar date | Order date, birth date |
| `datetime` | Date with time | Created timestamp |
| `boolean` | True/false | Is active, is premium |

The **identifier property** (marked with a key icon) is critical: it tells IQ how to count, group, and join entities correctly.

## Relationships and cardinality

Relationships connect entity types. Each relationship specifies:

- **Source and target** entity types
- **Name** (the verb: "places", "contains", "worksAt")
- **Cardinality** — how many instances can connect

| Cardinality | Meaning | Example |
|------------|---------|---------|
| One-to-one | Each A maps to exactly one B | `Employee` → `Badge` |
| One-to-many | Each A maps to many Bs | `Customer` → `Order` |
| Many-to-one | Many As map to one B | `Order` → `Store` |
| Many-to-many | Many As map to many Bs | `Student` → `Course` |

IQ uses cardinality to generate correct aggregations. A one-to-many relationship between `Customer` and `Order` means "count of orders per customer" is valid, while "count of customers per order" would typically be 1.

<ontology-embed id="official/ecommerce" height="400px"></ontology-embed>

*The E-Commerce ontology demonstrates IQ-ready patterns: identifier properties on each entity, typed columns, and cardinality on every relationship.*

## Designing for IQ

When building an ontology for Fabric IQ, follow these guidelines:

1. **Name entities clearly** — use business terms your users would say ("Customer", not "tbl_cust")
2. **Add descriptions** — IQ uses them to disambiguate similar concepts
3. **Mark identifiers** — every entity MUST have at least one identifier property
4. **Set cardinality** — helps IQ generate correct GROUP BY and JOIN logic
5. **Keep it focused** — model the concepts users will query, not every internal table

## Key takeaways

- Fabric IQ translates natural-language questions into SQL using an ontology
- Entity types, properties, relationships, and cardinality are the four pillars
- Every entity needs an identifier property for correct counting and joining
- Good naming and descriptions improve IQ's question-answering accuracy
- Use the [Ontology Designer](#/designer) to create IQ-ready ontologies visually

```quiz
Q: Why is an identifier property required on every entity type in Fabric IQ?
- It makes the ontology look professional
- It tells IQ how to count, group, and join entities correctly [correct]
- It is used as the entity's display name
- It sets the default sort order
> The identifier property uniquely distinguishes instances of an entity type. Without it, IQ cannot correctly generate COUNT, GROUP BY, or JOIN operations in the translated SQL.
```

```quiz
Q: What does the cardinality of a relationship tell Fabric IQ?
- The colour to use when drawing the relationship
- How many instances can connect on each side of the relationship [correct]
- Whether the relationship is optional or required
- The order in which entities should be displayed
> Cardinality (one-to-one, one-to-many, many-to-one, many-to-many) tells IQ how to generate correct aggregations and joins — for example, knowing that one customer has many orders.
```

---

# Building Your First Ontology

> A step-by-step tutorial to create an ontology from scratch using the visual designer — add entities, define properties, connect with relationships, and export to RDF.

## What we'll build

In this tutorial, you'll create a simple **Library** ontology with three entity types: `Book`, `Author`, and `Member` — connected by relationships. By the end, you'll have a valid RDF file ready for use with Microsoft Fabric IQ or any semantic tool.

## Step 1: Open the designer

Click the **Designer** button in the top navigation bar, or go directly to [/#/designer](#/designer). You'll see a blank canvas: an entity form on the left, a live graph preview on the right.

## Step 2: Create entity types

Add three entities using the **+ Add Entity** button:

**Book**
- Name: `Book`
- Icon: `📚`
- Color: pick a blue
- Properties:
  - `isbn` — string, **identifier** ✓
  - `title` — string
  - `publishedYear` — integer

**Author**
- Name: `Author`
- Icon: `✍️`
- Color: pick a green
- Properties:
  - `authorId` — string, **identifier** ✓
  - `name` — string
  - `nationality` — string

**Member**
- Name: `Member`
- Icon: `👤`
- Color: pick a purple
- Properties:
  - `memberId` — string, **identifier** ✓
  - `name` — string
  - `joinDate` — date

As you add each entity, watch the graph preview update in real-time.

## Step 3: Add relationships

Switch to the **Relationships** tab and add:

| Relationship | From | To | Cardinality |
|-------------|------|-----|-------------|
| `writtenBy` | Book | Author | Many-to-one |
| `borrowedBy` | Book | Member | Many-to-many |

The `writtenBy` relationship is many-to-one because many books can share one author, but each book has one primary author. The `borrowedBy` relationship is many-to-many because a book can be borrowed by many members, and a member can borrow many books.

## Step 4: Validate

Click the **Validate** button in the toolbar. If everything is correct, you'll see a green "No issues found" banner. Otherwise, fix any reported issues:

- Every entity must have at least one identifier property
- Relationships must reference existing entity types
- No duplicate IDs

## Step 5: Preview the RDF

Click the **RDF** tab in the preview pane. You'll see the live RDF/OWL output with syntax highlighting. This is the exact file that tools like Fabric IQ consume.

<ontology-embed id="official/cosmic-coffee" height="400px"></ontology-embed>

*The Fourth Coffee ontology was built using the same workflow. Your Library ontology will look similar — entities as colourful nodes, relationships as directed edges.*

## Step 6: Export

You have three options:

1. **Download RDF** — saves a `.rdf` file to your Downloads folder
2. **Submit to Catalogue** — opens a one-click PR flow to contribute your ontology to the community catalogue (requires GitHub sign-in)
3. **Copy JSON** — copies the JSON representation for use in apps

## What's next?

- Explore the [Catalogue](#/catalogue) to see how other ontologies are structured
- Read [Ontology Design Patterns](#/learn/ontology-design-patterns) for naming conventions and best practices
- Try the **Query Playground** on the home page to ask natural-language questions against your ontology

## Key takeaways

- The designer provides a visual, code-free workflow for building ontologies
- Every entity needs a name, at least one property, and one identifier
- Relationships connect entities with a name and cardinality
- The live graph and RDF previews give instant feedback as you design
- Export to RDF for Fabric IQ, or submit directly to the community catalogue

```quiz
Q: Why is the borrowedBy relationship between Book and Member set to many-to-many?
- A book can only be borrowed once
- Each member borrows exactly one book at a time
- A book can be borrowed by many members over time, and a member can borrow many books [correct]
- Many-to-many is the default cardinality for all relationships
> A single book can be borrowed by different members at different times, and each member can borrow multiple books simultaneously — this bidirectional multiplicity is what makes it many-to-many.
```

---

# Ontology Design Patterns

> Practical naming conventions, modelling patterns, and common anti-patterns to avoid when designing ontologies for data platforms.

## Name things for humans

The most important design decision is naming. Your entity types and properties will be read by both humans and machines — clear names make natural-language queries more accurate.

**Do:**
- Use singular nouns for entity types: `Customer`, `Product`, `Order`
- Use camelCase for properties: `firstName`, `totalAmount`, `createdDate`
- Use verb phrases for relationships: `placedBy`, `worksAt`, `contains`

**Don't:**
- Use internal table names: `tbl_cust_v2`, `DIM_PRODUCT`
- Abbreviate: `qty`, `amt`, `dt` — spell them out
- Use generic names: `Item`, `Record`, `Thing`

## One entity, one concept

Each entity type should represent a **single business concept**. If you find yourself adding unrelated properties, you probably need to split the entity.

**Anti-pattern:** A `Person` entity with `salary`, `patientId`, `courseGrade`, and `accountBalance` — this is four different concepts (Employee, Patient, Student, Customer) forced into one.

**Better:** Create separate entity types and relate them if needed: a `Person` can be linked to an `Employee` record, a `Patient` record, etc.

## Choose identifiers carefully

The identifier property determines how instances are counted, grouped, and joined. A good identifier is:

- **Unique** across all instances
- **Stable** — doesn't change over time
- **Meaningful** — preferably a business key, not an internal auto-increment

Examples: `isbn` for books, `email` for users, `orderId` for orders.

Avoid using compound identifiers (multiple fields that together form the key) — most ontology tools expect a single identifier per entity.

## Model relationships, not foreign keys

In relational databases, you use foreign keys to link tables. In an ontology, you use **named relationships** with explicit semantics.

| Relational | Ontology |
|-----------|----------|
| `orders.customer_id → customers.id` | `Order` → `placedBy` → `Customer` |
| `order_items.product_id → products.id` | `OrderItem` → `contains` → `Product` |

The relationship **name** is critical: it tells query engines (and humans) what the connection means. "placedBy" is infinitely clearer than a column called `fk_cust_id`.

## Get cardinality right

Wrong cardinality leads to wrong aggregations. Ask yourself: "For one instance of A, how many instances of B can there be?"

- A customer can place **many** orders → one-to-many
- An order is placed at **one** store → many-to-one
- A student can take **many** courses, and a course has **many** students → many-to-many

<ontology-embed id="official/healthcare" height="400px"></ontology-embed>

*The Healthcare ontology is a good study in cardinality: a patient has many appointments, but each appointment has one provider. A diagnosis belongs to one patient but may be linked to many prescriptions.*

## Avoid these common mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| **God entity** | One entity with 30+ properties | Split into focused entities |
| **Missing identifiers** | Can't count or group instances | Add a unique identifier property |
| **Vague relationship names** | `relatedTo`, `hasLink` | Use specific verbs: `prescribes`, `enrolledIn` |
| **Circular one-to-ones** | A → B and B → A both 1:1 | Probably the same entity — merge them |
| **Over-modelling** | Every internal table becomes an entity | Model what users will query, not your schema |

## When to use descriptions

Every entity type, property, and relationship can have an optional **description**. Use them when:

- The name alone is ambiguous (`status` could mean many things)
- The concept is domain-specific (`formulary`, `SKU`, `yield`)
- You want to guide natural-language query interpretation

## Key takeaways

- Name for humans: singular nouns, camelCase, verb phrases
- One entity, one concept — split over-loaded entities
- Choose stable, unique, meaningful identifiers
- Model relationships with names, not foreign key columns
- Set cardinality correctly to enable proper aggregations
- Add descriptions where names are ambiguous

```quiz
Q: A Person entity has properties salary, patientId, courseGrade, and accountBalance. What design pattern should you apply?
- Add an identifier property
- Merge all properties into a description field
- Split into separate entity types (Employee, Patient, Student, Customer) and relate them [correct]
- Remove all but one property to keep it simple
> When an entity accumulates unrelated properties, it becomes a "god entity". The fix is to separate each concept into its own entity type and link them with relationships where needed.
```

---

# Contributing to the Catalogue

> How to share your ontology with the community — fork, add your RDF and metadata, submit a PR, and see it published in the catalogue.

## The community catalogue

The Ontology Playground includes a [catalogue](#/catalogue) of ontologies — some maintained by the project team ("official") and others contributed by the community. Anyone can submit an ontology by opening a pull request.

## Two ways to contribute

### Option A: One-click PR from the designer

The fastest way to contribute:

1. Open the [Designer](#/designer) and build your ontology (or load an existing one)
2. Click **Submit to Catalogue** in the toolbar
3. Fill in the metadata: name, description, category, and tags
4. Sign in with GitHub (device flow — no passwords stored)
5. The tool automatically forks the repo, creates a branch, commits your RDF and metadata, and opens a pull request

That's it. The CI pipeline validates your RDF, checks the metadata schema, and runs tests. A maintainer reviews and merges.

### Option B: Manual PR

If you prefer working with Git directly:

1. **Fork** the repository on GitHub
2. Create a directory under `catalogue/community/<your-github-username>/<ontology-slug>/`
3. Add two files:
   - `ontology.rdf` — your RDF/OWL file
   - `metadata.json` — describes your ontology

## The metadata format

```json
{
  "name": "Library System",
  "description": "A public library with books, authors, members, and loans.",
  "icon": "📚",
  "category": "education",
  "tags": ["library", "books", "lending"],
  "author": "your-github-username"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name for the catalogue |
| `description` | Yes | One-sentence summary |
| `category` | Yes | One of: `retail`, `healthcare`, `finance`, `manufacturing`, `education`, `technology`, `general` |
| `icon` | No | Single emoji for the card |
| `tags` | No | Array of lowercase keywords for search |
| `author` | No | GitHub username (auto-filled by the one-click flow) |

## Validation rules

Your PR will be automatically validated against these rules:

- **Valid RDF/OWL** — must parse without errors
- **Round-trip fidelity** — `parse(serialize(ontology))` must produce equivalent output
- **Metadata schema** — all required fields present, category is valid
- **Directory naming** — lowercase alphanumeric, hyphens, and underscores only
- **No symlinks** — for security, symbolic links in the catalogue are rejected

## What happens after merge?

Once merged, the build pipeline:

1. Runs `npm run catalogue:build` — compiles all RDF files into `catalogue.json`
2. Deploys the updated site — your ontology appears in the [Gallery](#/catalogue)
3. It's immediately available for embedding, deep-linking, and loading in the playground

<ontology-embed id="official/university" height="400px"></ontology-embed>

*The University System ontology is one of the official catalogue entries. Community contributions follow the same format — your ontology will look just like this in the gallery.*

## Tips for a smooth review

- **Write a good description** — explain what domain your ontology models and who it's for
- **Add meaningful tags** — helps users find your ontology in search
- **Test locally** — run `npm run validate -- catalogue/community/<you>/<slug>/ontology.rdf` before pushing
- **Keep it focused** — a well-scoped ontology with 3-8 entity types is more useful than a sprawling one with 30+

## Key takeaways

- Anyone can contribute an ontology via the one-click PR flow or a manual pull request
- Each submission needs an RDF file and a `metadata.json`
- CI validates your RDF automatically — fix any errors before the review
- Merged ontologies appear in the live catalogue immediately after deployment

```quiz
Q: What two files must every catalogue contribution include?
- ontology.json and README.md
- schema.rdf and config.yaml
- ontology.rdf and metadata.json [correct]
- index.html and style.css
> Each catalogue entry requires an ontology.rdf file (the RDF/OWL ontology) and a metadata.json file (name, description, category, and tags for the catalogue listing).
```
