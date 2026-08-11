# Supply Chain Disruption & Risk Propagation

Master proactive risk management — model how supplier disruptions cascade through components and product lines, and automate mitigation decisions with ontology-driven data agents.

Source: content/learn/supply-chain-disruption-path (4 articles merged)

---

# Scenario Overview

## The challenge

Your manufacturing operation depends on a complex web of suppliers. One disruption — a natural disaster, geopolitical event, quality issue, or cyber attack — doesn't just affect that one supplier. It ripples through:

- **Components** that depend on that supplier
- **Product lines** that use those components
- **Revenue** when products can't be shipped
- **Production timelines** that slip week by week

Without visibility into these cascades, you react after the damage is done. With it, you **anticipate and act before customers are affected**.

## Real-world example

A semiconductor supplier in Taiwan experiences a power outage lasting 48 hours:

```
Disruption: Taiwan Supplier Outage
  ↓
Affects: ChipX component supply
  ↓
Impacts: 3 product lines (laptops, tablets, displays)
  ↓
Cascades: Production halts in 2 weeks (inventory runs out)
  ↓
Result: $12M revenue at risk, customer orders delayed
  ↓
Mitigation: Activate pre-qualified alternative supplier + safety stock
```

**Without an ontology**, this analysis takes days and manual spreadsheets.  
**With an ontology**, an AI agent can:
1. Identify all affected components within minutes
2. Trace to all product lines and production timelines
3. Recommend alternative suppliers and safety stock quantities
4. Calculate cost-benefit of each mitigation action
5. Trigger automated alerts and procurement workflows

## What you'll build

Over four steps, we'll construct a production-grade ontology that powers this intelligence:

| Step | Focus | Outcome |
|---|---|---|
| 1 | Core entities (Supplier, Component, ProductLine, Disruption) | Vocabulary of your supply chain |
| 2 | Entity properties and identifiers | Rich attributes for risk calculation |
| 3 | Relationships and cascade modeling | Impact propagation graph |
| 4 | Risk assessment and mitigation actions | Decision automation |

By the end, you'll have a 7-entity ontology with:
- **40 properties** capturing reliability scores, inventory levels, costs, timelines
- **7 relationships** modeling the disruption cascade
- **Fabric IQ compatibility** for data agent grounding and real-time alerting

## Key concepts

- **Disruption events** — the trigger (natural disaster, cyber attack, financial failure)
- **Impact propagation** — how disruptions cascade through dependencies
- **Risk assessment** — calculating revenue at risk and time to impact
- **Mitigation actions** — concrete steps to reduce or eliminate impact
- **Alternative suppliers** — pre-qualified backups with capacity and cost trade-offs

Let's start by understanding the core entities and relationships that make resilience decisions possible.

---

# Core Entities & Properties

## The 7 entity types

Your ontology captures the full lifecycle of a supply chain disruption, from the triggering event through detection, assessment, and response.

### Tier 1: The network

**Supplier**
- Represents external companies providing raw materials or components
- Key properties: `supplierId` (unique), `name`, `country`, `tier` (Tier 1/2/3), `reliabilityScore` (0-100), `singleSourced` (boolean)
- Use case: Identify critical single-source suppliers that are risk amplifiers

**Component**
- A part, material, or sub-assembly sourced from one or more suppliers
- Key properties: `componentId`, `name`, `category` (Electronic/Mechanical/Chemical/Packaging/Raw Material), `daysOfSupplyOnHand`, `criticalityLevel` (Critical/High/Medium/Low)
- Use case: Track which components can survive supplier interruptions based on safety stock

**ProductLine**
- A group of finished products sharing common components
- Key properties: `productLineId`, `name`, `annualRevenue`, `marketSegment`, `productionStatus` (Active/At Risk/Halted/Discontinued)
- Use case: Calculate revenue exposure and production timeline impact

### Tier 2: The disruption

**DisruptionEvent**
- An event interrupting or threatening normal supply from one or more suppliers
- Key properties: `eventId`, `type` (Natural Disaster/Geopolitical/Financial/Logistics/Quality Recall/Pandemic/Cyber Attack), `severity` (Critical/High/Medium/Low), `startDate`, `estimatedDurationDays`, `region`
- Use case: Classification and severity determine escalation level and response timeline

