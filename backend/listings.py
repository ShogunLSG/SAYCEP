"""Jobs for you -- module 4 as job cards (ADR-0022, docs/plans/advert-matching.md).

One advert at a time: real LinkedIn adverts (US, spring 2024, all closed),
shown as SAMPLE listings with how well the user fits each. Every screen that
shows them says so; nothing here is offered as an opening to apply to.

Pure functions only; backend/load_listings.py reads and writes, app.py routes.
Kept apart from adverts.py on purpose: adverts.py is part of the committed
advert-count cache's fingerprint (ADR-0019), so changing it would invalidate
those counts.
"""

import re

import adverts

LISTINGS_PER_JOB = 20    # the most recent linked adverts kept per occupation


def listing_title(raw):
    """An advert's own title, tidied for a card: single spaces, at most 90 characters."""
    t = re.sub(r"\s+", " ", raw or "").strip()
    return t if len(t) <= 90 else t[:89].rstrip() + "…"


def beginner_ok(level, reqs, years):
    """Open to someone starting out: an entry-level or internship advert, one
    that says training is given, or one asking a year's experience or less."""
    return adverts.is_entry(level) or "train" in reqs or (years is not None and years <= 1)


def fit(mentioned, statuses):
    """How a profile fits one advert, from the O*NET skills the advert mentions.
    statuses: {element_id: "held" | "learning"}. Returns counts and a plain
    word -- never a percentage, which would suggest a precision the matching
    doesn't have (there is no ground truth: nobody was hired)."""
    have = [e for e in mentioned if statuses.get(e) == "held"]
    learning = [e for e in mentioned if statuses.get(e) == "learning"]
    n = len(mentioned)
    if not n:
        band, word = 0, "No skills named"
    elif len(have) * 4 >= n * 3:
        band, word = 3, "Strong fit"
    elif len(have) * 2 >= n:
        band, word = 2, "Good fit"
    elif have:
        band, word = 1, "Some fit"
    else:
        band, word = 0, "A stretch"
    return {"have": len(have), "learning": len(learning), "mentioned": n, "band": band, "words": word}


def share(f):
    """The share of an advert's named skills the user holds (0 when it names none)."""
    return f["have"] / f["mentioned"] if f["mentioned"] else 0.0


def rank(items):
    """Best fit first (the share of the advert's named skills the user holds);
    then open to beginners; then fewer years asked; then the most recent.
    items: dicts with fit, beginner, years, listed, advert_id."""
    newest = sorted(items, key=lambda x: (x["listed"], x["advert_id"]), reverse=True)
    return sorted(newest, key=lambda x: (      # stable: ties stay newest first
        -share(x["fit"]), not x["beginner"], x["years"] if x["years"] is not None else 0))
