# E-Commerce Platform

Model an online marketplace — buyers, products, shopping carts, orders, and customer reviews.

Source: content/learn/ecommerce-path (4 articles merged)

---

# Scenario Overview

Meet the E-Commerce Platform — a marketplace that needs an ontology to connect buyers, products, carts, orders, and reviews.

## The scenario

You are building the data model for a **general-purpose e-commerce marketplace**. The platform handles:

- **Buyers** who browse and purchase products
- **Products** with inventory tracking
- **Shopping Carts** as active sessions before checkout
- **Orders** as completed purchase transactions
- **Reviews** where buyers rate and comment on products

Data flows through multiple systems — a transactional database for orders, a search engine for product discovery, and an analytics warehouse for buyer behavior.

## Why an ontology?

A question like **"Which verified reviewers rated products they didn't purchase?"** requires joining across buyers, reviews, orders, and products — touching multiple systems.

With an ontology, this becomes a graph pattern: find `Buyer` nodes that have a `writes → Review → reviews → Product` path but no `places → Order → includes → Product` path for the same product.

## What we'll build

| Step | Entities | What you'll learn |
|---|---|---|
| 1 | Buyer, Product, Order | Core marketplace entities and purchase flow |
| 2 | + Shopping-Cart | Pre-purchase sessions, one-to-one relationships |
| 3 | + Review | Customer feedback loop, closing the cycle |

By the end, you'll have a 5-entity, 6-relationship ontology covering the complete buyer journey from browsing to reviewing.

## Key concepts

- **Purchase flow** — the journey from browsing to buying
- **One-to-one relationships** — when each side has exactly one partner (Buyer ↔ Cart)
- **Feedback loops** — how reviews connect buyers back to products
- **Session entities** — temporary objects like shopping carts

Let's start with the core marketplace entities.

---

# Core Marketplace

Define Buyer, Product, and Order — the foundational entities that power any e-commerce platform.

## The purchase flow

Every marketplace revolves around three concepts:

- **Buyer** — who is purchasing?
- **Product** — what is being sold?
- **Order** — what was the completed transaction?

These three entities capture the essential purchase flow. Everything else we add enriches this foundation.

## Defining the entities

### Buyer

| Property | Type | Identifier? |
|---|---|---|
| `buyerId` | string | ✓ |
| `email` | string | |
| `memberSince` | date | |
| `loyaltyTier` | string | |
| `totalSpent` | decimal (USD) | |

Unlike a physical retail customer, an e-commerce buyer always has an `email` as a primary contact method. The `totalSpent` property enables lifetime-value segmentation.

### Product

| Property | Type | Identifier? |
|---|---|---|
| `sku` | string | ✓ |
| `name` | string | |
| `category` | string | |
| `price` | decimal (USD) | |
| `stockQty` | integer | |

The identifier here is `sku` (Stock Keeping Unit) — the standard product identifier in e-commerce. The `stockQty` property tracks real-time inventory.

### Order

| Property | Type | Identifier? |
|---|---|---|
| `orderId` | string | ✓ |
| `orderDate` | datetime | |
| `status` | string | |
| `total` | decimal (USD) | |
| `shippingMethod` | string | |

## Relationships

- **places** — `Buyer` → `Order` (one-to-many)
  A buyer can place many orders over time.

- **includes** — `Order` → `Product` (many-to-many)
  An order can include multiple products, and each product appears across many orders.

## The graph so far

<ontology-embed id="official/ecommerce-step-1" height="350px"></ontology-embed>

*Buyer, Product, and Order connected by the purchase flow relationships.*

## What we learned

- **SKU** is the standard identifier for e-commerce products
- The `stockQty` integer property enables inventory queries
- The basic purchase flow (Buyer → Order → Product) is the backbone of any marketplace

```quiz
Q: Why is "sku" used as the identifier for Product instead of "productId"?
- SKU is shorter to type
- SKU (Stock Keeping Unit) is the standard product identifier in e-commerce and retail systems [correct]
- productId would cause naming conflicts
- SKU is always a numeric value
> SKU stands for Stock Keeping Unit — it's the industry-standard identifier used across inventory management, warehousing, and e-commerce systems to uniquely identify each item.
```

Next, we'll add Shopping Cart to model the pre-purchase experience.

---

# Shopping Carts

Add Shopping-Cart to model active shopping sessions and introduce the one-to-one relationship pattern.

## Before the purchase

Not every browsing session leads to a purchase. The **Shopping Cart** captures what a buyer is considering before checking out. It's a session entity — temporary and mutable.

Adding the cart lets us answer questions like:
- "How many carts were abandoned this week?"
- "What's the average cart value vs. average order value?"
- "Which products are most often added to carts but not purchased?"

## Shopping-Cart entity

