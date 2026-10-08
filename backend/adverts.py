"""What employers ask for -- module 4 of the proposal, as the data allows (ADR-0017).

The proposal's "opportunity matching" needs live adverts a user can apply to.
The only Kaggle source that passed step 0 (docs/plans/next-three.md §3) is
LinkedIn's US adverts from spring 2024 -- all long expired (the ones linked
to O*NET were listed 5-20 April). So this module summarises them instead: per
O*NET occupation, how many adverts there were, how many took beginners, what
they asked for, and which tools and skills they named. Every screen that shows
it says US, and the month, from the data.

Pure functions only; backend/load_adverts.py does the reading and writing,
app.py only routes. Nothing here keeps advert text -- only counts and titles.

The software/tool matcher here is deliberately separate from cvscan.named:
the CV scanner's is tied to a measured benchmark figure (ADR-0014), so it
changes only with a re-measure. See BACKLOG.md.
"""

import re

from cvscan import AMBIGUOUS, _words

# Advert titles that name a level or a department, not a job. Each matched an
# O*NET alternate title and went wrong at volume in step 0 ("director" ->
# Producers and Directors, "project manager" -> Construction Managers,
# "sales associate" -> Online Merchants).
GENERIC = {
    "director", "manager", "associate", "supervisor", "assistant manager", "project manager",
    "sales associate", "account executive", "account manager", "team member", "intern",
    "consultant", "specialist", "coordinator", "analyst", "engineer", "technician", "vp",
    "vice president", "associate director", "operations manager", "program manager",
}

MIN_ADVERTS = 5          # fewer than this and the screen says there aren't enough
MIN_STATED = 5           # fewer adverts than this stating years or a level: say nothing
ENTRY_LEVELS = {"Entry level", "Internship"}

# What the screen shows (and backend/tests/check_adverts.py validates).
SKILL_MIN_SHARE, SKILL_MIN_LIFT = 0.25, 1.5     # "noticeably more than adverts in general"
OTHER_MIN_SHARE = 0.05                          # below this a requirement or tool is noise

# Requirements, as US adverts word them. Our rules; precision hand-checked
# in docs/test-results/adverts-2026-10-05.txt. The label is what the screen says.
REQUIREMENTS = [
    ("school", "A high-school diploma (about the same as matric)",
     r"\b(high[- ]school (diploma|education|graduate|degree)|hs diploma|ged)\b"),
    ("degree", "A college diploma or degree",
     r"\b(bachelor'?s?|associate'?s? degree|college degree|university degree|4[- ]year degree|"
     r"degree in|master'?s degree|bsn)\b"),
    # Employer boilerplate is not a requirement: "certified as a Great Place to
    # Work", "Great Place to Work-Certified", "a certified B Corp", "certified
    # minority-owned business". A driving licence is the next rule, not this one.
    ("licence", "A licence or certificate for the trade",
     r"\b((?<!work[- ])certified(?! as a great place| b ?corp| (minority|woman|women|veteran|disabled|small|"
     r"disadvantaged|diverse)[\w-]*)|certification|licensure|journeyman|(state|professional) (licen[cs]e|certificate)|"
     r"licensed (as|in|to)(?! drive)|(cna|lpn|epa|osha|cpr|bls) (certif\w*|licen[cs]e|card))\b"),
    ("driver", "A driver's licence",
     r"\b(driver'?s'? licen[cs]e|driving licen[cs]e|valid licen[cs]e to drive|class [ab] cdl|cdl[- ]?(a|b|licen[cs]e|driver))\b"),
    ("train", "No experience needed, or training given",
     r"\b(no (prior |previous |work )?experience (is )?(necessary|required|needed)|will train|"
     r"we('ll| will) train|paid training|training (is )?provided|on[- ]the[- ]job training)\b"),
    ("lifting", "Physical work (lifting)",
     r"\blift(ing)? (up to |at least |a minimum of )?\d{2,3}\s*(lbs?|pounds)\b"),
]
# Rules are written in lower case with straight quotes, and run on clean(text):
# Python's re.I is markedly slower on long adverts, and about half of adverts
# write "driver’s license" with a curly apostrophe.
_REQ = [(k, label, re.compile(rx)) for k, label, rx in REQUIREMENTS]
REQUIREMENT_LABELS = {k: label for k, label, _ in REQUIREMENTS}
_QUOTES = str.maketrans({"’": "'", "‘": "'", "`": "'", "´": "'", "“": '"', "”": '"'})


