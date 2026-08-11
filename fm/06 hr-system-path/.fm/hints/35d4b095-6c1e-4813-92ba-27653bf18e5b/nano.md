Create a clean flat-design educational infographic in ERD style, 16:9 landscape, titled at the top center: "HR System Ontology — 5 Entities". Directly under the title, a small single-line subtitle in gray: "5 entities, 4 relationships, one hub".

Layout: a single centered entity-relationship diagram filling the canvas, generous white background, no crossing lines. Eye flow starts at the center card, then branches down-left into a diamond and its two children, then right to a separate card.

CENTER: a large rounded rectangle card labeled "Employee" with a person icon in its header. Inside the card, three short property lines stacked vertically: a key icon next to "employeeId", then "hire date", then "job level". Give this card a small badge above it reading "HUB" to mark it as the only branching entity. Card fill color: soft blue.

From the Employee card, draw exactly two solid connector lines with small directional arrowheads:

1. One line going DOWN-LEFT to a diamond shape labeled "Assignment", with the cardinality label "1:N" placed on the line. The diamond is drawn as a rotated square (classic ERD relationship shape), amber or warm orange fill, with three short property lines beside or below it: "start date", "end date", "is primary".

2. One line going RIGHT to a rounded rectangle card labeled "PerformanceReview" with a star icon in its header, cardinality label "1:N" on the line. Inside the card two short property lines: "rating", "review period". Same amber or warm orange fill as the diamond.

From the "Assignment" diamond, draw exactly two solid connector lines fanning DOWNWARD, one to the lower-left and one to the lower-right, each with an arrowhead and the cardinality label "N:1":

- Lower-left: a rounded rectangle card labeled "Department" with a building icon, two property lines: a key icon next to "departmentId", then "budget". Card fill color: soft teal green.
- Lower-right: a rounded rectangle card labeled "Position" with a badge icon, two property lines: a key icon next to "positionId", then "salary band". Card fill color: soft teal green.

Highlight overlay: trace a thin dashed bright line along the path from "Department" up through "Assignment" up to "Employee" and across to "PerformanceReview", with one small pill label next to it reading "Cross query via Employee".

BOTTOM: a small horizontal legend strip, centered, with three color swatches and short labels: a blue swatch labeled "Person", a teal green swatch labeled "Org structure", an amber swatch labeled "Relationship / Event". Keep the legend compact and clearly smaller than the diagram.

Style: clean flat vector infographic, educational poster look, thin consistent line weights, rounded corners, soft subtle shadows, no gradients, no photographic elements. Typography: crisp modern sans-serif, strong readable hierarchy, all labels short and correctly spelled, property text noticeably smaller than entity names. Keep every label under five words. Do not add any paragraphs of body text.
