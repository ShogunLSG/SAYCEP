"""Interview practice -- proposal module 5, without an LLM (ADR-0015).

The proposal names an "interview chatbot". CLAUDE.md rules out a language
model, so this is practice with rule-based feedback, not a conversation:

  * Questions come from the goal job: an opener, one question per key skill
    (from SKILL_QUESTIONS, our wording, written for someone with little work
    history -- school, home, church, sport and piece work all count), and one
    question built from the job's most important O*NET task.
  * Feedback on a typed answer is a checklist: does it show the skill asked
    about (the CV scanner's rules), does it follow situation -> action ->
    result, does the speaker say "I", is there a specific detail, is the
    length workable.

No accuracy is claimed -- there is no ground truth for answer quality -- so
every rule here is unit-tested and the screen calls it guidance. Answers are
never stored.
"""

import re

import cvscan

# One behavioural question per O*NET skill. Our wording; plain on purpose.
SKILL_QUESTIONS = {
    "Active Listening": "Tell me about a time you had to listen carefully to understand what someone needed.",
    "Mathematics": "Tell me about a time you used numbers or measurements to get something right.",
    "Reading Comprehension": "Tell me about a time you had to follow written instructions, a manual or a plan.",
    "Science": "Tell me about something you investigated or tested to find out how it works.",
    "Speaking": "Tell me about a time you explained something to a group of people.",
    "Writing": "Tell me about something you wrote that other people had to rely on.",
    "Active Learning": "Tell me about a time you had to learn something new quickly.",
    "Critical Thinking": "Tell me about a time you had to weigh up options before deciding what to do.",
    "Learning Strategies": "Tell me how you go about learning a new skill. Give an example.",
    "Monitoring": "Tell me about a time you kept track of how something was going and changed course.",
    "Complex Problem Solving": "Tell me about a difficult problem you solved. What did you do?",
    "Coordination": "Tell me about a time you worked with others to get a job done.",
    "Instructing": "Tell me about a time you taught or showed someone how to do something.",
    "Negotiation": "Tell me about a time you helped two people reach an agreement.",
    "Persuasion": "Tell me about a time you convinced someone to change their mind or try something.",
    "Service Orientation": "Tell me about a time you went out of your way to help a customer or someone in need.",
    "Social Perceptiveness": "Tell me about a time you noticed someone was struggling. What did you do?",
    "Equipment Maintenance": "Tell me about a time you looked after a machine, tool or vehicle so it kept working.",
    "Equipment Selection": "Tell me about a time you had to choose the right tool or equipment for a job.",
    "Installation": "Tell me about something you installed, fitted or set up.",
    "Operation and Control": "Tell me about a machine, vehicle or piece of equipment you have operated.",
    "Operations Analysis": "Tell me about a time you worked out what people needed before making something.",
    "Operations Monitoring": "Tell me about a time you watched gauges, readings or a process to make sure it ran right.",
    "Programming": "Tell me about something you programmed or coded. What did it do?",
    "Quality Control Analysis": "Tell me about a time you checked work for mistakes before it was finished.",
    "Repairing": "Tell me about a time you fixed something that was broken.",
    "Technology Design": "Tell me about something you designed or built to solve a problem.",
    "Troubleshooting": "Tell me about a time something stopped working and you worked out why.",
    "Judgment and Decision Making": "Tell me about a hard decision you made. How did you decide?",
    "Systems Analysis": "Tell me about a time you worked out how a system or process fits together.",
    "Systems Evaluation": "Tell me about a time you judged whether something was working well and how to improve it.",
    "Management of Financial Resources": "Tell me about a time you were responsible for money or a budget.",
    "Management of Material Resources": "Tell me about a time you looked after stock, supplies or equipment for others.",
    "Management of Personnel Resources": "Tell me about a time you led or organised other people.",
    "Time Management": "Tell me about a time you had to get several things done before a deadline.",
}