### Tier 3: The analysis

**RiskAssessment**
- An analysis of business impact when a disruption affects the supply chain
- Key properties: `assessmentId`, `assessedDate` (datetime), `revenueAtRisk` (USD), `timeToImpactDays`, `confidenceLevel` (High/Medium/Low), `recommendedAction`
- Use case: Quantify impact in business terms (money and time) to prioritize response

**MitigationAction**
- A concrete step to reduce or eliminate disruption impact
- Key properties: `actionId`, `type` (Activate Alternative Supplier/Increase Safety Stock/Redesign Component/Reduce Production/Expedite Shipment/Customer Communication), `status` (Proposed/Approved/In Progress/Completed/Cancelled), `estimatedCost` (USD), `leadTimeSavedDays`
- Use case: Track which actions have been taken and their actual vs. estimated effectiveness

### Tier 4: The backup

**AlternativeSupplier**
- A qualified backup supplier capable of substituting for a primary supplier
- Key properties: `altSupplierId`, `name`, `country`, `qualificationStatus` (Pre-qualified/Approved/Pending Audit/Not Qualified), `capacityAvailable` (units/month), `pricePremiumPercent` (%))
- Use case: Rapidly activate backups with known capacity and cost impact

## Property types and validations

Each property has a type that shapes how AI agents and dashboards work with it:

| Type | Example | Use in agents |
|------|---------|---------------|
| `string` | Supplier name, Component category | Search, filtering, reporting |
| `integer` | Days of supply, capacity, units | Threshold-based alerts |
| `decimal` | Revenue, price premium, reliability score | Cost-benefit calculations |
| `date` | Disruption start date | Timeline comparisons |
| `datetime` | Risk assessment timestamp | Audit trails, trending |
| `enum` | Supplier tier, disruption type, severity | Classification, decision trees |
| `boolean` | Single-sourced flag | Risk flagging |

## Identifier properties

Each entity has a unique identifier:

```
Supplier → supplierId (e.g., "SUPP-00456")
Component → componentId (e.g., "COMP-SEM-0821")
ProductLine → productLineId (e.g., "PL-LAP-2024")
DisruptionEvent → eventId (e.g., "DISR-202405-TAIWAN-001")
RiskAssessment → assessmentId (e.g., "RA-20240501-SEM-001")
MitigationAction → actionId (e.g., "MA-20240501-ALT-SUPP")
AlternativeSupplier → altSupplierId (e.g., "ALTSUPP-00789")
```

These IDs are how you and your agents refer to specific instances in queries and reports.

## Cardinality and relationships

Entities connect via relationships with defined cardinality:

- **One-to-many**: A supplier provides many components; a disruption affects many suppliers
- **Many-to-many**: Components are used in many product lines; mitigation actions activate many alternative suppliers
- **Many-to-one**: Alternative suppliers can replace one primary supplier

We'll explore the full relationship map next.

---

# Risk Propagation Model

## The cascade: 7 relationships

The power of your ontology lies in its relationships — they encode how impact flows through your supply chain. A data agent follows these paths to answer questions like "How many product lines are exposed to this supplier failure?"

### 1. **Supplier supplies Component** (one-to-many)

```
Supplier "ChipX Corp" 
  supplies→ Component "GPU Module"
         → Component "Memory Board"
         → Component "Power Supply"
```

- **Why it matters**: Disrupting one supplier affects all its dependent components
- **Query example**: "Show me all components from suppliers in Taiwan"

### 2. **Component used in ProductLine** (many-to-many)

```
Component "GPU Module"
  usedIn→ ProductLine "Gaming Laptop 2024"
       → ProductLine "Workstation Pro"
       → ProductLine "Tablet Plus"
```

- **Why it matters**: A single component failure can halt multiple product lines
- **Query example**: "How many product lines depend on this component?"

### 3. **DisruptionEvent affects Supplier** (many-to-many)

```
DisruptionEvent "Taiwan Power Outage 2024-05-01"
  affects→ Supplier "ChipX Corp"
        → Supplier "Memory Inc"
```

