/* Builds the ISJ107V Assignment 3 submission (.docx) from its markdown.
 *
 *   node docs/build-assignment-3.js
 *
 * Unlike build-submission.js (Assignment 2), this reads
 * docs/assignment-3-submission.md directly, so the markdown is the single
 * source of truth and the two cannot drift. Figures are inserted after the
 * paragraph that first introduces them (FIGURES below).
 *
 * Readability: wide diagrams get their own landscape page. Before this, five
 * of eight diagrams printed with text under 6 px.
 *
 * Handles the markdown this document uses: #/## headings, paragraphs, tables,
 * "- " bullets, "1. " numbered lists, **bold**, *italic*, `code`, \* escapes.
 * The leading "> " draft note and "---" rules are not reproduced.
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
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow,
  TableCell, WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, Footer,
  PageNumber, LevelFormat, PageOrientation,
} = loadDocx();

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "docs", "assignment-3-submission.md");
const OUT = path.join(ROOT, "docs", "ISJ107V_Assignment_3_SAYCEP.docx");

const CONTENT_WIDTH = 9026;               // A4 portrait, 1-inch margins, in DXA
const ACCENT = "1F3864";
const HEADER_BG = "D9E2F3";
const BODY = 21;                          // half-points: 10.5 pt
const CELL = 17;                          // half-points: 8.5 pt

// Page geometry. A4 is 11906 x 16838 twips; 1440 twips = 1 inch = 96 px.
const A4 = { width: 11906, height: 16838 };
const PORTRAIT_MARGIN = 1440, LANDSCAPE_MARGIN = 864;
const px = (twips) => Math.floor(twips / 15);
const LAYOUT = {
  normal:    { maxW: 600, maxH: 700 },
  tall:      { maxW: px(A4.width - 2 * PORTRAIT_MARGIN), maxH: 860 },           // own portrait page
  landscape: { maxW: px(A4.height - 2 * LANDSCAPE_MARGIN), maxH: px(A4.width - 2 * LANDSCAPE_MARGIN) - 70 },
  shot:      { maxW: 400, maxH: 330 },
};

// In document order. The image is placed after the first block whose raw
// markdown contains `marker`.
const UML = "docs/uml/a3", SHOT = "docs/screenshots/v2";
const FIGURES = [
  { id: "1",  file: `${UML}/01-architecture.png`,   layout: "landscape", marker: "*Figure 1.*",
    caption: "System architecture, as implemented" },
  { id: "2",  file: `${UML}/02-use-case.png`,       layout: "landscape", marker: "*Figure 2.*",
    caption: "Use-case diagram, updated to the implemented system" },
  { id: "3a", file: `${UML}/03a-class-domain.png`,  layout: "landscape", marker: "*Figures 3a and 3b.*",
    caption: "Class diagram, part A — domain model, as implemented" },
  { id: "3b", file: `${UML}/03b-class-services.png`, layout: "landscape", marker: "*Figures 3a and 3b.*",
    caption: "Class diagram, part B — services, as implemented" },
  { id: "4",  file: `${UML}/04-sequence.png`,       layout: "landscape", marker: "*Figure 4.*",
    caption: "Sequence diagram for UC-08 Generate Career Pathway, as implemented" },
  { id: "5a", file: `${UML}/05-activity.png`,       layout: "tall",      marker: "*Figures 5a and 5b.*",
    caption: "Activity diagram, part A — the five-screen journey, with exceptions and completion states" },
  { id: "5b", file: `${UML}/05b-activity-plan.png`, layout: "normal",    marker: "*Figures 5a and 5b.*",
    caption: "Activity diagram, part B — the My plan dashboard and its progress loop" },
  { id: "6",  file: `${UML}/06-component.png`,      layout: "normal",    marker: "*Figure 6 — components.*",
    caption: "Component diagram" },
  { id: "7",  file: `${UML}/07-deployment.png`,     layout: "landscape", marker: "*Figure 7 — deployment.*",
    caption: "Deployment diagram, demonstration environment" },
  { id: "8",  file: `${UML}/08-erd.png`,            layout: "normal",    marker: "*Figure 8* is the entity",
    caption: "Entity-relationship diagram of saycep.db, read from its schema" },
  { id: "9",  file: `${SHOT}/03a-for-you.jpg`,     layout: "shot",      marker: "*Figure 9 —",
    caption: "Step 3, For you tab — recommendations with a match label and similarity score" },
  { id: "10", file: `${SHOT}/08-api-docs.jpg`,      layout: "shot",      marker: "*Figure 9 —",
    caption: "The API's generated documentation at /docs, listing all eleven endpoints" },
  { id: "11", file: `${SHOT}/01-start.jpg`,         layout: "shot",      marker: "*(Figure 11)*",
    caption: "Step 1 — choosing a starting point" },
  { id: "12", file: `${SHOT}/02-skills.jpg`,        layout: "shot",      marker: "*(Figure 12)*",
    caption: "Step 2 — six skills selected, grouped, the last one explained" },
  { id: "13", file: `${SHOT}/03b-browse.jpg`,       layout: "shot",      marker: "*(Figures 9, 13 and 14)*",
    caption: "Step 3, Browse tab — jobs by how much training they take" },
  { id: "14", file: `${SHOT}/03c-job-panel.jpg`,    layout: "shot",      marker: "*(Figures 9, 13 and 14)*",
    caption: "Step 3 — the occupation panel for Electricians, with A day in this job" },
  { id: "15", file: `${SHOT}/04-gap.jpg`,           layout: "shot",      marker: "*(Figure 15)*",
    caption: "Step 4 — the gap for Electricians: 6 of 34 held, 2 must-haves to learn" },
  { id: "16", file: `${SHOT}/05-route.jpg`,         layout: "shot",      marker: "*(Figure 16)*",
    caption: "Step 5 — the pathway, with New to you and Use it more badges" },
  { id: "17", file: `${SHOT}/06a-plan.jpg`,         layout: "shot",      marker: "*(Figures 17–19)*",
    caption: "My plan — 0 of 2 must-haves, the route with the first step already ticked" },
  { id: "18", file: `${SHOT}/06b-plan-learning.jpg`, layout: "shot",     marker: "*(Figures 17–19)*",
    caption: "My plan — Troubleshooting marked working on it; readiness unchanged" },
  { id: "19", file: `${SHOT}/06c-plan-progress.jpg`, layout: "shot",     marker: "*(Figures 17–19)*",
    caption: "My plan — after I can do this now: 1 of 2, route recalculated" },
];

/* ---------- images ---------- */

