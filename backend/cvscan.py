"""CV Scanner -- module 3 of the proposal (ADR-0014).

Reads pasted CV text and returns two things:

  1. Skill suggestions: which of O*NET's 35 skills the CV shows evidence of,
     each quoting the CV line that triggered it. The user confirms every one
     -- nothing is added to a profile automatically (FR-02's self-report rule).
  2. A goal check: how well the CV evidences one occupation -- chiefly the
     software and tools that job uses (as O*NET lists them) which the CV names.

Why it is built this way -- measured, not assumed (backend/tests/benchmark_cv.py
and ADR-0014, 5 October):

  * On the Kaggle Resume Dataset's held-out CVs, *named software and tools*
    are what track the human match score. Inferring O*NET's 35 abstract
    skills from free text tracked it worse than naive word overlap, in three
    designs tried (TF-IDF against each skill's O*NET wording; the same with
    18,000 linked task statements; nearest O*NET sentence). In practice they
    suggested "Writing" for "Fixed broken bicycles".
  * So skill suggestions come from explicit trigger words per skill (SKILL_RULES,
    our wording, kept short and quoted back to the user), and make no accuracy
    claim. The goal score leans on the evidence that measured well.

The CV text is never stored. Nothing in this module touches the profile
tables; app.py does not log request bodies.
"""

import math
import re
from collections import Counter

# Software names that are also everyday words; matching them in prose would
# be wrong far more often than right ("I chose my words", "access to").
AMBIGUOUS = {"word", "access", "project", "teams", "office", "publisher", "notes", "forms",
             "connect", "base", "go", "edge", "paint", "photos", "mail", "calendar", "maps"}

COMMON_IN_TASKS = 3       # a word in this many O*NET task statements is ordinary English
COVERAGE_WEIGHT = 0.3     # weight of key-skill coverage in the goal score (chosen on the tuning half)
TOP_SKILLS = 8            # a job's most important skills, for coverage

