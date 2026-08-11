# Banking & Finance

Model a financial services domain — customers, accounts, transactions, loans, and investment portfolios.

Source: content/learn/finance-path (4 articles merged)

---

# Scenario Overview

Meet the Banking & Finance scenario — why financial services need ontologies for customer, account, and product relationships.

## The scenario

You are designing the data model for a **retail banking platform**. The bank manages:

- **Customers** with credit profiles and risk assessments
- **Accounts** (checking, savings, brokerage) with balances and interest rates
- **Transactions** recording every debit, credit, and transfer
- **Loans** including mortgages, auto loans, and personal credit
- **Investments** tracking stock holdings and portfolio values

Data spans core banking systems, payment processors, credit bureaus, and brokerage platforms — each with its own schema and identifiers.

## Why an ontology?

A compliance question like **"Show all transactions from accounts owned by high-risk customers with active loans exceeding $100K"** requires traversing from transactions to accounts to customers to loans, crossing multiple systems.

With an ontology, this is a graph traversal: `Transaction → Account → Customer (riskProfile='high') → Loan (principal > 100000)`.

## What we'll build

| Step | Entities | What you'll learn |
|---|---|---|
| 1 | Customer, Account | Core banking entities, ownership relationships |
| 2 | + Transaction | Activity tracking, temporal data |
| 3 | + Loan, Investment | Financial products, multi-path relationships |

By the end, you'll have a 5-entity, 6-relationship ontology covering the complete banking customer relationship.

## Key concepts

- **Ownership chains** — Customer → Account → Transaction / Loan / Investment
- **Financial identifiers** — account numbers, transaction IDs, loan IDs
- **Risk and compliance** — credit scores, risk profiles
- **Multi-path relationships** — when one entity connects to another through different paths

Let's start with the banking foundation: Customer and Account.

---

# Customer & Accounts

Define Customer and Account — the banking foundation — with ownership relationships and financial properties.

## The banking foundation

Every financial institution starts with two core concepts:

- **Customer** — who holds the accounts?
- **Account** — where is money stored and managed?

This pair forms the foundation of any banking ontology. Every other financial product connects through them.

## Defining the entities

### Customer

| Property | Type | Identifier? |
|---|---|---|
| `customerId` | string | ✓ |
| `name` | string | |
| `ssn` | string | |
| `creditScore` | integer | |
| `riskProfile` | string | |

The `creditScore` is an integer (300–850) used for lending decisions. The `riskProfile` property captures the bank's assessment for compliance and monitoring.

> **Sensitive data note:** Properties like `ssn` appear in the ontology as metadata — they describe what data *exists*, not the actual values. The ontology is a schema, not a database.

### Account

| Property | Type | Identifier? |
|---|---|---|
| `accountNumber` | string | ✓ |
| `type` | string | |
| `balance` | decimal (USD) | |
| `interestRate` | decimal (%) | |
| `openDate` | date | |

The `type` property distinguishes between checking, savings, and brokerage accounts. The `interestRate` uses a percentage unit.

## Ownership relationship

- **owns** — `Customer` → `Account` (one-to-many)
  A customer can own multiple accounts (checking, savings, brokerage), but each account belongs to one customer.

## The graph so far

<ontology-embed id="official/finance-step-1" height="300px"></ontology-embed>

*Customer and Account connected by the ownership relationship. Simple but foundational.*

## What we learned

- **Integer properties** work well for scores and ratings (creditScore)
- **Percentage units** (%) indicate rate-based properties
- The **owns** relationship creates the fundamental ownership chain
- Ontologies describe the *shape* of data, not the data itself — sensitive fields like SSN are metadata

```quiz
Q: Why is creditScore modeled as an integer rather than a string?
- Strings are harder to store in databases
- Integer type enables numeric comparisons and range queries (e.g., creditScore > 700) [correct]
- Credit scores are always exactly three digits
- Integers take less storage space
> By using an integer type, the ontology signals that creditScore supports numeric operations — comparisons, ranges, averages, and thresholds. A string property wouldn't convey this capability to query engines.
```

Next, we'll add Transaction to track account activity.

---

# Transactions

Add Transaction records to track every debit, credit, and transfer on an account.

## Tracking activity

An account without transaction history is just a static balance. Adding **Transaction** captures the flow of money — every purchase, deposit, transfer, and fee.

This enables questions like:
- "What did this customer spend at restaurants last month?"
- "Which accounts have unusual transaction patterns?"
- "What's the average transaction amount per account type?"

## Transaction entity

| Property | Type | Identifier? |
|---|---|---|
| `transactionId` | string | ✓ |
| `amount` | decimal (USD) | |
| `type` | string | |
| `timestamp` | datetime | |
| `merchant` | string | |

The `timestamp` is a datetime (not just a date) because financial transactions need precision — a purchase at 2:30 PM is different from one at 2:31 PM for fraud detection.

The `merchant` property captures where the transaction occurred — useful for spending category analysis.

## New relationship

- **has_transaction** — `Account` → `Transaction` (one-to-many)
  Each account has many transactions over time, but each transaction belongs to one account.