function imageSize(buf, type) {
  if (type === "png") return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
  let i = 2;                                  // JPEG: walk to the SOF marker
  while (i < buf.length) {
    if (buf[i] !== 0xff) { i++; continue; }
    const m = buf[i + 1];
    if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc)
      return [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)];
    i += 2 + buf.readUInt16BE(i + 2);
  }
  throw new Error("could not read JPEG size");
}

function figureBlocks(fig) {
  const buf = fs.readFileSync(path.join(ROOT, fig.file));
  const type = fig.file.endsWith(".png") ? "png" : "jpg";
  const [w, h] = imageSize(buf, type);
  const { maxW, maxH } = LAYOUT[fig.layout];
  let width = Math.min(maxW, w), height = Math.round(h * width / w);
  if (height > maxH) { height = maxH; width = Math.round(w * height / h); }

  // PNG only. An SVG-with-PNG-fallback build was tried on 30 September and
  // Word hung exporting it to PDF, where the PNG build exported in seconds.
  // A document the marker's Word might choke on is worse than one that is
  // slightly soft when zoomed; legibility comes from the landscape layout.
  const image = new ImageRun({ type, data: buf, transformation: { width, height } });

  fig.shown = { width, height, scale: width / w };
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true, children: [image] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: `Figure ${fig.id} — ${fig.caption}`, bold: true, size: 17, color: "404040" })] }),
  ];
}

/* ---------- inline markdown ---------- */

const ESC = "\u0001";
function runs(text, base = {}) {
  const out = [];
  const src = text.replace(/\\\*/g, ESC);
  for (const part of src.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g)) {
    if (!part) continue;
    let t = part, opts = { ...base };
    if (part.startsWith("`")) { t = part.slice(1, -1); opts.font = "Consolas"; opts.size = (base.size || BODY) - 2; }
    else if (part.startsWith("**")) { t = part.slice(2, -2); opts.bold = true; }
    else if (part.startsWith("*") && part.length > 2) { t = part.slice(1, -1); opts.italics = true; }
    out.push(new TextRun({ text: t.split(ESC).join("*"), size: opts.size || BODY, ...opts }));
  }
  return out;
}