# Trigger words per O*NET skill. Our wording, conservative on purpose: a
# missed skill costs the user a tap, a wrong one costs their trust.
SKILL_RULES = {
    "Repairing": r"\b(fix(ed|es|ing)?|repair(ed|ing|s)?|mend(ed|ing)?)\b",
    "Installation": r"\b(install(ed|ing|s|ation)?|fitted|mounted|wired)\b",
    "Troubleshooting": r"\b(troubleshoot\w*|diagnos\w*|fault[- ]?find\w*|found (the )?faults?)\b",
    "Equipment Maintenance": r"\b(maintenance|servic(ed|ing) (cars?|vehicles?|machines?|equipment|engines?)|maintain(ed|ing)? (the )?(machines?|equipment|vehicles?|engines?|tools))\b",
    "Operation and Control": r"\b(operat(e|ed|ing) (a |an |the )?(machines?|forklifts?|equipment|tills?|vehicles?|cranes?|tractors?|pos)|driver'?s licen[cs]e|drove|driving)\b",
    "Operations Monitoring": r"\b(monitor(ed|ing)? (the )?(machines?|gauges?|equipment|systems?|production|readings?))\b",
    "Quality Control Analysis": r"\b(quality (checks?|control|assurance)|inspect(ed|ing|ions?)?|tested (the )?(products?|equipment|circuits?))\b",
    "Equipment Selection": r"\b(chose|choos(e|ing)|select(ed|ing)?) (the )?(right )?(tools?|equipment|materials?|parts?)\b",
    "Programming": r"(\b(programm(ed|ing)|coding|coded|python|javascript|java|html|css|sql)\b|c\+\+)",
    "Technology Design": r"\b(design(ed|ing)? (a |an |the )?(websites?|apps?|systems?|circuits?|products?|databases?))\b",
    "Mathematics": r"\b(maths?|mathematics|calculat\w*|accounting|bookkeeping|statistics)\b",
    "Science": r"\b(physical sciences?|life sciences?|biology|chemistry|physics|laborator\w*|experiments?)\b",
    "Reading Comprehension": r"\b(read(ing)? (and interpret(ing)? )?(\w+ )?(manuals?|instructions?|diagrams?|plans?|reports?|drawings?))\b",
    "Writing": r"\b(wrote|writ(e|ing|ten) (reports?|articles?|letters?|essays?|minutes|stories)|report writing|editor)\b",
    "Speaking": r"\b(present(ed|ations?)|public speaking|communication|debat\w*|spoke at)\b",
    "Active Listening": r"\b(listen\w*)\b",
    "Instructing": r"\b(teach\w*|taught|tutor\w*|coach\w*|mentor\w*|train(ed|ing)? (new |other |junior )?(staff|learners|others|workers|players))\b",
    "Learning Strategies": r"\b(lesson plans?|study groups?|learning methods)\b",
    "Active Learning": r"\b(quick learner|learn(ed|t)? (new things |quickly|fast)|self[- ]taught)\b",
    "Service Orientation": r"\b(customers?|clients?|serv(ed|ing) (customers|clients|people|the public)|volunteer\w*|caregiv\w*|cared for|looked after)\b",
    "Social Perceptiveness": r"\b(empath\w*|counsel+\w*|peer support)\b",
    "Coordination": r"\b(team ?work|teams?|coordinat\w*|organi[sz](ed|ing) (an |the |a )?(events?|teams?|trips?|tournaments?))\b",
    "Persuasion": r"\b(sell(ing)?|sold|sales|marketing|persuad\w*|fundrais\w*|promot(ed|ing))\b",
    "Negotiation": r"\b(negotiat\w*|bargain\w*|resolv(ed|ing) (disputes?|conflicts?)|mediat\w*)\b",
    "Time Management": r"\b(deadlines?|schedul\w*|time management|punctual\w*)\b",
    "Management of Financial Resources": r"\b(budget\w*|cash(ier)?|petty cash|treasurer|financ\w*)\b",
    "Management of Material Resources": r"\b(stock(ed|taking)?|inventory|storeroom|supplies|warehouse)\b",
    "Management of Personnel Resources": r"\b(supervis\w*|manag(ed|ing) (staff|a team|people|workers)|led (a |the )?team|team leader|captain|prefect|head (boy|girl))\b",
    "Complex Problem Solving": r"\b(problem[- ]solv\w*|solv(ed|ing) problems)\b",
    "Critical Thinking": r"\b(critical thinking|analy[sz](ed|ing|is|e))\b",
    "Judgment and Decision Making": r"\b(decision[- ]making|made decisions)\b",
    "Systems Analysis": r"\b(systems analysis)\b",
    "Systems Evaluation": r"\b(evaluat(ed|ing|ion) (the )?(systems?|processes|performance))\b",
    "Operations Analysis": r"\b(requirements (gathering|analysis)|user needs)\b",
    "Monitoring": r"\b(kept track|tracked progress|monitor(ed|ing)? (progress|performance))\b",
}


def _words(text):
    """Lower-case word sequence with plurals folded, for naming software/tools."""
    out = []
    for w in re.findall(r"[a-z0-9][a-z0-9+#.]*", (text or "").lower()):
        w = w.rstrip(".")
        if len(w) > 3 and w.endswith("es") and not w.endswith("ses"):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def lines(text):
    """CV text split into the units evidence is quoted from."""
    parts = re.split(r"[\n\r]+|(?<=[.;!?])\s+|\s[•\-*·]\s", text or "")
    return [p.strip(" •-*·\t") for p in parts if len(p.strip()) > 2]


