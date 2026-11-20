/* Builds the two Thabo documents for the presentation (20 November 2026):
 *
 *   Thabo_Mokoena_CV.docx   from Thabo_Mokoena_CV.txt, a one-page CV a person
 *                           could upload to the CV check
 *   Thabo_plan.docx         his path and skills to take, built from the real
 *                           SAYCEP output saved in thabo-run-2026-11-20.json
 *
 *   node docs/thabo/build-thabo.js
 *
 * Thabo is a made-up person; both documents say so. The plan reads every
 * figure from the saved output rather than carrying its own copy, so it cannot
 * disagree with what the app produced.
 */

const fs = require("fs");
const path = require("path");

function loadDocx() {
  try { return require("docx"); }
  catch (e) {
    const root = require("child_process").execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "docx"));
  }
}
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, Footer, LevelFormat,
} = loadDocx();

const DIR = __dirname;
const ACCENT = "1D4E6F", INK = "161D25", MUTED = "5B6670", SOFT = "E3EDF3", OK = "E2EFE8", AMBER = "F6E9DC";
const PAGE = { width: 11906, height: 16838 };
const MARGIN = 1134;                      // 2 cm
const WIDTH = PAGE.width - 2 * MARGIN;    // 9638 twips of text

/* ---------- small helpers ---------- */

const ESC = "\u0001";
let BODY = 21;                            // half-points; the plan sets it to 20
function runs(text, base = {}) {
  const out = [];
  for (const part of text.replace(/\\\*/g, ESC).split(/(\*\*[^*]+\*\*)/g)) {
    if (!part) continue;
    const bold = part.startsWith("**") && part.endsWith("**");
    out.push(new TextRun({ text: (bold ? part.slice(2, -2) : part).split(ESC).join("*"),
                           bold: bold || base.bold, size: base.size || BODY, color: base.color || INK,
                           italics: base.italics, characterSpacing: base.spacing }));
  }
  return out;
}
const para = (text, o = {}) => new Paragraph({
  spacing: { before: o.before || 0, after: o.after ?? 100, line: o.line || 264 },
  alignment: o.align, keepNext: o.keepNext, border: o.border, shading: o.shading,
  indent: o.indent, children: runs(text, o) });
const bullet = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 50, line: 260 }, numbering: { reference: "bullets", level: 0 }, children: runs(text, o) });

const bullets = {
  config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] }],
};

const footer = (text) => ({ default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ text, size: 16, color: "808080" })] })] }) });

const page = (children, footerText) => ({
  properties: { page: { size: PAGE, margin: { top: MARGIN, bottom: 1000, left: MARGIN, right: MARGIN } } },
  footers: footer(footerText), children });

/* ---------- 1. the CV ---------- */

function buildCv() {
  const lines = fs.readFileSync(path.join(DIR, "Thabo_Mokoena_CV.txt"), "utf8").replace(/\r/g, "").split("\n");
  const HEADINGS = new Set(["Career objective", "Education", "Experience", "Skills", "Languages"]);
  const out = [];
  let i = 0;
  while (!lines[i].trim()) i++;
  out.push(new Paragraph({ spacing: { after: 40 },
    children: [new TextRun({ text: lines[i++].trim(), bold: true, size: 48, color: ACCENT })] }));
  out.push(new Paragraph({ spacing: { after: 160 },
    children: [new TextRun({ text: lines[i++].trim(), size: 21, color: MUTED })] }));

  let section = "";
  for (; i < lines.length; i++) {
    const t = lines[i].trim();
    if (!t) continue;
    if (HEADINGS.has(t)) {
      section = t;
      out.push(new Paragraph({ spacing: { before: 220, after: 80 }, keepNext: true,
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 2 } },
        // allCaps is formatting only, so the stored text stays "Career objective"
        // and the CV check reads it exactly as in the .txt.
        children: [new TextRun({ text: t, allCaps: true, bold: true, size: 20, color: ACCENT, characterSpacing: 30 })] }));
    } else if (t.startsWith("- ")) {
      out.push(bullet(t.slice(2), { size: 21 }));
    } else if (section === "Experience") {
      out.push(new Paragraph({ spacing: { before: 100, after: 40 }, keepNext: true,
        children: [new TextRun({ text: t, bold: true, size: 21 })] }));
    } else {
      out.push(para(t, { after: 60 }));
    }
  }
  return new Document({ creator: "Thabo Mokoena (fictional)", title: "Thabo Mokoena, CV",
    styles: { default: { document: { run: { font: "Calibri", size: 21 } } } }, numbering: bullets,
    sections: [page(out, "Fictional example CV, written for the SAYCEP demonstration.")] });
}

