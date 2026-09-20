"""Configuration constants.

The essential/desirable threshold lives here and nowhere else. Changing your
mind about it is a one-line edit with no reload, which is the whole reason
importance is stored raw in the database rather than as a precomputed label.
"""

from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "saycep.db"

# O*NET Importance scale runs 1-5. A skill at or above this is essential to the
# occupation; below it, desirable. See FR-07.
#
# Why 3.5: importance ratings cluster hard on whole numbers and 3.0 alone holds
# 32.5% of them, so a cut at 3.0 would flip a third of the dataset depending on
# whether the comparison is >= or >. 3.5 sits in the sparse gap between the 3.0
# and 4.0 clusters. It also yields about 7.3 essential skills per occupation,
# where 3.0 gives 14.4 -- and fourteen "essential" skills is not a gap anyone
# can act on.
ESSENTIAL_THRESHOLD = 3.5

IMPORTANCE_SCALE_MAX = 5.0

# FR-08: no fewer than three intermediate steps, plus the target itself.
PATHWAY_INTERMEDIATE_STEPS = 3