class Index:
    """Everything the scanner needs, read once from the database."""

    def __init__(self, con):
        self.skills = {r[0]: (r[1], r[2]) for r in con.execute(
            "SELECT element_id, name, description FROM skills")}
        by_name = {n: e for e, (n, _) in self.skills.items()}
        self.rules = [(by_name[n], re.compile(rx, re.I)) for n, rx in SKILL_RULES.items()]
        assert len(self.rules) == len(self.skills), "every skill needs a rule"

        self.importance = {}
        for soc, e, imp in con.execute("SELECT soc_code, element_id, importance FROM occupation_skills"):
            self.importance.setdefault(soc, {})[e] = imp

        # Words common in O*NET's task statements are ordinary English, so a
        # one-word product name made of one ("Calyx Point" -> "point") must not
        # match on its own. Real product names appear in no task statement.
        seen = Counter()
        for (task,) in con.execute("SELECT DISTINCT task FROM occupation_tasks"):
            seen.update(set(_words(task)))
        self.common = {w for w, n in seen.items() if n >= COMMON_IN_TASKS}

        # Software and tools: the phrases to look for, and which jobs list them.
        self.software, self.tools = {}, {}
        self.occ_software, self.occ_tools = {}, {}
        for example, soc in con.execute("SELECT example, soc_code FROM occupation_technology"):
            self.occ_software.setdefault(soc, set()).add(example)
            self._alias(self.software, example, vendor_strip=True, common=self.common)
        for example, soc in con.execute("SELECT example, soc_code FROM occupation_tools"):
            self.occ_tools.setdefault(soc, set()).add(example)
            self._alias(self.tools, example, vendor_strip=False)

    @staticmethod
    def _alias(table, example, vendor_strip, common=frozenset()):
        ws = tuple(_words(example))
        if not ws:
            return
        table.setdefault(ws, example)
        # "Microsoft Excel" is usually written "Excel" -- but "Calyx Point" is
        # never written "point". A one-word remainder must be a word O*NET's
        # task statements don't use.
        if vendor_strip and len(ws) > 1:
            rest = ws[1:]
            if not (len(rest) == 1 and (len(rest[0]) < 3 or rest[0] in AMBIGUOUS or rest[0] in common)):
                table.setdefault(rest, example)


def skill_evidence(index, text):
    """{element_id: [CV lines that triggered it]} for every skill with evidence."""
    found = {}
    for line in lines(text):
        for e, rx in index.rules:
            if rx.search(line):
                found.setdefault(e, []).append(line)
    return found


def named(table, text, common=None):
    """Which known software/tools the text names (as O*NET writes them).
    Pass common= for software, so a one-word name that is ordinary English
    ("Teams", "Windows") needs its vendor ("Microsoft Teams") to count."""
    ws = _words(text)
    found = set()
    for n in (4, 3, 2, 1):
        for i in range(len(ws) - n + 1):
            hit = table.get(tuple(ws[i:i + n]))
            if hit and not (n == 1 and (len(ws[i]) < 3 or ws[i] in AMBIGUOUS
                                        or (common and ws[i] in common))):
                found.add(hit)
    return found


def suggestions(index, evidence):
    out = [{"element_id": e, "name": index.skills[e][0], "evidence": ev[0], "lines": len(ev)}
           for e, ev in evidence.items()]
    return sorted(out, key=lambda x: (-x["lines"], x["name"]))


def goal_score(index, evidence, software, tools, soc):
    """The measured score (benchmark model M6): concrete evidence the job uses,
    plus a smaller weight on its most important skills showing in the text."""
    need = index.occ_software.get(soc, set()) | index.occ_tools.get(soc, set())
    have = (software | tools) & need
    overlap = len(have) / math.sqrt(len(need) + 1)
    imp = index.importance.get(soc, {})
    top = sorted(imp, key=lambda e: -imp[e])[:TOP_SKILLS]
    total = sum(imp[e] for e in top) or 1.0
    coverage = sum(imp[e] for e in top if e in evidence) / total
    return {"value": round(overlap + COVERAGE_WEIGHT * coverage, 4),
            "overlap": round(overlap, 4), "coverage": round(coverage, 4),
            "named": sorted(have), "top_skills": top}


SECTIONS = [
    ("objective", "A line about what you want to do", r"\b(objective|profile|summary|about me|career goal)\b"),
    ("education", "Your education (school, matric, college)", r"\b(matric|grade 12|school|college|tvet|university|diploma|degree|certificate|n\d)\b"),
    ("experience", "Experience (jobs, piece work, volunteering)", r"\b(experience|worked|work at|volunteer|employ|internship|job|piece work|helped)\b"),
    ("skills", "A list of your skills", r"\bskills?\b"),
    ("contact", "How to reach you (phone or email)", r"(@|\b0\d{2}[ -]?\d{3}[ -]?\d{4}\b|\+27)"),
]


def checks(text):
    t = (text or "").lower()
    return [{"key": k, "label": label, "present": bool(re.search(rx, t))} for k, label, rx in SECTIONS]
