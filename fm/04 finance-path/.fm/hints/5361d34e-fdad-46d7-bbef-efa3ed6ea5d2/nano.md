Create a clean flat-design educational infographic, 16:9 landscape, titled at the top center in bold: "Multi-System JOIN becomes One Graph Path" with a smaller Korean subtitle underneath: "시스템 간 조인 → 하나의 경로 패턴".

Split the canvas into two vertical panels of equal width, separated by a thin vertical divider with a large right-pointing arrow at its middle labeled "ONTOLOGY".

LEFT PANEL (tinted pale red/grey background, header label "Relational: 4 systems"):
Show four separate grey database cylinder icons scattered in a loose square arrangement, each with a short label under it: "Core Banking", "Payment Processor", "Credit Bureau", "Loan Ledger". Draw tangled crossing dashed red lines between all four cylinders, each dashed line tagged with a tiny key icon and messy mismatched key labels: "acct_num = account_no", "cust_ref = customer_id", "ssn_hash = subject_hash". Under the tangle place a small red banner: "5 JOINs + ETL mapping".

RIGHT PANEL (tinted pale blue background, header label "Ontology: one path"):
Draw a single clean left-to-right chain of four rounded rectangle nodes connected by bold blue arrows, evenly spaced:
Node 1 (grey outline): "Transaction"
Node 2 (grey outline): "Account"
Node 3 (highlighted, amber fill): "Customer"
Node 4 (highlighted, amber fill): "Loan"
Label each arrow above the line with the relationship name in small monospace text, and mark direction of traversal below it:
Arrow 1: "has_transaction" / "reverse"
Arrow 2: "owns" / "reverse"
Arrow 3: "has_loan" / "forward"
Attach a small filter tag below Node 3 with a funnel icon: "riskProfile = 'high'".
Attach a small filter tag below Node 4 with a funnel icon: "principal > 100000".
Make both filter tags point up at their node with a short connector line, so it is clear filters sit on nodes, not on arrows.

BOTTOM STRIP spanning full width: a single dark rounded bar containing centered monospace text in one line:
"MATCH (t:Transaction)<-[:has_transaction]-(a:Account)<-[:owns]-(c:Customer)-[:has_loan]->(l:Loan)"
with a small tag at its left end reading "GQL".

Style: clean flat vector infographic, generous white space, thin consistent line weights, muted palette of navy, amber, soft red and grey on off-white, sans-serif labels, monospace only for code and relationship names. All labels short and exactly as specified, no extra text, no watermark, high legibility.