/* ---------- tables ---------- */

function table(lines) {
  const rows = lines
    .filter((l) => !/^\|\s*:?-{2,}/.test(l))
    .map((l) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
  const cols = rows[0].length;
  const plain = (t) => (t || "").replace(/[*`\\]/g, "");
  const need = Array.from({ length: cols }, (_, c) =>
    Math.max(6, ...rows.map((r) => Math.min(60, plain(r[c]).length))));
  // Every column is at least as wide as its longest word, so a short column
  // such as "FR-01" or "TEXT" never wraps one letter per line. Only the space
  // left over is shared in proportion to content length, as before.
  const CHAR = 125;                                    // ~DXA per character at cell size
  const floor = Array.from({ length: cols }, (_, c) => CHAR * (2 + Math.min(20,
    Math.max(...rows.map((r) => Math.max(0, ...plain(r[c]).split(/\s+/).map((w) => w.length)))))));
  const floorTotal = floor.reduce((a, b) => a + b, 0);
  if (floorTotal > CONTENT_WIDTH) floor.forEach((f, c) => { floor[c] = Math.floor(f * CONTENT_WIDTH / floorTotal); });
  const spare = Math.max(0, CONTENT_WIDTH - floor.reduce((a, b) => a + b, 0));
  const extra = need.map((n, c) => Math.max(0, n * CHAR - floor[c]));
  const extraTotal = extra.reduce((a, b) => a + b, 0) || 1;
  const widths = floor.map((f, c) => Math.floor(f + spare * extra[c] / extraTotal));
  widths[cols - 1] += CONTENT_WIDTH - widths.reduce((a, b) => a + b, 0);
  const cell = (text, c, header) => new TableCell({
    width: { size: widths[c], type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: HEADER_BG } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ spacing: { after: 0, line: 240 },
      children: runs(text || "", { size: CELL, bold: header || undefined }) })],
  });
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true,
      children: Array.from({ length: cols }, (_, c) => cell(r[c], c, i === 0)) })),
  });
}

/* ---------- the document ---------- */

const footer = () => ({ default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: "ISJ107V Assignment 3 — SAYCEP — 219045719 — page ", size: 16, color: "808080" }),
  new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "808080" }),
] })] }) });

const portrait = (children) => ({ children, footers: footer(),
  properties: { page: { size: A4, margin: { top: PORTRAIT_MARGIN, bottom: PORTRAIT_MARGIN, left: PORTRAIT_MARGIN, right: PORTRAIT_MARGIN } } } });
const landscape = (children) => ({ children, footers: footer(),
  properties: { page: { size: { ...A4, orientation: PageOrientation.LANDSCAPE },
    margin: { top: LANDSCAPE_MARGIN, bottom: LANDSCAPE_MARGIN, left: LANDSCAPE_MARGIN, right: LANDSCAPE_MARGIN } } } });

function titlePage() {
  const rows = [
    ["Student name", "Lesego Jan Malema Matsimela"], ["Student number", "219045719"],
    ["Module code", "ISJ107V"], ["Assessment", "Assignment 3 — Individual"],
    ["Weighting / marks", "20% of the final module mark / 50 marks"],
    ["Document version", "1.0, 30 September 2026"], ["Submission", "Through EC"],
  ];
  return [
    new Paragraph({ spacing: { before: 2000 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "ISJ107V — Integrated Software Project", size: 24, color: "595959" })] }),
    new Paragraph({ spacing: { before: 160 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Assignment 3", bold: true, size: 56, color: ACCENT })] }),
    new Paragraph({ spacing: { before: 80, after: 360 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Project Documentation and UML Design", size: 28, color: "404040" })] }),
    new Paragraph({ spacing: { after: 60 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "SAYCEP", bold: true, size: 32 })] }),
    new Paragraph({ spacing: { after: 560 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "South African Youth Career and Employment Platform", italics: true, size: 24, color: "404040" })] }),
    table(["| Field | Detail |", "|---|---|", ...rows.map(([k, v]) => `| ${k} | ${v} |`)]),
  ];
}

function build() {
  const lines = fs.readFileSync(SRC, "utf8").replace(/\r/g, "").split("\n");
  const sections = [];
  let blocks = titlePage();
  let listInstance = 0, inNumbered = false, firstQuestion = true, i = 0;
  const placed = new Set();

  const flush = () => { if (blocks.length) sections.push(portrait(blocks)); blocks = []; };

  const placeFigures = (raw) => {
    for (const fig of FIGURES) {
      if (placed.has(fig.id) || !raw.includes(fig.marker)) continue;
      placed.add(fig.id);
      if (fig.layout === "landscape") { flush(); sections.push(landscape(figureBlocks(fig))); }
      else if (fig.layout === "tall") { blocks.push(new Paragraph({ children: [new PageBreak()] }), ...figureBlocks(fig)); }
      else blocks.push(...figureBlocks(fig));
    }
  };

  // Each Question starts a new page; the title page is its own section.
  const newQuestionPage = () => { if (firstQuestion) { flush(); firstQuestion = false; } else flush(); };

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim() || line.startsWith(">") || /^---\s*$/.test(line)) {
      if (line.trim()) inNumbered = false;
      i++; continue;
    }
    if (line.startsWith("# ")) {
      inNumbered = false;
      if (line.startsWith("# ISJ107V")) { i++; continue; }      // covered by the title page
      newQuestionPage();
      blocks.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 0, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 4 } },
        children: runs(line.slice(2), { size: 30, bold: true, color: ACCENT }) }));
      i++; continue;
    }
    if (line.startsWith("## ")) {
      inNumbered = false;
      blocks.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 100 }, keepNext: true,
        children: runs(line.slice(3), { size: 24, bold: true, color: ACCENT }) }));
      i++; continue;
    }
    if (line.startsWith("|")) {
      const t = [];
      while (i < lines.length && lines[i].startsWith("|")) t.push(lines[i++]);
      blocks.push(table(t), new Paragraph({ spacing: { after: 120 }, children: [] }));
      continue;
    }
    const bullet = line.match(/^\s*- (.*)$/), numbered = line.match(/^\s*(\d+)\. (.*)$/);
    if (bullet || numbered) {
      let text = bullet ? bullet[1] : numbered[2];
      i++;
      while (i < lines.length && /^\s{2,}\S/.test(lines[i]) && !/^\s*(- |\d+\. )/.test(lines[i])) text += " " + lines[i++].trim();
      if (numbered && !inNumbered) { listInstance++; inNumbered = true; }
      if (bullet) inNumbered = false;
      blocks.push(new Paragraph({ spacing: { after: 50, line: 260 },
        numbering: bullet ? { reference: "bullets", level: 0 } : { reference: "numbered", level: 0, instance: listInstance },
        children: runs(text) }));
      placeFigures(text);
      continue;
    }
    let text = line.trim(); i++;
    while (i < lines.length && lines[i].trim() && !/^(#|\||>|---|\s*- |\s*\d+\. )/.test(lines[i])) text += " " + lines[i++].trim();
    inNumbered = false;
    blocks.push(new Paragraph({ spacing: { after: 120, line: 264 }, children: runs(text) }));
    placeFigures(text);
  }
  flush();

  const missing = FIGURES.filter((f) => !placed.has(f.id)).map((f) => f.id);
  if (missing.length) throw new Error("figures never placed: " + missing.join(", "));

  return new Document({
    creator: "Lesego Jan Malema Matsimela",
    title: "ISJ107V Assignment 3 — Project Documentation and UML Design",
    styles: { default: { document: { run: { font: "Calibri", size: BODY } } } },
    numbering: { config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 460, hanging: 240 } } } }] },
      { reference: "numbered", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 460, hanging: 300 } } } }] },
    ] },
    sections,
  });
}

const doc = build();
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`wrote ${path.relative(ROOT, OUT)}  (${(buf.length / 1024).toFixed(0)} KB)\n`);
  console.log("diagram legibility (text ~13 px native; want >= 6 px shown):");
  for (const f of FIGURES.filter((f) => f.file.endsWith(".png")))
    console.log(`  Fig ${f.id.padEnd(3)} ${f.layout.padEnd(9)} ${String(f.shown.width).padStart(4)}x${String(f.shown.height).padEnd(4)} text ~${(13 * f.shown.scale).toFixed(1)} px`);
});