- **Why it matters**: One disaster can hit multiple suppliers simultaneously
- **Query example**: "Which suppliers are in the flood zone?"

### 4. **DisruptionEvent triggers RiskAssessment** (one-to-many)

```
DisruptionEvent "Taiwan Power Outage"
  triggers→ RiskAssessment "Gaming Laptop - Impact Analysis"
         → RiskAssessment "Workstation - Impact Analysis"
```

- **Why it matters**: Each disruption triggers detailed impact analysis for affected product lines
- **Query example**: "What's the total revenue at risk from this disruption?"

### 5. **RiskAssessment recommends MitigationAction** (one-to-many)

```
RiskAssessment "Gaming Laptop - Impact Analysis"
  recommends→ MitigationAction "Activate Alt Supplier X"
           → MitigationAction "Increase Safety Stock"
           → MitigationAction "Redesign Component"
```

- **Why it matters**: Each impact analysis produces a prioritized action list
- **Query example**: "What's the best action to minimize disruption impact?"

### 6. **MitigationAction activates AlternativeSupplier** (many-to-many)

```
MitigationAction "Activate Alt Supplier X"
  activates→ AlternativeSupplier "ChipX Europe"
          → AlternativeSupplier "SemiCorp Japan"
```

- **Why it matters**: One action can bring multiple backups online simultaneously
- **Query example**: "Which pre-qualified suppliers can take over?"

### 7. **AlternativeSupplier canReplace Supplier** (many-to-one)

```
AlternativeSupplier "ChipX Europe"
  canReplace→ Supplier "ChipX Corp"

AlternativeSupplier "SemiCorp Japan"  
  canReplace→ Supplier "ChipX Corp"
```

- **Why it matters**: Multiple approved backups exist for critical suppliers
- **Query example**: "Is there an approved backup for this supplier?"

## The complete cascade example

Let's trace impact through a real scenario:

```
DISRUPTION
│
├─ Taiwan Power Outage (2024-05-01, Critical severity)
│
├─ AFFECTS
│  └─ Supplier "ChipX Corp" (singleSourced=true)
│     ├─ SUPPLIES
│     │  ├─ Component "GPU Module" (daysOfSupplyOnHand=3)
│     │  │  ├─ USED IN
│     │  │  │  ├─ ProductLine "Gaming Laptop 2024" ($50M annual revenue)
│     │  │  │  ├─ ProductLine "Workstation Pro" ($30M annual revenue)
│     │  │  │
│     │  │  └─ TRIGGERS RiskAssessment
│     │  │     ├─ revenueAtRisk=$80M
│     │  │     ├─ timeToImpactDays=3
│     │  │     │
│     │  │     └─ RECOMMENDS
│     │  │        ├─ MitigationAction "Activate ChipX Europe"
│     │  │        │  ├─ estimatedCost=$2M
│     │  │        │  ├─ leadTimeSavedDays=2
│     │  │        │  │
│     │  │        │  └─ ACTIVATES
│     │  │        │     ├─ AlternativeSupplier "ChipX Europe" 
│     │  │        │     │  ├─ qualificationStatus=Approved
│     │  │        │     │  ├─ capacityAvailable=50,000 units/month
│     │  │        │     │  ├─ pricePremiumPercent=12%
│     │  │        │     │  │
│     │  │        │     │  └─ CAN REPLACE
│     │  │        │     │     └─ Supplier "ChipX Corp"
│     │  │        │     │
│     │  │        │     └─ AlternativeSupplier "SemiCorp Japan"
│     │  │        │        └─ (secondary option)
│     │  │        │
│     │  │        └─ MitigationAction "Increase Safety Stock"
│     │  │           └─ estimatedCost=$500K
│     │  │
│     │  └─ Component "Memory Board"
│     │     └─ (similar cascade...)
```

## Why this structure enables automation

Your data agent can now:

1. **Detect** — "Monitor these suppliers and this region"
2. **Trace** — "When ChipX Corp has issues, automatically trace to all 14 affected product lines"
3. **Quantify** — "Calculate total revenue at risk ($80M) and time to impact (3 days)"
4. **Recommend** — "Activate pre-qualified alternatives that save 2 days and cost $2M vs. $80M loss"
5. **Act** — "Send procurement alerts, update production schedules, notify stakeholders"
6. **Learn** — "Track which actions actually worked and their real vs. estimated impact"