/* ---------- 2. the plan ---------- */

function table(widths, header, rows, fills = {}) {
  const cell = (text, c, head, fill) => new TableCell({
    width: { size: widths[c], type: WidthType.DXA }, margins: { top: 70, bottom: 70, left: 110, right: 110 },
    shading: head ? { type: ShadingType.CLEAR, fill: SOFT } : (fill ? { type: ShadingType.CLEAR, fill } : undefined),
    children: String(text).split("\n").map((ln) => new Paragraph({ spacing: { after: 0, line: 240 },
      children: runs(ln, { size: 18, bold: head || undefined }) })) });
  return new Table({ width: { size: WIDTH, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, c) => cell(h, c, true)) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true,
        children: r.map((t, c) => cell(t, c, false, fills[`${ri}:${c}`])) }))] });
}
const h2 = (text) => new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true,
  children: [new TextRun({ text, bold: true, size: 26, color: ACCENT })] });
const gap = () => new Paragraph({ spacing: { after: 60 }, children: [] });

function buildPlan() {
  BODY = 20;
  const d = JSON.parse(fs.readFileSync(path.join(DIR, "thabo-run-2026-11-20.json"), "utf8"));
  const g = d.gap, steps = d.pathway.steps, recs = d.for_you.recommendations, cv = d.scan_draft, ad = d.adverts;
  const must = g.missing.filter((m) => m.classification === "essential");
  const nice = g.missing.filter((m) => m.classification !== "essential");
  const evidence = Object.fromEntries(cv.suggestions.map((s) => [s.name, s.evidence]));
  const req = Object.fromEntries(ad.requirements.map((r) => [r.key, r]));
  const prep = g.target.preparation;
  const out = [];

  out.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Thabo’s plan", bold: true, size: 52, color: ACCENT })] }));
  out.push(para("From school-leaver to electrician: one walk-through of SAYCEP", { size: 26, color: MUTED, after: 60 }));
  out.push(para("Thabo Mokoena is a made-up person. Everything below is what SAYCEP produced for him on 20 November 2026.",
    { size: 18, color: MUTED, italics: true, after: 120 }));

  out.push(h2("1. Where Thabo starts"));
  out.push(para("Matric in 2025 (Mathematics and Physical Science), studying N2 Electrical part-time. A weekend job at a hardware store, and weekend wiring work with his uncle."));
  out.push(bullet(`**Skills he ticked (6):** Operation and Control, Operations Monitoring, Equipment Maintenance, Active Listening, Critical Thinking, Monitoring.`));
  out.push(bullet(`**Skills his CV also shows:** ${cv.suggestions.map((s) => s.name).join(", ")}.`));

  out.push(h2("2. Jobs that fit him"));
  out.push(para("Two views, because they tell different stories:", { after: 60 }));
  out.push(table([3500, 1700, 4438], ["From the six skills he ticked", "How well", "Because he has"],
    recs.map((r) => [r.title, r.match, r.because.join(", ")])));
  out.push(gap());
  out.push(table([9638], ["From his CV (the skills it seems to show)"],
    [[cv.points_to.slice(0, 5).map((j) => j.title).join("; ")]]));
  out.push(para("His ticks are all operator skills, so operator jobs lead the first list. His CV is about wiring and repair, so it points at electrical and installer jobs, with Electricians first. His own goal is the electrician’s trade.",
    { before: 100 }));

  out.push(h2("3. The goal: Electricians"));
  out.push(bullet(`**Preparation:** ${prep.label}. ${prep.detail}`));
  out.push(bullet(`**What employers asked for** (${ad.adverts} real adverts from the United States, ${ad.period}; they have closed, so this shows what was asked, not jobs to apply for): ${ad.entry_words} of the ${ad.levels_stated} that stated a level were open to beginners; ${req.licence.words} asked for a licence or certificate for the trade; ${req.driver.words} for a driver’s licence.`));

  out.push(h2("4. What stands between Thabo and the job"));
  out.push(para(`He already has **${g.already_held_count} of the ${g.required_total}** skills Electricians use. **${must.length} must-haves** are still missing:`, { after: 70 }));
  const fills = {};
  out.push(table([2300, 2700, 4638], ["Must-have skill", "How much the job needs it", "His CV today"],
    must.map((m, i) => {
      const ev = evidence[m.name];
      if (ev) fills[`${i}:2`] = OK; else fills[`${i}:2`] = AMBER;
      return [m.name, `${m.level} (${m.importance.toFixed(2)} out of 5)`,
        ev ? `Shown: “${ev}” He can tick it now.` : "Not shown yet. This is the gap to close."];
    }), fills));
  out.push(para(`**The most useful nice-to-haves:** ${nice.slice(0, 5).map((m) => `${m.name} (${m.level.toLowerCase()})`).join("; ")}. They help, but he can start without them.`,
    { before: 100 }));

  out.push(h2("5. The route"));
  out.push(para("Three jobs related to Electricians, then the trade itself. Related jobs need nearly the same skills, so each step is a small move. They are ordered with the job closest to Thabo’s skills now first. The route shows jobs, not courses.", { after: 70 }));
  const rf = {};
  out.push(table([700, 3100, 3438, 2400], ["Step", "Job", "What to build there", "Thabo today"],
    steps.map((s, i) => {
      const build = s.focus.filter((f) => f.badge).slice(0, 4)
        .map((f) => `${f.name} (${f.badge === "new" ? "new" : "needs more depth"})`);
      rf[`${i}:3`] = s.ready ? OK : undefined;
      return [String(s.step), `${s.title}${s.is_target ? "  — the goal" : ""}`,
        build.length ? build.join("\n") : "Nothing new: he already has what it asks.",
        s.ready ? "Ready now. He holds every must-have." : "Not yet ready."];
    }), rf));

  out.push(h2("6. Skills to take, in this order"));
  out.push(para("Must-haves first, then the nice-to-haves that tell jobs apart. The “on the route” column shows which steps ask for the skill.", { after: 70 }));
  const order = [...must, ...nice.slice(0, 2)];
  const onRoute = (name) => steps.filter((s) => s.focus.some((f) => f.name === name)).map((s) => s.step);
  out.push(table([500, 2300, 3000, 1500, 2338], ["#", "Skill", "Why", "On the route", "His CV today"],
    order.map((m, i) => [String(i + 1), m.name, `${m.level}. ${m.description}`,
      onRoute(m.name).length ? `Step ${onRoute(m.name).join(", ")}` : "—",
      evidence[m.name] ? `“${evidence[m.name]}”` : "Not shown yet"])));

  out.push(h2("7. What to add to his CV"));
  for (const a of cv.goal.add) out.push(bullet(`**${a.title}.** ${a.why} ${a.example}`));
  out.push(para("Add only what is true: SAYCEP points at the gap and never writes the CV for him.", { before: 60, italics: true, color: MUTED, size: 19 }));

  out.push(h2("Keep in mind"));
  out.push(bullet("**Data:** O*NET 29.0 (US Department of Labor) and closed US adverts (LinkedIn 2023–2024), both via Kaggle."));
  out.push(bullet("**Not in our data:** South African training routes. This trade is usually entered through an apprenticeship or learnership, college theory and a trade test. Thabo should check with a TVET college or the relevant SETA."));
  out.push(bullet("**The CV check** reads wording, not meaning. It suggests skills and he confirms each one."));

  return new Document({ creator: "SAYCEP", title: "Thabo’s plan",
    styles: { default: { document: { run: { font: "Calibri", size: 21 } } } }, numbering: bullets,
    sections: [page(out, "Thabo is fictional. Built from SAYCEP output of 20 November 2026 (thabo-run-2026-11-20.json).")] });
}

(async () => {
  for (const [name, doc] of [["Thabo_Mokoena_CV.docx", buildCv()], ["Thabo_plan.docx", buildPlan()]]) {
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(path.join(DIR, name), buf);
    console.log(`wrote docs/thabo/${name}  (${(buf.length / 1024).toFixed(0)} KB)`);
  }
})();
