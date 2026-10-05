"""What employers ask for -- module 4 of the proposal, as the data allows (ADR-0017).

The proposal's "opportunity matching" needs live adverts a user can apply to.
The only Kaggle source that passed step 0 (docs/plans/next-three.md §3) is
LinkedIn's US adverts from March-April 2024 -- all long expired. So this
module summarises them instead: per O*NET occupation, how many adverts there
were, how many took beginners, what they asked for, and which tools and
skills they named. Every screen that shows it says US, 2024.

Pure functions only; backend/load_adverts.py does the reading and writing.
Nothing here keeps advert text -- only counts and normalised titles.
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
ENTRY_LEVELS = {"Entry level", "Internship"}

# Requirements, as US adverts word them. Our rules; precision hand-checked
# in docs/test-results/adverts-2026-10-05.txt. The label is what the screen says.
REQUIREMENTS = [
    ("school", "A high-school diploma (about the same as matric)",
     r"\b(high[- ]school (diploma|education|graduate|degree)|hs diploma|ged)\b"),
    ("degree", "A college diploma or degree",
     r"\b(bachelor'?s?|associate'?s? degree|college degree|university degree|4[- ]year degree|"
     r"degree in|master'?s degree|bsn)\b"),
    # "certified as a Great Place to Work" is employer boilerplate, not a requirement.
    ("licence", "A licence or certificate for the trade",
     r"\b(certified(?! as a great place)|certification|licensure|journeyman|(state|professional|valid) (licen[cs]e|certificate)|"
     r"licensed (as|in|to)|(cna|lpn|epa|osha|cdl|cpr|bls) (certif\w*|licen[cs]e|card))\b"),
    ("driver", "A driver's licence",
     r"\b(driver'?s'? licen[cs]e|driving licen[cs]e|valid licen[cs]e to drive|class [ab] cdl|cdl[- ]?(a|b|licen[cs]e|driver))\b"),
    ("train", "No experience needed, or training given",
     r"\b(no (prior |previous |work )?experience (is )?(necessary|required|needed)|will train|"
     r"we('ll| will) train|paid training|training (is )?provided|on[- ]the[- ]job training)\b"),
    ("lifting", "Physical work (lifting)",
     r"\blift(ing)? (up to |at least |a minimum of )?\d{2,3}\s*(lbs?|pounds)\b"),
]
# Rules are written in lower case and run on lower-cased text: Python's
# re.I is markedly slower on long adverts and gives the same matches.
_REQ = [(k, label, re.compile(rx)) for k, label, rx in REQUIREMENTS]
REQUIREMENT_LABELS = {k: label for k, label, _ in REQUIREMENTS}

# "3+ years of experience", "2-4 years' experience", "minimum of 5 years
# relevant experience". The first number is the floor asked for. No \b
# before it: adverts run words together ("preferred1-3 years").
_YEARS = re.compile(r"(?<!\d)(\d{1,2})\+?\s*(?:(?:-|–|to)\s*\d{1,2}\+?\s*)?(?:years?|yrs?)\.?'?\s+(?:of\s+)?"
                    r"(?:[a-z]+\s+){0,3}?experience\b", re.I)


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
    """{word tuple: O*NET example} for one occupation's own software and tools."""
    table = {}
    for example in software:
        ws = tuple(_words(example))
        if ws:
            table.setdefault(ws, example)
            if len(ws) > 1 and ws[0] in VENDORS:
                table.setdefault(ws[1:], example)
    for example in tools:
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
    found = set()
    for n in (4, 3, 2, 1):
        for i in range(len(ws) - n + 1):
            hit = table.get(tuple(ws[i:i + n]))
            if hit and not (n == 1 and (len(ws[i]) < 4 or ws[i] in AMBIGUOUS or ws[i] in common)):
                found.add(hit)
    return found


def requirements(text):
    """The requirement keys an advert's text asks for."""
    low = (text or "").lower()
    return {k for k, _, rx in _REQ if rx.search(low)}


def years_asked(text):
    """The smallest number of years' experience the advert asks for, or None.
    Anything over 15 is taken to be about the company, not the applicant."""
    found = [int(m.group(1)) for m in _YEARS.finditer(text or "")]
    found = [y for y in found if y <= 15]
    return min(found) if found else None


def is_entry(level):
    return (level or "") in ENTRY_LEVELS


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
