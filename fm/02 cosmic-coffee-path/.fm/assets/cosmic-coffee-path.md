# Fourth Coffee

Build a coffee shop chain ontology from scratch — customers, orders, products, stores, suppliers, and shipments.

Source: content/learn/cosmic-coffee-path (4 articles merged)

---

# Scenario Overview

Meet Fourth Coffee — a modern coffee chain that needs an ontology to unify data across stores, suppliers, and orders.

## The scenario

You are designing the data model for **Fourth Coffee**, a specialty coffee chain with stores across multiple cities. The company tracks:

- **Customers** who visit stores and place orders
- **Orders** containing coffee products and food items
- **Products** sourced from suppliers around the world
- **Stores** in different cities with varying capacities
- **Suppliers** providing beans and goods
- **Shipments** moving products from suppliers to stores

Data lives in multiple systems — a lakehouse for customer profiles, a real-time Eventhouse for order transactions, and a Power BI semantic model for product analytics.

## Why an ontology?

Without an ontology, answering a question like **"Which suppliers provide organic beans to our highest-capacity stores?"** requires knowing which tables are in which system, how they join, and what the column names mean.

With an ontology, the question maps directly to a graph traversal:

`Store → Shipment → Supplier` filtered by `Product.isOrganic = true` and `Store.capacity`.

## What we'll build

Over three steps, we'll progressively construct the complete Fourth Coffee ontology:

| Step | Entities | What you'll learn |
|---|---|---|
| 1 | Customer, Order, Product | Core entity types, identifiers, cardinality |
| 2 | + Store | Location modelling, many-to-one relationships |
| 3 | + Supplier, Shipment | Supply chain connections, hub entities |

By the end, you'll have a 6-entity, 7-relationship ontology that can power graph queries, GQL, and natural-language Data Agent interactions.

## Key concepts

- **Entity types** — the nouns of your domain (Customer, Order, Product…)
- **Properties** — attributes that describe each entity (name, price, status…)
- **Identifier properties** — unique keys for each entity instance
- **Relationships** — directed connections with cardinality (one-to-many, many-to-many)
- **Hub entities** — entities like Shipment that connect multiple domains

Let's start with the three most fundamental entities in any commerce system.

---

# Core Orders

Define Customer, Order, and Product — the foundational entities of the coffee business — and connect them with relationships.

## The foundation

Every commerce system starts with three core concepts:

- **Customer** — who is buying?
- **Order** — what transaction happened?
- **Product** — what was purchased?

These three entity types form the heart of the Fourth Coffee ontology. Everything we add later connects back to them.

## Defining the entities

### Customer

| Property | Type | Identifier? |
|---|---|---|
| `customerId` | string | ✓ |
| `name` | string | |
| `email` | string | |
| `loyaltyTier` | enum (Bronze, Silver, Gold, Platinum) | |
| `joinDate` | date | |
| `totalSpend` | decimal (USD) | |

The `customerId` uniquely identifies each customer. The `loyaltyTier` uses an enum to restrict values to valid tiers — this prevents data quality issues in downstream analytics.

### Order

| Property | Type | Identifier? |
|---|---|---|
| `orderId` | string | ✓ |
| `timestamp` | datetime | |
| `total` | decimal (USD) | |
| `status` | enum (Pending, Preparing, Ready, Completed, Cancelled) | |
| `paymentMethod` | enum (Card, Cash, Mobile, Gift Card) | |

### Product

| Property | Type | Identifier? |
|---|---|---|
| `productId` | string | ✓ |
| `name` | string | |
| `category` | enum (Espresso, Brewed, Cold Brew, Tea, Food, Merchandise) | |
| `price` | decimal (USD) | |
| `origin` | string | |
| `isOrganic` | boolean | |

The `isOrganic` flag is a boolean — useful for filtering and compliance queries later.

## Connecting with relationships

Entities alone are just isolated tables. **Relationships** turn them into a graph:

- **places** — `Customer` → `Order` (one-to-many)
  Each customer can place many orders, but each order belongs to one customer.

- **contains** — `Order` → `Product` (many-to-many)
  An order can contain multiple products, and a product can appear in many orders.

## The graph so far

Three entities, two relationships. This is the foundation everything else builds on.

## What we learned

- Every entity needs an **identifier property** — a unique key
- **Enum properties** constrain values to valid options
- **Boolean properties** enable simple filtering
- **Cardinality** (one-to-many vs many-to-many) determines how entities relate

### Quiz

Q: Why is the "contains" relationship between Order and Product set to many-to-many instead of one-to-many?

Answer: An order can contain multiple products AND a product can appear in multiple orders. An order typically includes several products (a latte, a muffin, a bag of beans), and each product appears across many different orders — this bidirectional multiplicity requires many-to-many.

Next, we'll add Store to track where orders are processed.

---

# Adding Stores

Introduce Store locations into the ontology and connect orders to their processing stores.

## Where orders happen

So far, we know *who* orders *what* — but not *where*. Fourth Coffee operates stores across multiple cities, and each order is processed at a specific store.

