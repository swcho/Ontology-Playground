Create a clean flat-design educational infographic, 16:9 landscape, titled "Why Enrollment Must Be a Node" at the top center in bold sans-serif, with a small Korean subtitle underneath reading "정션 엔티티 패턴".

Layout: three horizontal panels of equal height stacked as a left-to-right reading flow, separated by thin light-gray dividers. A large gray arrow points from Panel A to Panel B.

PANEL A (left, muted red/gray tint), header label "DIRECT LINK — BROKEN":
Two rounded rectangle nodes side by side: a blue node labeled "Student" and a green node labeled "Course", joined by a single plain line labeled "takes". Above the middle of that line, draw three small floating tag chips labeled "grade", "semester", "status" — each chip is dashed-outline, semi-transparent, tilted, and falling downward with small motion lines, with a red X mark over them. Below the line put a short caption "No place to attach". Add two thin red dotted arrows from the chips pointing at Student and at Course, each crossed out with a small red X, with tiny labels "not a student trait" and "not a course trait".

PANEL B (center, healthy blue/teal tint), header label "JUNCTION ENTITY — WORKS":
Three nodes in a row: blue "Student" — orange diamond-shaped node "Enrollment" — green "Course". Solid arrows: "enrolls_in" from Student to Enrollment, "for_course" from Enrollment to Course. Under the arrows show tiny cardinality tags "1:N" and "N:1". Attached under the orange Enrollment node, draw a small white property card listing four rows with a key icon on the first: "enrollmentId", "semester", "grade", "status". A green check badge sits beside the Enrollment node.

PANEL C (right, neutral light tint), header label "NOW QUERYABLE":
A code-window box with rounded corners showing three short monospace lines: "MATCH (s)-[:enrolls_in]->(e)", "-[:for_course]->(c)", "RETURN e.grade". Below it a callout bubble with the question "Grade this semester?" and a green check mark. Underneath, a small two-item checklist with green ticks: "Retake same course" and "Track drop status".

BOTTOM STRIP spanning full width, a slim dark bar with white text reading: "Attributes on the link → promote link to node".

Style: clean flat vector infographic, educational textbook quality, generous white space, soft rounded shapes, subtle drop shadows, limited palette of blue, teal, orange, muted red and warm gray on an off-white background, crisp legible sans-serif typography, no photographic texture, no clutter. Aspect ratio 16:9.
