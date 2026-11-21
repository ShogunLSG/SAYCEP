# Plan: the Pathway as a ladder (ADR-0034)

**Why:** a route to Electricians went through jobs at the target's own level
(repair roles) and, earlier, a millwright. The user's brief: look like a
step-by-step climb through lower zones; a goal at the bottom should not be padded.

**Rule:** build back from the target; at each step take a related, lower-zone job
(nearest zone first, same field preferred, O*NET review order, similarity >= 0.70);
at most three steps; none if nothing qualifies (`aim_directly`).

**Measured before building:** see ADR-0034 (508 of 879 goals have no ladder; the
whole catalogue as candidates gave nonsense; the 0.70 floor and the related-job
restriction came from that).

**Not done:** FR-08's "no fewer than three intermediate steps" is the author's text.