## Cardinality rules

| Relationship | Cardinality | Why |
|---|---|---|
| Supplier → Component | 1:N | One supplier may provide many components |
| Component → ProductLine | M:N | Components reused; products share components |
| Disruption → Supplier | M:N | One disaster hits multiple suppliers; supplier faces multiple threats |
| Disruption → Assessment | 1:N | Each disruption spawns assessments for each affected product line |
| Assessment → Action | 1:N | Each assessment recommends multiple actions |
| Action → Alternative | M:N | One action activates multiple backups; backups handle multiple situations |
| Alternative → Supplier | M:1 | Multiple pre-qualified backups exist for one primary supplier |

Next, we'll see how to use this model to execute mitigation workflows in practice.

---

# Mitigation Execution & Automation

## From model to action

Your ontology is now ready to power real-time decision automation. Here's how it flows from disruption detection to mitigation execution:

### Phase 1: Detection (minute 0)

**Input**: External signal (supplier goes offline, natural disaster alert, quality issue reported)

**Your ontology enables**:
```
Data Agent Query:
  "Which suppliers are affected by the Taiwan earthquake?"
  ↓
  Matches: Supplier.country="Taiwan" + DisruptionEvent.region="Taiwan" 
           + DisruptionEvent.type="Natural Disaster"
  ↓
  Result: 3 critical suppliers identified
```

### Phase 2: Trace impact (minute 5)

**Input**: List of affected suppliers

**Your ontology enables**:
```
Data Agent Query:
  "For these 3 suppliers, show me all components they supply"
  ↓
  Follows: Supplier → supplies → Component
  ↓
  Result: 47 components identified
  
Then: "For these 47 components, which product lines use them?"
  ↓
  Follows: Component → usedIn → ProductLine
  ↓
  Result: 12 product lines exposed
```

### Phase 3: Quantify impact (minute 15)

**Input**: List of exposed product lines

**Your ontology enables**:
```
Calculation Engine:
  For each exposed ProductLine:
    revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand
    urgency = 100 - (daysOfSupplyOnHand * 10)
  
  Aggregate:
    total_revenue_at_risk = SUM(revenue_at_risk)
    critical_product_lines = WHERE urgency > 70
    
  Result: 
    Total at risk: $127M
    Critical timeline: 3 days
    Affected customers: 450,000+
```

### Phase 4: Recommend actions (minute 20)

**Input**: Risk assessment results

**Your ontology enables**:
```
Recommendation Engine:
  For each component in each affected product line:
    1. Find AlternativeSupplier records where:
       - qualificationStatus="Approved"
       - capacityAvailable >= demand
       - country NOT IN earthquake_region
    
    2. Score each alternative by:
       - Lead time saved (leadTimeSavedDays)
       - Cost impact (pricePremiumPercent)
       - Reliability (reliabilityScore)
    
    3. Recommend top 3 actions with ROI:
       - Action A: Activate ChipX Europe (save 2 days, cost +$2M)
       - Action B: Increase safety stock (cost $500K, cover 2 weeks)
       - Action C: Redesign component (lead time unknown)
```

### Phase 5: Execute (minute 25)

**Your ontology triggers automated workflows**:

```
IF RiskAssessment.revenueAtRisk > $50M AND 
   RiskAssessment.timeToImpactDays < 5:
   
   THEN:
     1. Create PurchaseOrder for recommended AlternativeSupplier
     2. Update ProductionSchedule with new timeline
     3. Send email to:
        - Procurement team (execute purchase)
        - Operations (adjust schedules)
        - Finance (forecast $2M additional cost)
        - CEO/Board (update on exposure)
     4. Create Activator alerts with escalation policy
     5. Start monitoring MitigationAction.status
```

## Real-world workflow: End-to-end

### Day 1: Disruption detected