MIN_WORDS, MAX_WORDS = 40, 250

# How people *tell* a skill in an interview, beyond the CV scanner's rules
# (which stay as measured, ADR-0014). Our wording; only where spoken answers
# differ from CV wording.
ANSWER_RULES = {
    "Troubleshooting": r"\b(worked out why|figured out (why|what)|found (the |a )?(\w+ )?(problem|cause|fault|wire|leak)|"
                       r"(stopped|wasn't|was not|not) working|tested (it|each|the))\b",
    "Repairing": r"\b(tightened|replaced|patched|glued|sorted (it|out))\b",
    "Coordination": r"\b(worked together|together we|with (my|the) (team|group|friends|classmates))\b",
    "Instructing": r"\b(showed (him|her|them|my|a|the)|explained (how|to))\b",
    "Service Orientation": r"\b(helped (a|an|the|my|our|people|someone)|went out of my way)\b",
    "Time Management": r"\b(on time|before the deadline|planned my (day|time|week))\b",
    "Quality Control Analysis": r"\b(checked (it|my|the|each|for)|double[- ]checked)\b",
    "Operation and Control": r"\b(used (a|the) (machine|forklift|tractor|till|drill|mower))\b",
}
_ANSWER_RX = {k: re.compile(v, re.I) for k, v in ANSWER_RULES.items()}

# Cues for the three parts of a STAR answer. Our wording, deliberately broad:
# a school-leaver's answer is about church, sport or a neighbour as often as a job.
SITUATION = re.compile(r"\b(when|while|during|last (year|month|week|term)|at (my|a|the|our|school|church|work)|"
                       r"in (grade|matric|my|our|the)|one (day|time)|there was|we had)\b", re.I)
# "I" + a past-tense action. "-ed" alone would accept "I need", so a few
# present-tense look-alikes are excluded; irregular past forms are listed.
ACTION = re.compile(r"\bI\s+(also\s+|then\s+|quickly\s+)?((?!need\b|feed\b|bleed\b|speed\b|proceed\b)\w+ed|"
                    r"made|took|went|did|told|showed|taught|chose|built|kept|spent|sent|brought|bought|"
                    r"spoke|wrote|ran|led|found|got|put|set|began|gave|held|met|paid|sold|drove|knew|"
                    r"understood|thought|caught|dealt|felt|left|won|became|came|saw|said)\b")
RESULT = re.compile(r"\b(so that|as a result|in the end|afterwards|which meant|because of (this|that)|"
                    r"result|finally|it worked|we (won|finished|passed)|saved|improved|on time|"
                    r"thanked|learned|learnt)\b", re.I)
SPECIFIC = re.compile(r"(\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|hundred|"
                      r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|"
                      r"april|may|june|july|august|september|october|november|december)\b)", re.I)


def tool_for(con, soc_code, min_share=0.05, min_adverts=5):
    """The one tool or piece of software to ask about for this job: the one the
    most real adverts name, if at least min_adverts adverts and min_share of
    them do. Otherwise none, and the practice set has no technical question:
    no evidence beats a generic or silly one (O*NET's "hot technology" list
    offered Git for coroners and Apache Spark for nurses)."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name = 'advert_summary'").fetchone():
        return None
    row = con.execute("SELECT adverts FROM advert_summary WHERE soc_code = ?", (soc_code,)).fetchone()
    if not row or row[0] < min_adverts:
        return None
    hit = con.execute("SELECT item FROM advert_counts WHERE soc_code = ? AND kind IN ('tool','software')"
                      " AND n >= ? AND n >= ? ORDER BY n DESC, item LIMIT 1",
                      (soc_code, min_adverts, min_share * row[0])).fetchone()
    return hit[0] if hit else None


def names_tool(answer, tool):
    """Does the answer name this tool? Word by word, plural-folded like the CV
    scanner, so 'multimeter' names Multimeters; a vendor alone doesn't count."""
    want = cvscan._words(tool)
    ws = cvscan._words(answer or "")
    n = len(want)
    return bool(n) and any(ws[i:i + n] == want for i in range(len(ws) - n + 1))