def clean(text):
    """Advert text as every rule here expects it: lower case, straight quotes."""
    return (text or "").translate(_QUOTES).lower()


# "3+ years of experience", "2-4 years' experience", "1.5 years experience",
# "minimum of 5 years relevant experience". The first number is the floor
# asked for. No \b before it: adverts run words together ("preferred1-3
# years", "related field.5-8 years"); but never straight after a digit, or a
# digit and a point, so "1.5" is never read as 5.
_YEARS = re.compile(r"(?<!\d)(?<!\d\.)(\d{1,2}(?:\.\d+)?)\+?\s*(?:(?:-|–|to)\s*\d{1,2}(?:\.\d+)?\+?\s*)?"
                    r"(?:years?|yrs?)\.?'?\s+(?:of\s+)?(?:[a-z]+\s+){0,3}?experience\b")


def norm(title):
    """An advert title reduced to the job it names: lower case, without
    seniority, shift, location or a department after a dash."""
    t = (title or "").lower()
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    t = re.split(r"\s[-–|/,]\s|\s-\s|,", t)[0]
    t = re.sub(r"\b(sr|senior|jr|junior|lead|i{1,3}|iv|level \d|entry level|part[- ]time|full[- ]time|"
               r"remote|hybrid)\b\.?", " ", t)
    t = re.sub(r"[^a-z ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def build_lookup(con):
    """{normalised title: {soc_code, ...}} from O*NET titles and alternate titles."""
    lookup = {}
    for soc, t in con.execute("SELECT soc_code, title FROM occupations"):
        lookup.setdefault(norm(t), set()).add(soc)
    for soc, t, s in con.execute("SELECT soc_code, title, short_title FROM occupation_alt_titles"):
        for x in (t, s):
            if x:
                lookup.setdefault(norm(x), set()).add(soc)
    lookup.pop("", None)
    return lookup


def link(title, lookup):
    """The one O*NET occupation an advert title names, or None.
    Strict on purpose (step 0): a generic title or one that matches several
    occupations is dropped rather than guessed."""
    k = norm(title)
    if not k or k in GENERIC:
        return None
    socs = lookup.get(k)
    return next(iter(socs)) if socs and len(socs) == 1 else None


# Software is often written without its vendor ("Excel" for "Microsoft
# Excel"), but only these vendors are safe to drop: "Timpani Chat" written as
# "chat" is just a word in an advert.
VENDORS = {"microsoft", "adobe", "google", "sap", "oracle", "ibm", "intuit", "autodesk", "apple",
           "salesforce", "atlassian", "amazon", "cisco"}


def aliases(software, tools):
    """{word tuple: O*NET example} for one occupation's own software and tools.
    Sorted, so when two examples share a key the same one always wins."""
    table = {}
    for example in sorted(software):
        ws = tuple(_words(example))
        if ws:
            table.setdefault(ws, example)
            if len(ws) > 1 and ws[0] in VENDORS:
                table.setdefault(ws[1:], example)
    for example in sorted(tools):
        ws = tuple(_words(example))
        if ws:
            table.setdefault(ws, example)
    return table


def named_in(table, text, common=frozenset()):
    """Which of one occupation's software and tools an advert names.
    A one-word name must be 4+ letters, not an everyday word in O*NET's task
    statements, and not on the scanner's ambiguous list: plural folding turns
    "Canes" into "can", which every advert contains."""
    ws = _words(text)
    longest = max((len(k) for k in table), default=0)
    found, i = set(), 0
    # Longest match first, and a match uses up its words: "Microsoft Visual
    # Basic for Applications" names one product, not also "Microsoft Visual Basic".
    while i < len(ws):
        for n in range(min(longest, len(ws) - i), 0, -1):
            hit = table.get(tuple(ws[i:i + n]))
            if hit and not (n == 1 and (len(ws[i]) < 4 or ws[i] in AMBIGUOUS or ws[i] in common)):
                found.add(hit)
                i += n
                break
        else:
            i += 1
    return found


def requirements(text):
    """The requirement keys an advert's text asks for."""
    low = clean(text)
    return {k for k, _, rx in _REQ if rx.search(low)}


def years_asked(text):
    """The smallest number of years' experience the advert asks for, or None.
    Anything over 15 is taken to be about the company, not the applicant."""
    found = [float(m.group(1)) for m in _YEARS.finditer(clean(text))]
    found = [y for y in found if y <= 15]
    return min(found) if found else None


def is_entry(level):
    return (level or "") in ENTRY_LEVELS


def display_title(key, raw_titles):
    """A normalised title for the screen, with acronyms kept: "IT Project
    Manager", not "It Project Manager". A word is upper case where most of
    the adverts that write it in mixed case write it in capitals."""
    mixed = [(t, n) for t, n in raw_titles.items() if t != t.upper()]
    out = []
    for w in key.split():
        up = sum(n for t, n in mixed if re.search(rf"\b{w.upper()}\b", t))
        seen = sum(n for t, n in mixed if re.search(rf"\b{w}\b", t, re.I))
        out.append(w.upper() if seen and up * 2 > seen else w.capitalize())
    return " ".join(out)


def period(first, last):
    """'April 2024' or 'March–April 2024' from two ISO dates."""
    import datetime
    a, b = (datetime.date.fromisoformat(x) for x in (first, last))
    if (a.year, a.month) == (b.year, b.month):
        return f"{b:%B %Y}"
    return f"{a:%B}–{b:%B %Y}" if a.year == b.year else f"{a:%B %Y}–{b:%B %Y}"


def share_words(n, total):
    """A share in words a school-leaver reads at a glance."""
    if not total:
        return None
    p = n / total
    if p >= 0.95:
        return "almost all"
    if p >= 0.15:
        return f"{int(p * 10 + 0.5)} in 10"
    if n:
        return "a few"
    return "none"


def summarise(row, counts, base, total, names, held):
    """The screen's view of one occupation's adverts.
    row: its advert_summary row; counts: [(kind, item, n)]; base/total: the
    all-advert baseline; names: {element_id: name}; held: {element_id: status}.
    Keys the current rules don't know (a database built by older code) are
    skipped, not fatal."""
    n = row["adverts"]
    words = lambda k, of=n: share_words(k, of)
    reqs, tools, skills = [], [], []
    for kind, item, k in counts:
        share = k / n
        if kind == "req" and share >= OTHER_MIN_SHARE and item in REQUIREMENT_LABELS:
            reqs.append({"key": item, "label": REQUIREMENT_LABELS[item], "n": k,
                         "share": round(share, 3), "words": words(k)})
        elif kind in ("tool", "software") and share >= OTHER_MIN_SHARE:
            tools.append({"name": item, "kind": kind, "n": k, "share": round(share, 3), "words": words(k)})
        elif kind == "skill" and base.get(("skill", item)) and item in names:
            lift = share / (base[("skill", item)] / total)
            if share >= SKILL_MIN_SHARE and lift >= SKILL_MIN_LIFT:
                skills.append({"element_id": item, "name": names[item], "n": k, "share": round(share, 3),
                               "lift": round(lift, 2), "words": words(k), "status": held.get(item)})
    skills.sort(key=lambda x: -x["lift"])
    level_n = row["level_n"]
    return {
        # Beginners: a share of the adverts that state a level, not of all of them.
        "levels_stated": level_n, "entry_level": row["entry_level"],
        "entry_words": words(row["entry_level"], level_n) if level_n >= MIN_STATED else None,
        "years": ({"stated": row["years_n"], "median": row["years_median"]}
                  if row["years_n"] >= MIN_STATED else None),
        "requirements": reqs, "tools": tools[:6], "skills": skills[:5],
    }