```
10:30 AM: Taiwan earthquake magnitude 6.8
          ↓
10:45 AM: Your system detects: DisruptionEvent created
          ├─ type = "Natural Disaster"
          ├─ severity = "Critical"
          ├─ region = "Taiwan"
          ├─ estimatedDurationDays = 7
          
10:46 AM: Data Agent traces impact
          ├─ 3 critical suppliers affected
          ├─ 47 components halted
          ├─ 12 product lines exposed
          ├─ $127M revenue at risk
          ├─ 3 days to production stoppage
          
10:47 AM: RiskAssessment created
          ├─ assesses impact for each product line
          ├─ recommends actions ranked by ROI
          
10:48 AM: MitigationActions auto-created
          ├─ PO issued to ChipX Europe (approved alternative)
          ├─ Safety stock orders placed
          ├─ Alerts sent to procurement, ops, finance
          
10:50 AM: Activator triggered
          ├─ Real-time dashboard shows impact + actions
          ├─ Escalation policy notifies leadership
          ├─ Procurement team acknowledges + confirms receipt
          
11:30 AM: MitigationAction.status = "In Progress"
          ├─ Purchase order in progress
          ├─ ChipX Europe confirms 48-hour shipment
          ├─ Production impact reduced from 7 days → 3 days
```

### Day 2-4: Monitoring and adjustment

```
Every 4 hours:
  - Check DisruptionEvent.estimatedDurationDays (update if recovery changes)
  - Monitor MitigationAction progress
  - Recalculate RiskAssessment with latest inventory data
  - Alert if leadTimeSavedDays slips (alternative supplier delays)
  - Recommend contingency actions if needed
  
Day 3: ChipX Europe shipment received
  ├─ MitigationAction.status = "Completed"
  ├─ Inventory restored for 47 components
  ├─ Production resumes (3-day delay, not 7-day)
  ├─ Actual cost: $2.1M (estimated $2M)
  ├─ Revenue protected: ~$100M of $127M exposure
```

## Connecting to Fabric IQ

Your ontology integrates seamlessly with Fabric IQ data agents:

```
User: "What's our supply chain risk exposure right now?"
  ↓
Data Agent grounds query against your ontology:
  1. Find all Supplier records with singleSourced=true
  2. For each, find Components they supply
  3. Trace to ProductLines using those components
  4. Calculate revenueAtRisk for each ProductLine
  5. Return ranked list by revenueAtRisk
  
Agent Response:
  "You have 3 critical single-source suppliers. 
   If any are disrupted, you lose ~$180M in 
   4-9 days. We recommend pre-qualifying 
   8 alternative suppliers (list attached)."

User: "Which alternatives are approved for ChipX?"
  ↓
Agent Query:
  AlternativeSupplier WHERE:
    canReplace.Supplier.name = "ChipX Corp"
    AND qualificationStatus = "Approved"
  ↓
Result:
  - ChipX Europe (capacity: 50K/month, +12% cost)
  - SemiCorp Japan (capacity: 30K/month, +18% cost)
  - Semiconductor Direct USA (capacity: 25K/month, +15% cost)
```

## Continuous improvement

Track the effectiveness of your mitigation model:

| Metric | Calculation | Goal |
|--------|-------------|------|
| Detection speed | Hours from disruption to RiskAssessment | < 1 hour |
| Trace accuracy | % of actual affected components identified | > 95% |
| Impact estimate accuracy | Estimated vs. actual revenue at risk | ±10% |
| Time to mitigation | Hours from assessment to MitigationAction execution | < 2 hours |
| Cost efficiency | Actual cost vs. estimated cost of actions | ±5% |
| Revenue protection rate | % of at-risk revenue protected by actions | > 80% |

Each disruption event becomes a training opportunity. Your agents learn which alternative suppliers actually perform, which lead times hold up, and which product lines are most resilient.

## Summary

Your Supply Chain Disruption & Risk Propagation ontology is production-ready:

✅ **7 entity types** capture the full disruption lifecycle  
✅ **40 properties** provide rich context for decision-making  
✅ **7 relationships** model realistic impact cascades  
✅ **Fabric IQ compatible** for natural-language agents  
✅ **Automation-ready** with enum classifications and timestamps  
✅ **Measurable outcomes** — reduce disruption impact from days to hours  

Deploy it, monitor it, and watch your supply chain resilience transform.