This extends the ownership chain: `Customer → Account → Transaction`.

## The growing graph

<ontology-embed id="official/finance-step-2" diff="official/finance-step-1" height="400px"></ontology-embed>

*Transaction adds the activity layer. The ownership chain grows: Customer → Account → Transaction.*

## What we learned

- **Datetime precision** matters for financial and compliance scenarios
- **Ownership chains** (Customer → Account → Transaction) enable drill-down queries
- The `merchant` property opens up spending analysis without adding a Merchant entity
- Each new entity deepens the questions you can answer

```quiz
Q: Why does Transaction use a datetime type for timestamp instead of a date?
- Datetime is the default property type for all time-based fields
- Financial transactions require time-of-day precision for fraud detection and audit trails [correct]
- Date types are deprecated in modern ontologies
- Datetime uses less storage than date
> Financial compliance and fraud detection require precise timestamps. Two transactions on the same date but minutes apart could indicate a fraud pattern. Datetime captures both date and time, providing the precision needed.
```

Next, we'll add Loan and Investment to complete the banking product suite.

---

# Complete Banking Model

Add Loan and Investment to complete the banking ontology — connecting credit products and portfolio holdings.

## Financial products

Beyond basic accounts and transactions, banks offer two major product categories:

- **Loans** — credit products where the bank lends money
- **Investments** — holdings where customers grow wealth

Adding these completes the picture and creates interesting multi-path relationships.

## Loan

| Property | Type | Identifier? |
|---|---|---|
| `loanId` | string | ✓ |
| `principal` | decimal (USD) | |
| `apr` | decimal (%) | |
| `term` | integer (months) | |
| `status` | string | |

The `term` is an integer measured in months — a common pattern for duration properties. The `apr` (Annual Percentage Rate) uses a percentage unit.

## Investment

| Property | Type | Identifier? |
|---|---|---|
| `holdingId` | string | ✓ |
| `symbol` | string | |
| `shares` | decimal | |
| `purchasePrice` | decimal (USD) | |
| `currentValue` | decimal (USD) | |

The `symbol` property (e.g., MSFT, AAPL) identifies the stock. Having both `purchasePrice` and `currentValue` enables gain/loss calculations.

## New relationships

Four relationships connect the financial products:

- **has_loan** — `Customer` → `Loan` (one-to-many)
  A customer can have multiple loans.

- **funds** — `Account` → `Loan` (one-to-many)
  An account serves as the payment source for loan repayments.

- **holds** — `Customer` → `Investment` (one-to-many)
  A customer's investment portfolio.

- **linked_to** — `Account` → `Investment` (one-to-many)
  A brokerage account linked to investment holdings.

> **Multi-path pattern:** Investment connects to Customer through *two* different paths: directly via `holds` and indirectly via `Account → linked_to`. This redundancy is intentional — it models both ownership (who holds it?) and funding (which account backs it?).

## The complete graph

<ontology-embed id="official/finance-step-3" diff="official/finance-step-2" height="500px"></ontology-embed>

*The complete Banking & Finance ontology: 5 entities, 6 relationships. Loan and Investment connect through both Customer and Account.*

## What the complete model enables

| Question | Graph path |
|---|---|
| Which high-risk customers have large loans? | Customer (riskProfile=high) → Loan (principal > 100K) |
| What's the portfolio value for our top customers? | Customer → Investment (sum currentValue) |
| Which accounts fund both loans and investments? | Account → Loan AND Account → Investment |
| Which customers' investments outperform their loan costs? | Customer → Investment (currentValue) vs Customer → Loan (principal × apr) |

## GQL query example

Find customers whose investment portfolio exceeds their total loan principal:

```gql
MATCH (c:Customer)-[:holds]->(inv:Investment),
      (c)-[:has_loan]->(loan:Loan)
WITH c, SUM(inv.currentValue) AS portfolio, SUM(loan.principal) AS debt
WHERE portfolio > debt
RETURN c.name, portfolio, debt
```

## What we built

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | Customer, Account | 2 | Ownership, financial identifiers |
| 2 | Transaction | 3 | Activity tracking, datetime precision |
| 3 | Loan, Investment | 5 | Financial products, multi-path relationships |

## Key takeaways

1. **Ownership chains** (Customer → Account → Transaction) enable compliance queries
2. **Datetime precision** is critical for financial data
3. **Multi-path relationships** model different aspects of the same connection
4. **Duration properties** (term in months) use integers with units
5. Financial ontologies describe data shape — sensitive data stays in source systems

```quiz
Q: Why does Investment connect to both Customer (via "holds") and Account (via "linked_to")?
- It's a mistake — only one relationship is needed
- Each relationship models a different aspect: ownership vs. funding source [correct]
- Investment needs at least two relationships to be valid
- One-to-many relationships always come in pairs
> The "holds" relationship answers "who owns this investment?" while "linked_to" answers "which account funds it?" These are different questions with potentially different answers (e.g., a joint account funding one person's investment).
```

You've completed the Banking & Finance learning path! Load any step from the [catalogue](#/catalogue) to explore it interactively.