Adding the **Store** entity lets us answer location-based questions like:
- "Which store has the most orders?"
- "What's the average order value per city?"
- "Which stores need more staff based on order volume?"

## Store entity

| Property | Type | Identifier? |
|---|---|---|
| `storeId` | string | ✓ |
| `name` | string | |
| `city` | string | |
| `state` | string | |
| `openDate` | date | |
| `capacity` | integer | |

The `capacity` property (seating capacity) is an **integer** — useful for operations planning. The `city` and `state` properties provide geographic context without the complexity of a full address hierarchy.

## New relationship

- **processedAt** — `Order` → `Store` (many-to-one)
  Each order is processed at exactly one store, but a store processes many orders.

> **Design note:** This is a many-to-one relationship. Many orders map to one store. This is the most common cardinality pattern for "belongs to" or "happens at" relationships.

## The growing graph

Store joins the graph via the processedAt relationship. The diff view highlights what's new since Step 1.

## What we learned

- **Many-to-one relationships** model "belongs to" or "located at" patterns
- **Integer properties** work well for countable quantities (capacity, floors, seats)
- Adding one entity opens up an entire category of location-based queries
- The `diff` view shows exactly what changed — making it easy to track ontology evolution

### Quiz

Q: What cardinality should the "processedAt" relationship between Order and Store have?

Answer: Many-to-one — many orders are processed at one store. Each order is processed at exactly one store location, but a store processes many orders throughout the day. From Order's perspective, this is many-to-one.

Next, we'll complete the supply chain with Supplier and Shipment.

---

# Complete Supply Chain

Add Supplier and Shipment to complete the Fourth Coffee ontology — connecting sourcing, logistics, and retail.

## Completing the picture

Fourth Coffee doesn't just sell coffee — it sources beans from suppliers around the world, receives shipments at its stores, and tracks the entire supply chain. Adding **Supplier** and **Shipment** closes the loop.

## Supplier

| Property | Type | Identifier? |
|---|---|---|
| `supplierId` | string | ✓ |
| `name` | string | |
| `country` | string | |
| `certification` | enum (Fair Trade, Rainforest Alliance, Organic, Direct Trade, None) | |
| `rating` | decimal | |

The `certification` property is an enum that captures sustainability credentials. The `rating` is a decimal (1–5) for quality scoring.

## Shipment

| Property | Type | Identifier? |
|---|---|---|
| `shipmentId` | string | ✓ |
| `dispatchDate` | date | |
| `arrivalDate` | date | |
| `status` | enum (In Transit, Delivered, Delayed) | |
| `weight` | decimal (kg) | |

Shipment acts as a **hub entity** — it connects Supplier to Store through Product, bridging the sourcing and retail sides of the business.

## New relationships

Four new relationships complete the supply chain:

- **sourcedFrom** — `Product` → `Supplier` (many-to-one)
  Each product's beans come from one supplier.

- **sentBy** — `Shipment` → `Supplier` (many-to-one)
  Each shipment originates from one supplier.

- **deliveredTo** — `Shipment` → `Store` (many-to-one)
  Each shipment arrives at one store.

- **carries** — `Shipment` → `Product` (many-to-many)
  A shipment can carry multiple products, and a product can be in multiple shipments.

> **Hub entity pattern:** Shipment connects three different entities (Supplier, Store, Product). Hub entities are powerful because they bridge otherwise disconnected parts of the graph.

## The complete graph

The complete Fourth Coffee ontology: 6 entity types, 7 relationships. Shipment acts as a hub connecting Supplier, Store, and Product.

## What the complete model enables

| Question | Graph path |
|---|---|
| Which suppliers provide organic beans? | Product (isOrganic=true) → Supplier |
| Which stores received delayed shipments? | Shipment (status=Delayed) → Store |
| What's the rating of our top supplier? | Product → Supplier (sort by rating) |
| Which certified suppliers ship to our largest stores? | Supplier → Shipment → Store (sort by capacity) |

## GQL query example

Find suppliers with Fair Trade certification that ship to stores in California:

```gql
MATCH (sup:Supplier)<-[:sentBy]-(s:Shipment)-[:deliveredTo]->(st:Store)
WHERE sup.certification = 'Fair Trade' AND st.state = 'CA'
RETURN sup.name, st.name, s.status
```

## What we built

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | Customer, Order, Product | 3 | Entity types, identifiers, cardinality |
| 2 | Store | 4 | Location modelling, many-to-one |
| 3 | Supplier, Shipment | 6 | Supply chain, hub entities |

## Key takeaways

1. **Start small** — three entities are enough to create value
2. **Hub entities** like Shipment bridge different business domains
3. **Enum properties** enforce data quality at the model level
4. **The graph grows incrementally** — each step adds new query capabilities
5. **GQL queries** map directly to ontology structure — no impedance mismatch

### Quiz

Q: Why is Shipment considered a "hub entity" in this ontology?

Answer: It connects three different entities: Supplier, Store, and Product. Shipment is a hub because it has relationships to Supplier (sentBy), Store (deliveredTo), and Product (carries) — bridging the sourcing, logistics, and retail domains in a single entity.