def questions(con, soc_code, index):
    """The practice set for one job, in order: opener, skills, a tool, a task."""
    occ = con.execute("SELECT title FROM occupations WHERE soc_code = ?", (soc_code,)).fetchone()
    imp = index.importance.get(soc_code, {})
    names = {e: index.skills[e][0] for e in imp}
    essential = [e for e in sorted(imp, key=lambda e: -imp[e]) if imp[e] >= 3.5][:4]
    keys = essential or sorted(imp, key=lambda e: -imp[e])[:3]
    out = [{"id": "why", "kind": "opener", "skill": None,
            "text": f"Why do you want this job ({occ[0]})? What draws you to it?"}]
    out += [{"id": f"skill:{e}", "kind": "skill", "skill": {"element_id": e, "name": names[e]},
             "text": SKILL_QUESTIONS[names[e]]} for e in keys]
    tool = tool_for(con, soc_code)
    if tool:
        out.append({"id": "tool", "kind": "tool", "skill": None, "tool": tool,
                    "text": f"Tell me about a time you used {tool}, or how you would use it in this job."})
    task = con.execute("SELECT task FROM occupation_tasks WHERE soc_code = ? AND importance IS NOT NULL"
                       " ORDER BY importance DESC LIMIT 1", (soc_code,)).fetchone()
    if task:
        t = task[0].rstrip(".")
        out.append({"id": "task", "kind": "task", "skill": None,
                    "text": f"This job involves this: “{t}.” Have you done anything like it? Tell me about it."})
    return out


def feedback(index, answer, skill_id=None, tool=None):
    """A checklist for one answer. Each item: key, ok, and a tip when not ok."""
    text = (answer or "").strip()
    words = len(re.findall(r"\b\w+\b", text))
    items = []

    def add(key, label, ok, tip):
        items.append({"key": key, "label": label, "ok": bool(ok), "tip": None if ok else tip})

    if skill_id:
        ev = cvscan.skill_evidence(index, text)
        name = index.skills[skill_id][0]
        extra = _ANSWER_RX.get(name)
        add("skill", f"Shows {name}", skill_id in ev or bool(extra and extra.search(text)),
            f"Say plainly what you did that shows {name.lower()} — the action, in everyday words.")
    if tool:
        add("tool", f"Names {tool}", names_tool(text, tool),
            f"Say which tool you used and what for: “I used {tool.lower()} to …”. If you haven't used it, say how you would.")
    add("situation", "Sets the scene (when and where)", SITUATION.search(text),
        "Start with the situation: when it was and where — school, home, church, sport or work all count.")
    add("action", "Says what *you* did", ACTION.search(text),
        "Use “I” and an action: “I checked…”, “I fixed…”, “I showed…”.")
    add("result", "Ends with what happened", RESULT.search(text),
        "Finish with the result: what changed, what you learned, or how it turned out.")
    we, i = len(re.findall(r"\bwe\b", text, re.I)), len(re.findall(r"\bI\b", text))
    add("ownership", "Your part is clear, not only the team's", i >= 1 and i >= we / 2,
        "Interviewers want your part. Swap some “we” for “I” where it was you.")
    add("specific", "Has a specific detail (a number, a day, a place)", SPECIFIC.search(text),
        "Add one concrete detail — how many, how long, which day. It makes the story believable.")
    add("length", f"About the right length ({MIN_WORDS}–{MAX_WORDS} words)", MIN_WORDS <= words <= MAX_WORDS,
        "Too short — add the situation and the result." if words < MIN_WORDS
        else "Too long — keep to the main story; one example is enough.")
    return {"words": words, "items": items, "met": sum(x["ok"] for x in items), "of": len(items)}
