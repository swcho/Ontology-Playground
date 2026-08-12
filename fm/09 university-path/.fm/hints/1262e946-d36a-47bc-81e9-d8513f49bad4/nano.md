A clean flat-design educational infographic, 16:9 landscape, titled "Same Edges, Opposite Traversal" in a bold sans-serif header at the top center. Subtitle underneath in smaller grey text: "Schema direction vs query traversal".

Layout: two stacked horizontal panels sharing the same five node positions, so the eye reads top-to-bottom as a before/after comparison. A thin horizontal divider line separates them.

TOP PANEL, labeled on the left edge with a small vertical tag reading "SCHEMA DIRECTION": four rounded rectangle nodes arranged in a single horizontal row, evenly spaced, left to right — a blue node labeled "Department", an amber node labeled "Course", a green node labeled "Enrollment", a purple node labeled "Student". Between them, three thick solid arrows that show the fixed, defined edge directions:
- from "Department" pointing RIGHT into "Course", edge label "offers"
- from "Enrollment" pointing LEFT into "Course", edge label "for_course"
- from "Student" pointing LEFT into "Enrollment", edge label "enrolls_in"
So two arrowheads collide at "Course". Place a small red circular badge with a downward caret just under the "Course" node, labeled "Arrows meet here". Place a small grey caption under the "Enrollment" node reading "Junction entity".

BOTTOM PANEL, labeled on the left edge with a small vertical tag reading "QUERY TRAVERSAL": the same four nodes in the same horizontal positions, drawn faded/outline-only in light grey. Overlaid on top, one long continuous DASHED arrow in bright orange sweeping left to right, starting at "Department", passing over "Course" and "Enrollment", and ending with a single large arrowhead at "Student". Three small orange step circles numbered 1, 2, 3 sit on the dashed line between consecutive nodes. Under the dashed path, a monospace code strip on a dark rounded background showing: (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student) — with the two "<-" tokens highlighted in orange and the one "->" token highlighted in blue.

Bottom strip: three short takeaway chips in a row — a blue chip "Edges never move", an orange chip "Walk any direction", a grey chip "Wrong arrow = 0 rows".

Style: clean flat design, educational infographic, white background, soft pastel node fills with darker matching outlines, generous white space, thick geometric arrows, rounded corners, no gradients, no drop shadows, no 3D, crisp modern sans-serif typography, high contrast, all labels short and legible.