| Property | Type | Identifier? |
|---|---|---|
| `cartId` | string | ✓ |
| `createdAt` | datetime | |
| `itemCount` | integer | |
| `subtotal` | decimal (USD) | |

The `itemCount` and `subtotal` are denormalized summary properties — they could be computed from cart contents, but storing them directly makes queries faster.

## New relationships

- **has_cart** — `Buyer` → `Shopping-Cart` (one-to-one)
  Each buyer has exactly one active cart, and each cart belongs to exactly one buyer.

- **contains** — `Shopping-Cart` → `Product` (many-to-many)
  A cart can contain multiple products, and a product can be in many carts.

> **One-to-one pattern:** The `has_cart` relationship is one-to-one because each buyer has a single active shopping session. This is different from orders (one-to-many) because a buyer accumulates orders over time but only has one cart at any moment.

## The growing graph

<ontology-embed id="official/ecommerce-step-2" diff="official/ecommerce-step-1" height="400px"></ontology-embed>

*Shopping-Cart connects Buyer to Product through two new relationships. The diff highlights what changed since Step 1.*

## What we learned

- **Session entities** model temporary or in-progress states (carts, drafts, sessions)
- **One-to-one relationships** enforce a strict pairing (one buyer ↔ one cart)
- **Denormalized properties** (itemCount, subtotal) trade storage for query speed
- Cart analysis enables **conversion funnel** insights (cart → order ratio)

```quiz
Q: Why is the has_cart relationship between Buyer and Shopping-Cart set to one-to-one instead of one-to-many?
- Because shopping carts don't need unique identifiers
- Because each buyer has exactly one active cart at any given time [correct]
- Because one-to-one is simpler to implement
- Because carts are deleted after purchase
> A buyer maintains a single active shopping session (cart) at a time. Unlike orders which accumulate over a buyer's lifetime, the cart is a current-state entity — one buyer, one active cart.
```

Next, we'll complete the platform with customer reviews.

---

# Complete Platform

Add Review to close the buyer feedback loop and complete the e-commerce ontology.

## Closing the feedback loop

The final piece of the e-commerce puzzle is **customer reviews**. Reviews connect buyers back to products, creating a feedback loop that influences future purchases.

## Review entity

| Property | Type | Identifier? |
|---|---|---|
| `reviewId` | string | ✓ |
| `rating` | integer | |
| `title` | string | |
| `body` | string | |
| `verified` | boolean | |

The `verified` boolean indicates whether the reviewer actually purchased the product — a critical trust signal for other buyers and for analytics.

## New relationships

- **writes** — `Buyer` → `Review` (one-to-many)
  A buyer can write many reviews over time.

- **reviews** — `Review` → `Product` (many-to-one)
  Each review is about exactly one product, but a product can have many reviews.

> **Feedback loop:** The path `Buyer → writes → Review → reviews → Product` creates a cycle back to Product — buyers consume products, then review them, influencing other buyers.

## The complete graph

<ontology-embed id="official/ecommerce-step-3" diff="official/ecommerce-step-2" height="500px"></ontology-embed>

*The complete E-Commerce ontology: 5 entities, 6 relationships. Review closes the buyer feedback loop.*

## What the complete model enables

| Question | Graph path |
|---|---|
| Which products have the highest-rated verified reviews? | Review (verified=true) → Product |
| Which buyers have full carts but no orders? | Buyer → Cart (itemCount > 0) with no Buyer → Order |
| What's the average rating for products in a category? | Review → Product (group by category) |
| Which loyal buyers write the most reviews? | Buyer (loyaltyTier=Gold) → Review (count) |

## GQL query example

Find verified reviews for products currently in someone's cart:

```gql
MATCH (b:Buyer)-[:has_cart]->(c:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE r.verified = true
RETURN p.name, r.rating, r.title
```

## What we built

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | Buyer, Product, Order | 3 | Purchase flow, SKU identifiers |
| 2 | Shopping-Cart | 4 | Session entities, one-to-one |
| 3 | Review | 5 | Feedback loops, verified trust |

## Key takeaways

1. **Session entities** (Cart) capture in-progress state
2. **One-to-one** relationships model exclusive ownership
3. **Boolean properties** (verified) enable trust-based filtering
4. **Feedback loops** create richer query paths than linear chains
5. The complete graph enables **funnel analysis** from browsing to reviewing

```quiz
Q: What makes the Review entity create a "feedback loop" in this ontology?
- It connects to every other entity in the graph
- It creates a path from Buyer back to Product through a different route than the purchase path [correct]
- It has the most properties of any entity
- It uses a boolean verified property
> Without Review, the path from Buyer to Product only goes through Order. Review creates a second path — Buyer → Review → Product — forming a loop. This dual-path structure enables comparative queries (e.g. "bought but didn't review" vs "reviewed but didn't buy").
```

You've completed the E-Commerce Platform learning path! Load any step from the [catalogue](#/catalogue) to explore it interactively.
