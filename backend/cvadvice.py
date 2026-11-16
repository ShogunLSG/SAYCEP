"""CV advice: what to add, with the evidence for it (ADR-0024).

The CV check already says what a CV shows. This says what it doesn't, for the
goal job, and how common each thing is in real adverts for that job (US,
spring 2024, the advert counts of ADR-0017). Three kinds of advice:

  requirement  something adverts for this job commonly ask for (a licence, a
               matric result) that the CV text doesn't mention
  tool         software or a tool those adverts name that the CV doesn't
  skill        a key skill of the job (O*NET) the CV doesn't show yet

Pure functions: app.py supplies the advert summary and the CV's own findings.
Nothing here touches the scanner or the goal score, so the measured r = 0.27
(ADR-0014) is unchanged, and it makes no accuracy claim of its own: it is
advice, and every line says where it comes from.
"""

import re

import adverts

MAX_PER_KIND = 3
MIN_REQUIREMENT_SHARE = 0.25     # a requirement most adverts don't mention isn't advice
MIN_TOOL_SHARE = 0.15            # "a few adverts name it" isn't advice either

# What a CV says where an advert says it: South African wording ("matric",
# "Code 8"), not the US wording the advert rules look for.
REQUIREMENTS = {
    "school": (
        r"\b(matric|grade 12|national senior certificate|nsc|high school|ged)\b",
        "your school results",
        "Give your highest school result, for example: “National Senior Certificate (Matric), 2025, with Mathematics.”"),
    "degree": (
        r"\b(degree|diploma|tvet|college|university|n[1-6]|national certificate|studying|student|bachelor)\b",
        "your studies or qualification",
        "If you are studying or have a qualification, name it and the year, for example: “Studying N2 Electrical at a TVET college, 2026.”"),
    "licence": (
        r"\b(licen[cs]e|certificate|certified|certification|trade test|apprentic\w*|journeyman|red seal)\b",
        "a trade licence or certificate",
        "If you hold a trade certificate or licence, name it and the year. If you are working towards one, say that."),
    "driver": (
        r"\b(driver'?s? licen[cs]e|driving licen[cs]e|licen[cs]e to drive|code (8|10|14)|drive)\b",
        "a driver's licence",
        "If you have a driver's licence, give the code, for example: “Code 8 driver's licence.”"),
    "lifting": (
        r"\b(lift\w*|physical|manual (work|labour)|heavy)\b",
        "physical work",
        "If you have done physical work, say so, for example: “Loaded and unloaded stock at a hardware store.”"),
}

# A worked line for the skills a CV most often lacks. Others get a frame.
SKILL_EXAMPLES = {
    "Repairing": "I fixed my neighbour's broken gate hinge and it has worked since.",
    "Troubleshooting": "When the lights at home stopped working, I tested each plug point and found the loose wire.",
    "Installation": "I helped my uncle fit new plug points in two houses.",
    "Equipment Maintenance": "I clean and check the school's lawnmowers every Friday so they keep running.",
    "Operation and Control": "I operated the till and the stock scanner at the shop every weekend.",
    "Operations Monitoring": "I watched the gauges on the generator and told the caretaker when a reading was off.",
    "Quality Control Analysis": "I checked each delivery against the invoice and reported damaged items.",
    "Service Orientation": "I helped customers find what they needed and handled their complaints calmly.",
    "Active Listening": "I listened to each customer's problem before suggesting a solution.",
    "Critical Thinking": "I compared three suppliers' prices and chose the one with the best delivery time.",
    "Monitoring": "I kept a weekly record of stock levels and flagged what was running low.",
    "Speaking": "I explained the safety rules to new members of the team.",
    "Mathematics": "I counted the till at the end of each day and balanced it to the cent.",
    "Instructing": "I showed two new staff members how the till system works.",
    "Coordination": "I worked with three classmates to finish the project on time.",
}


def example_for(skill_name):
    if skill_name in SKILL_EXAMPLES:
        return f"For example: “{SKILL_EXAMPLES[skill_name]}”"
    return (f"Add one line about a time you used {skill_name.lower()}: what you did and what happened. "
            "School, home, church, sport or work all count.")


def _mentions(text, key):
    """Does the CV already say this? Our South African cues, or the advert rule itself."""
    cue = REQUIREMENTS[key][0]
    return bool(re.search(cue, text or "", re.I)) or key in adverts.requirements(text or "")


def advice(summary, cv_text, tools_named, missing_skills):
    """What to add, as a list of {kind, title, why, example}.

    summary: adverts.summarise(...) plus 'adverts' (the count) and 'period', or
    None when this job has too few adverts to say anything. tools_named: the
    software and tools the CV names. missing_skills: names of the job's key
    skills the CV doesn't show. Without a summary, only skill advice is given
    and no advert figure is claimed."""
    out = []
    if summary:
        n, when = summary["adverts"], summary["period"]
        basis = f"of the {n} US adverts for this job ({when})"
        reqs = [r for r in summary["requirements"]
                if r["key"] in REQUIREMENTS and r["share"] >= MIN_REQUIREMENT_SHARE]
        shown = 0
        for r in sorted(reqs, key=lambda r: -r["share"]):
            if shown == MAX_PER_KIND:
                break
            if _mentions(cv_text, r["key"]):
                continue
            _, title, example = REQUIREMENTS[r["key"]]
            out.append({"kind": "requirement", "title": title.capitalize(),
                        "why": f"{r['words'].capitalize()} {basis} mention {title}. Your CV doesn't.",
                        "example": example})
            shown += 1
        have = {t.lower() for t in tools_named}
        shown = 0
        for t in summary["tools"]:
            if shown == MAX_PER_KIND:
                break
            if t["share"] < MIN_TOOL_SHARE or t["name"].lower() in have:
                continue
            out.append({"kind": "tool", "title": t["name"],
                        "why": f"{t['words'].capitalize()} {basis} name {t['name']}. Your CV doesn't.",
                        "example": f"If you have used it, say what for: “I used {t['name']} to …”"})
            shown += 1
    for name in missing_skills[:MAX_PER_KIND]:
        out.append({"kind": "skill", "title": name,
                    "why": "O*NET rates this as essential for the job, and your CV doesn't show it yet.",
                    "example": example_for(name)})
    return out
