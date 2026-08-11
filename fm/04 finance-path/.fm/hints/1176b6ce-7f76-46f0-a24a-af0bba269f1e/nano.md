Create a clean, flat-design educational infographic titled "Banking & Finance Ontology: 5 Entities, 6 Relationships" with a small subtitle "완성된 온톨로지 규모". Aspect ratio 16:9, landscape, white or very light gray background, generous whitespace, crisp sans-serif typography, no photographic textures, no drop shadows beyond a subtle card edge.

LAYOUT: one large central entity-relationship diagram occupying about 78% of the canvas, with a slim vertical legend strip down the right edge (about 22%). Visual flow reads left to right: Customer on the left, Account in the center, and the three attached entities on the right.

CENTRAL ER DIAGRAM — five rounded rectangle entity cards, each showing the entity name in bold on the first line and its identifier property in smaller monospace type on the second line:

1. "Customer" / "customerId (ID)" — far left, vertically centered. Fill light blue, blue border.
2. "Account" / "accountNumber (ID)" — center, vertically centered. Fill light blue, blue border.
3. "Transaction" / "transactionId (ID)" — right column, top. Fill light green, green border.
4. "Loan" / "loanId (ID)" — right column, middle. Fill light amber, amber border.
5. "Investment" / "holdingId (ID)" — right column, bottom. Fill light amber, amber border.

SIX DIRECTED EDGES — each drawn as a clean arrow with a single arrowhead at the target, labeled with the relationship name in monospace plus a cardinality badge "1:N" in a small pill:

- Customer to Account, label "owns  1:N"
- Account to Transaction, label "has_transaction  1:N"
- Customer to Loan, label "has_loan  1:N" — draw as a gentle curve sweeping below the Account card so it does not overlap it
- Account to Loan, label "funds  1:N"
- Customer to Investment, label "holds  1:N" — draw as a gentle curve sweeping below, clearly separate from the has_loan curve
- Account to Investment, label "linked_to  1:N"

Keep every label fully legible and non-overlapping; route curves with clear separation. Make the two Customer-to-product curves a slightly lighter stroke weight so the diagram still reads clearly.

COLOR MEANS GROWTH STAGE: blue = Step 1, green = Step 2, amber = Step 3. Place a tiny circular numbered badge ("1", "2", "3") in the top-left corner of each entity card matching its stage color.

RIGHT LEGEND STRIP — stacked top to bottom:
- A small heading "Growth in 3 steps"
- Three color swatch rows: blue square with "Step 1 · Customer, Account · 2 entities"; green square with "Step 2 · + Transaction · 3 entities"; amber square with "Step 3 · + Loan, Investment · 5 entities"
- A thin divider line
- A highlighted callout box titled "Multi-path pattern" with two short lines of monospace text: "Customer → Loan (owner)" and "Account → Loan (funder)"
- At the very bottom, two large stat tiles side by side: "5" above the word "ENTITIES" and "6" above the word "RELATIONSHIPS", numbers set very large and bold.

STYLE: modern educational infographic, flat vector illustration, limited palette of blue, green, amber, and dark slate gray on white, high contrast text, thin 2px borders, aligned grid, everything sharp and readable at a glance.
