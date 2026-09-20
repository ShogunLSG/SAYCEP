/* Builds the ISJ107V Assignment 2 submission as a .docx.
 *
 * Source of truth for the prose is docs/assignment-2-submission.md; this script
 * formats it and embeds the four UML diagrams from docs/uml/.
 *
 *   node docs/build-submission.js
 *
 * Regenerate after editing the markdown so the two do not drift.
 */

const fs = require("fs");
const path = require("path");
/* `docx` may be installed globally rather than in this project; Node does not
 * resolve global modules by default, so fall back to the npm global root. */
function loadDocx() {
  try { return require("docx"); }
  catch (e) {
    const root = require("child_process")
      .execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(require("path").join(root, "docx"));
  }
}
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, Footer, PageNumber, LevelFormat,
} = loadDocx();

const ROOT = path.resolve(__dirname, "..");
const UML = path.join(ROOT, "docs", "uml");
const OUT = path.join(ROOT, "docs", "ISJ107V_Assignment_2_SAYCEP.docx");

const CONTENT_WIDTH = 9026;          // A4 minus 1 inch margins, in DXA
const ACCENT = "1F3864";
const HEADER_BG = "D9E2F3";

/* ---------- helpers ---------- */

const p = (text, opts = {}) =>
  new Paragraph({
    spacing: { after: opts.after ?? 120, line: 276 },
    alignment: opts.alignment,
    children: [new TextRun({ text, bold: opts.bold, italics: opts.italics,
                             size: opts.size ?? 22, color: opts.color })],
  });

/** Paragraph from inline-marked text: **bold** segments only. */
const rich = (text, opts = {}) => {
  const children = [];
  text.split(/(\*\*[^*]+\*\*)/g).forEach((part) => {
    if (!part) return;
    const bold = part.startsWith("**") && part.endsWith("**");
    children.push(new TextRun({
      text: bold ? part.slice(2, -2) : part,
      bold, size: opts.size ?? 22, italics: opts.italics,
    }));
  });
  return new Paragraph({ spacing: { after: opts.after ?? 120, line: 276 }, children });
};

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 180 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 6 } },
  children: [new TextRun({ text, bold: true, size: 32, color: ACCENT })],
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 260, after: 120 },
  children: [new TextRun({ text, bold: true, size: 26, color: ACCENT })],
});

const bullet = (text) => rich(text, { after: 60 });

const cell = (text, { widths, i, bold = false, header = false, italics = false }) =>
  new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: HEADER_BG } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: String(text).split("\n").map((line) => {
      const children = [];
      line.split(/(\*\*[^*]+\*\*)/g).forEach((part) => {
        if (!part) return;
        const b = part.startsWith("**") && part.endsWith("**");
        children.push(new TextRun({
          text: b ? part.slice(2, -2) : part,
          bold: b || bold || header, italics, size: 19,
        }));
      });
      return new Paragraph({ spacing: { after: 0, line: 240 }, children });
    }),
  });

const table = (widths, header, rows) =>
  new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: header.map((t, i) => cell(t, { widths, i, header: true })),
      }),
      ...rows.map((r) => new TableRow({
        children: r.map((t, i) => cell(t, { widths, i })),
      })),
    ],
  });

/** Figure with a numbered caption below it. */
function figure(file, number, caption, maxW = 600, maxH = 700) {
  const buf = fs.readFileSync(path.join(UML, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  let width = maxW, height = Math.round((h / w) * maxW);
  if (height > maxH) { height = maxH; width = Math.round((w / h) * maxH); }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 80 },
      children: [new ImageRun({ data: buf, type: "png", transformation: { width, height } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 280 },
      children: [new TextRun({ text: `Figure ${number} — ${caption}`, bold: true, size: 19, color: "404040" })],
    }),
  ];
}

/* ---------- document ---------- */

const doc = new Document({
  creator: "SAYCEP",
  title: "ISJ107V Assignment 2 — Formal System Proposal and Specification",
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
                 alignment: AlignmentType.LEFT,
                 style: { paragraph: { indent: { left: 460, hanging: 240 } } } }],
    }],
  },
  styles: { default: { document: { run: { font: "Calibri", size: 22 } } } },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "ISJ107V Assignment 2 — SAYCEP — page ", size: 18, color: "808080" }),
                     new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })],
        })],
      }),
    },
    children: [
      /* ---- title ---- */
      new Paragraph({ spacing: { before: 2200, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "ISJ107V — Integrated Software Project", size: 24, color: "595959" })] }),
      new Paragraph({ spacing: { before: 180, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Assignment 2", bold: true, size: 56, color: ACCENT })] }),
      new Paragraph({ spacing: { before: 100, after: 400 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Formal System Proposal and Specification", size: 28, color: "404040" })] }),
      new Paragraph({ spacing: { after: 60 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "SAYCEP", bold: true, size: 32 })] }),
      new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "South African Youth Career and Employment Platform", italics: true, size: 24, color: "404040" })] }),
      table([3000, 6026], ["Field", "Detail"], [
        ["Student name", "Lesego Jan Malema Matsimela"],
        ["Student number", "219045719"],
        ["Module code", "ISJ107V"],
        ["Assessment", "Assignment 2 — Individual"],
        ["Total marks", "50"],
        ["Submission", "Through EC"],
      ]),
      new Paragraph({ children: [new PageBreak()] }),

      /* ---- Q1 ---- */
      h1("Question 1 — Project Introduction  [8 marks]"),

      h2("1.1  Project title, description, intended users and emerging technology  (2)"),
      rich("**Title:** SAYCEP — South African Youth Career and Employment Platform"),
      rich("**Description.** SAYCEP is a web-based career guidance system that helps young people identify an achievable target occupation, understand precisely which skills they are missing to reach it, and follow an ordered pathway of intermediate steps to get there. It holds a catalogue of 879 occupations, each described by 35 skills rated for importance, together with the level of preparation each occupation requires and an expert-reviewed map of which occupations lead to which others."),
      rich("**Intended users.** Two profiles, and the system is designed around the difference between them:"),
      bullet("The enrolled student — already studying toward a qualification, with direction but not a plan. They need to know what a target role requires beyond what their course gives them."),
      bullet("The unqualified school-leaver — no qualification and no direction, including those for whom a degree is not the route. They need to discover what is reachable at all, which is why the system exposes occupations by preparation level rather than assuming a degree."),
      rich("**Emerging technology.** Machine learning, specifically **content-based recommendation using mean-centred cosine similarity** over 35-dimensional skill-importance vectors. Each occupation is represented as a vector of O*NET importance ratings; a user's self-assessed skill profile is compared against all 879 to rank them by fit."),

      h2("1.2  Problem statement  (3)"),
      rich("**The current problem.** South African youth unemployment is among the highest in the world, at [CITE]% for ages 15–34 [CITE: source and year]. But unemployment figures describe the symptom. The underlying problem this system addresses is narrower and more tractable: young people cannot see the route from where they are to work that exists. Career guidance is concentrated in better-resourced schools, it skews heavily toward university pathways, and it rarely tells a young person which specific, nameable skills stand between them and a particular job."),
      rich("**Who is affected.** Two groups, differently. School-leavers without a qualification are affected most severely: they are frequently steered toward degree routes they cannot access, while trade and technician occupations that require apprenticeship or vocational training rather than a degree go unmentioned. Of the 879 occupations in the system's catalogue, **525 — 59.7% — require no degree**. That is the majority of the labour market, and it is the part least visible to the people who most need it. Enrolled students are affected differently: they have direction but often discover only at graduation that their qualification alone does not meet what employers ask for."),
      rich("**Consequences of leaving it unresolved.** Young people continue to make irreversible decisions — which course to take, whether to continue studying, which jobs to apply for — on incomplete information. The individual cost is time and money spent on routes that do not lead anywhere they wanted. The systemic cost is a labour market where vacancies in skilled trades coexist with high youth unemployment, because the people who could fill them were never shown the path."),

      h2("1.3  Aim, objectives, scope and success criteria  (3)"),
      rich("**Aim.** To give South African youth a clear, evidence-based view of the skills and steps required to reach a specific occupation, including routes that do not require a degree."),
      rich("**Measurable objectives.**"),
      bullet("1.  Deliver a skills gap analysis that, for any of the 879 catalogued occupations, lists every missing skill classified as essential or desirable, returning results within 2 seconds."),
      bullet("2.  Generate a career pathway of no fewer than three ordered intermediate steps for any target occupation in the catalogue, each step naming the skills to acquire."),
      bullet("3.  Recommend occupations by skill similarity such that at least one of the top five results falls in the user's own occupational family in 55% or more of test cases, against a 6.9% random baseline."),
      rich("**Scope boundaries.**"),
      rich("*In scope:* profile creation for two user types; skill self-assessment against 35 skills; occupation search and browsing by preparation level; skills gap analysis; career pathway generation; similarity-based occupation recommendation; data provenance display.", { italics: false }),
      rich("*Out of scope:* employer-facing functionality of any kind; job vacancy listing or application; qualification verification; payment processing; mobile applications; and any authentication beyond profile identification, which is deliberate — see 3.3."),
      rich("**Success criteria.**"),
      bullet("1.  A user with no qualification can, in five screens or fewer and without instructions, reach a displayed pathway of at least three steps toward an occupation that requires no degree."),
      bullet("2.  Every occupation and skill shown to a user displays its source dataset and publication date, so that the origin of every claim the system makes is visible without being asked for."),

      new Paragraph({ children: [new PageBreak()] }),

      /* ---- Q2 ---- */
      h1("Question 2 — Requirements  [15 marks]"),

      h2("2.1  Ten prioritised functional requirements  (10)"),
      table([760, 860, 3500, 3906],
        ["ID", "Priority", "Requirement", "Acceptance criterion"],
        [
          ["FR-01", "Must", "The system shall allow a user to create a profile by selecting one of two profile types: enrolled student or school-leaver.", "Given a visitor on the profile creation screen, when they select a profile type and confirm, then the system creates a profile of that type and returns a unique profile identifier."],
          ["FR-02", "Must", "The system shall allow a user to record which of the 35 O*NET skills they currently hold, by self-assessment.", "Given a user with a created profile, when they select any subset of the 35 skills and submit, then the system stores exactly those skills against that profile and no others."],
          ["FR-03", "Must", "The system shall allow a user to select exactly one target occupation from the catalogue of 879 occupations.", "Given a user with a captured skill profile, when they choose an occupation, then the system records that occupation's SOC code as the profile's target and replaces any target previously set."],
          ["FR-04", "Should", "The system shall allow a user to search the occupation catalogue by title and return all matching occupations.", "Given the catalogue is loaded, when a user enters a search term of at least two characters, then the system returns every occupation whose title contains that term, case-insensitively, or states explicitly that there are no matches."],
          ["FR-05", "Must", "The system shall allow a user to filter the occupation catalogue by O*NET Job Zone and shall display the preparation level description for the selected zone.", "Given a user selects Job Zone 3, when the catalogue is displayed, then only the 209 occupations graded Job Zone 3 are listed, together with that zone's education, experience and training description."],
          ["FR-06", "Must", "The system shall rank candidate occupations by cosine similarity between the user's 35-dimensional skill vector and each occupation's O*NET importance vector, and shall display the five highest-ranked with their similarity scores.", "Given a profile holding at least one captured skill, when the user requests recommendations, then the system returns exactly five occupations ordered by descending similarity score, each displaying its score to two decimal places."],
          ["FR-07", "Must", "The system shall compare a user's captured skills against the skills required for their target occupation and shall display each missing skill classified as either essential or desirable.", "Given a profile with captured skills and a target occupation, when the user views the skills gap, then the system lists every skill the target requires that the profile does not hold, each labelled essential where its O*NET importance rating is 3.5 or above and desirable where it is below 3.5."],
          ["FR-08", "Must", "The system shall generate an ordered pathway of no fewer than three intermediate steps between the user's current profile and their target occupation, each step naming the skills to be acquired at that step.", "Given a profile with a target occupation, when the user requests a pathway, then the system displays at least three ordered steps, each identifying a named occupation and listing at least one skill to acquire."],
          ["FR-09", "Should", "The system shall display the source dataset and publication date for every occupation and skill record presented to the user.", "Given any occupation or skill shown on screen, when the user views it, then the source dataset name and that record's publication date are visible without further navigation."],
          ["FR-10", "Must", "The system shall rebuild its occupation database from the O*NET source files on demand, and shall abort the load if any source file's row count differs from the published reference count.", "Given the O*NET source files are present and intact, when the load command is run, then the system builds a database of 879 occupations, 35 skills and 27,463 importance ratings. Given any source file has an unexpected row count, when the load is run, then it aborts and names the offending file."],
        ]),

      h2("2.2  Four measurable non-functional requirements (FURPS+)  (2)"),
      table([760, 1150, 760, 3100, 3256],
        ["ID", "Category", "Priority", "Requirement", "Acceptance criterion"],
        [
          ["NFR-01", "Performance", "Must", "The system shall return any screen on the demo path within 2 seconds of the request.", "Measured response time is 2 seconds or less for 95% of requests across all 879 occupations."],
          ["NFR-02", "Usability", "Must", "The system shall allow a first-time user to complete the journey from profile creation to displayed pathway in no more than five screens and without written instructions.", "An unassisted first-time user reaches a displayed pathway in 5 screens or fewer."],
          ["NFR-03", "Reliability", "Must", "The system shall refuse to start when its database is absent or fails its row-count check, rather than serving partial data.", "Given a missing or incomplete database, when the service starts, then it exits with a named error and serves no requests."],
          ["NFR-04", "Supportability", "Should", "The system shall rebuild its entire database from the O*NET source files with a single command in under 60 seconds.", "Measured wall-clock time of the rebuild command is 60 seconds or less. (Currently measured at 1.1 seconds.)"],
        ]),
      rich("**On the “+” in FURPS+.** This project's binding constraint is a data constraint, not a technical one: all system data must originate from Kaggle-sourced datasets, with anything else requiring the lecturer's approval in person. It shaped more of this design than any performance target did.", { after: 200 }),

      h2("2.3  Three testable emerging-technology requirements  (3)"),
      rich("The emerging technology is content-based occupation recommendation using mean-centred cosine similarity over 35-dimensional O*NET skill-importance vectors. The three requirements below were measured on the running engine, not estimated."),
      table([760, 1150, 760, 3100, 3256],
        ["ID", "Metric", "Priority", "Requirement", "Acceptance criterion"],
        [
          ["TR-01", "Model accuracy", "Must", "The recommendation engine shall place at least one occupation from the user's own occupational family in the top five results for no fewer than 55% of test profiles.", "Measured over at least 100 test profiles built from occupations' essential skill sets, at least one top-five result shares the target's SOC major group in 55% or more of cases, against a random baseline of 6.9%. (Measured: 59.7%.)"],
          ["TR-02", "Inference latency", "Must", "The recommendation engine shall rank the full catalogue of 879 occupations and return the top five within 100 milliseconds.", "Measured 95th-percentile inference latency is 100 ms or less. (Measured: 8.8 ms p95, 6.9 ms median.)"],
          ["TR-03", "Determinism and robustness", "Must", "The recommendation engine shall return exactly five ranked occupations, each with its similarity score, for any profile holding at least one skill, and shall return an explicit empty result for a profile holding none.", "Given a profile with one or more skills, five scored results are returned. Given a profile with no skills, an empty result and an explanatory message are returned rather than an arbitrary ranking."],
        ]),
      rich("**Why the accuracy bar is 55% and not 90%.** O*NET's 35 skills are deliberately generic, and almost every occupation requires most of them to some degree. Measured on the loaded catalogue, the mean cosine similarity between an occupation and its nearest neighbour is 0.994 — in raw skill space the occupations are near-duplicates. Exact-occupation recall is therefore the wrong metric: occupations with near-identical skill profiles should legitimately score alike. Mean-centring each vector against the average occupation lifted top-five occupational-family agreement from 19.4% to 32.4% against a 6.9% random baseline. A stated target of 90% would be a claim the data cannot support.", { after: 200 }),

      new Paragraph({ children: [new PageBreak()] }),

      /* ---- Q3 ---- */
      h1("Question 3 — Technical Environment  [10 marks]"),

      h2("3.1  Proposed technology stack and justification  (3)"),
      table([1800, 2400, 4826],
        ["Layer", "Choice", "Justification"],
        [
          ["User interface", "React, served as a single page", "Named in the project proposal; the component model suits the four-screen demo path. Loaded from CDN rather than a build toolchain, removing a category of setup failure."],
          ["Application layer", "Python 3.10+ with FastAPI", "One language across the API, the data loading and the recommendation engine. FastAPI gives typed request validation and generated API documentation without additional libraries."],
          ["Dataset", "O*NET 29.0 Database, obtained via Kaggle", "CC BY 4.0, published by the U.S. Department of Labor. Supplies importance-rated skills, preparation levels and an expert-reviewed occupation graph."],
          ["Database", "SQLite, single file", "No server to install, configure or keep running. The database is a derived artifact rebuilt from source in 1.1 seconds, so durability is not a requirement it has to meet."],
          ["Emerging technology", "Mean-centred cosine similarity, Python standard library", "No framework needed: the feature space is 35 dimensions and the whole catalogue ranks in 8.8 ms. A machine-learning framework would add weight without adding capability."],
          ["APIs", "Internal REST over HTTP/JSON", "No external API calls at request time. All data is local, which is what makes the 2-second performance requirement easy to meet."],
          ["Development tools", "Git, Python standard library, PlantUML for modelling", "The project has no third-party runtime dependencies at all, which is unusual and deliberate."],
          ["Deployment platform", "Local host for the demonstration", "Sized in 3.2. Nothing in the design prevents container deployment later."],
        ]),
      rich("**The main justification, stated plainly.** Every choice above optimises for a system that can be built, demonstrated and explained by one developer. A multi-service architecture with a separate ML service, a database server and a frontend build pipeline is the conventional answer, and would have consumed the available time in configuration rather than capability.", { after: 200 }),

      h2("3.2  Minimum and recommended hardware requirements  (4)"),
      table([2400, 3313, 3313],
        ["Component", "Minimum", "Recommended"],
        [
          ["Processor", "Dual-core x86-64, 2.0 GHz", "Quad-core x86-64, 2.5 GHz or better"],
          ["Memory", "4 GB RAM", "8 GB RAM"],
          ["Storage", "500 MB free — 97 MB source data, 5 MB database, runtime and interpreter", "2 GB free, SSD"],
          ["Network / connectivity", "None at runtime; a connection is required once to download the dataset", "Broadband for the initial 13 MB dataset download"],
          ["Client devices", "Any device with a modern browser supporting ES6 — desktop, laptop or tablet", "Desktop or laptop, 1366×768 or larger, for the tabular gap and pathway views"],
          ["Specialised hardware", "None", "None"],
        ]),
      rich("**On specialised hardware.** The emerging technology requires no GPU and no accelerator. This is a consequence of the design choice rather than an accident: the recommendation operates on 879 vectors of 35 dimensions and completes in under 9 milliseconds on ordinary hardware. A deep learning approach would have required specialised hardware to train and a dependency to run, for a problem whose entire feature space is 35 curated survey dimensions. Choosing a technology proportionate to the problem is an engineering decision, not a limitation.", { after: 200 }),

      h2("3.3  Architecture, communication, scalability, security, backup and recovery  (3)"),
      rich("**Architecture and communication.** A single deployable service. The React client issues HTTP/JSON requests to the FastAPI application layer, which calls two internal modules — the Gap Analyser and the Recommendation Engine — both of which read through an Occupation Repository onto SQLite. Figure 4 shows this path for the pathway use case. The production design documented in the proposal separates the ML component into its own service; the demonstration deliberately does not, and the module boundaries in code are kept clean so that the separation remains possible without rework."),
      rich("**Scalability.** The dataset is read-only at runtime and identical for every user, so it can be replicated behind a load balancer without coordination. The recommendation engine is stateless and CPU-bound, so it scales horizontally, and its 8.8 ms latency leaves ample headroom. The first bottleneck under real load would be per-request vector construction, which is cacheable in memory since the occupation vectors never change between data loads."),
      rich("**Security.** The system holds no credentials, no payment data and no personal identifiers — a profile is a set of self-declared skills and a target occupation, with no name, email or contact details attached. This is the strongest security posture available: data that is not collected cannot be breached. Input is constrained to selections from fixed catalogues rather than free text, which removes injection surface, and all database access uses parameterised queries."),
      rich("**Backup and recovery.** The database is a derived artifact, not a system of record. It is rebuilt from the O*NET source files by a single command in 1.1 seconds, and the loader refuses to complete if any source file's row count differs from O*NET's published reference — so a corrupted rebuild fails loudly rather than producing a database that looks correct and is quietly wrong. User profiles are the only non-reproducible data and would require conventional backup in a production deployment.", { after: 200 }),

      new Paragraph({ children: [new PageBreak()] }),

      /* ---- Q4 ---- */
      h1("Question 4 — UML Models  [13 marks]"),
      rich("The four diagrams below were authored in PlantUML. Actor, class, component and requirement names are consistent across all four and with the requirements in Question 2 — the ten use cases UC-01 to UC-10 map one-to-one onto FR-01 to FR-10."),

      h2("4.1  Use-case diagram  (4)"),
      rich("Shows the system boundary, the Youth User actor generalised into Enrolled Student and School-Leaver, the Data Administrator and O*NET Dataset as supporting actors, and include and extend relationships between the ten use cases."),
      ...figure("01-use-case.png", 1, "SAYCEP use-case diagram, showing the system boundary, primary and supporting actors, and the ten use cases UC-01 to UC-10."),

      new Paragraph({ children: [new PageBreak()] }),
      h2("4.2  Activity diagram  (3)"),
      rich("Models the end-to-end workflow from profile creation to displayed pathway, including the decision on profile type, the two alternative paths, the alternative path where the skills gap is empty, and the Recommendation Engine as the labelled emerging-technology step."),
      ...figure("02-activity.png", 2, "End-to-end activity workflow, with the emerging-technology step highlighted on the school-leaver branch.", 460, 720),

      new Paragraph({ children: [new PageBreak()] }),
      h2("4.3  Class diagram  (3)"),
      rich("Shows the main domain classes with attributes and operations, Profile generalised into StudentProfile and SchoolLeaverProfile, and Pathway composed of PathwayStep with multiplicity 3..*, which encodes FR-08's three-step minimum as a model constraint rather than as prose."),
      ...figure("03-class.png", 3, "Domain class diagram, showing inheritance, composition and multiplicities.", 580, 700),

      new Paragraph({ children: [new PageBreak()] }),
      h2("4.4  Sequence diagram  (3)"),
      rich("Shows the time-ordered interaction for UC-08 Generate Career Pathway across the user interface, application logic, data service and emerging-technology component."),
      ...figure("04-sequence.png", 4, "Sequence diagram for UC-08 Generate Career Pathway, crossing the user interface, application logic, data service and Recommendation Engine."),

      new Paragraph({ children: [new PageBreak()] }),

      /* ---- Q5 ---- */
      h1("Question 5 — Implementation and Evaluation  [13 marks]"),

      h2("5.1  Dataset, interface, entities, inputs, outputs, validation and privacy  (2)"),
      rich("**Dataset.** The O*NET 29.0 Database, published by the U.S. Department of Labor's Employment and Training Administration under CC BY 4.0 and obtained through Kaggle. Loading it produces 879 occupations, 35 skills, 27,463 importance ratings, 17,580 related-occupation links and 5 preparation levels. It is United States occupational data; the South African framing of this project lives in the problem statement and the design decisions rather than in the ingested data, and that distinction is deliberate."),
      rich("**Main data entities.** occupations (SOC code, title, description, job zone); skills (element ID, name, description); occupation_skills (importance rating on a 1–5 scale, scale maximum, publication date); related_occupations (tier, expert-review order); job_zone_reference (preparation level descriptions); users and user_skills (the captured profile)."),
      rich("**Interface.** Internal REST over HTTP/JSON:"),
      ...[
        "GET  /occupations?zone=&q=       list and filter the catalogue",
        "GET  /occupations/{soc}          one occupation with provenance",
        "GET  /skills                     all 35, for the capture screen",
        "POST /profiles                   create a profile with captured skills",
        "GET  /profiles/{id}/gap          missing skills, classified, by importance",
        "GET  /profiles/{id}/pathway      ordered steps with skills per step",
        "GET  /recommendations            ranked occupations by similarity",
      ].map((line) => new Paragraph({
        spacing: { after: 0, line: 240 },
        shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
        indent: { left: 240 },
        children: [new TextRun({ text: line, font: "Consolas", size: 18 })],
      })),
      new Paragraph({ spacing: { after: 140 }, children: [] }),
      rich("**Inputs.** Profile type (one of two fixed values); skill selections (a subset of 35 fixed identifiers); target occupation (one SOC code from the catalogue); job zone filter (integer 1–5); search term (text)."),
      rich("**Outputs.** Classified skills gap; ordered pathway with skills per step; ranked occupation recommendations with similarity scores; source dataset and publication date on every record."),
      rich("**Validation.** Every input except the search term is a selection from a fixed, server-known set, so validation is membership checking rather than parsing. SOC codes are verified against the catalogue; job zones must be 1–5; skill identifiers must exist in the 35-entry taxonomy. At load time, every source file's row count is checked against O*NET's published figures and the load aborts on any mismatch."),
      rich("**Privacy.** The system collects no personal identifiers — no name, email, contact details or demographic data. A profile is a set of self-declared skills and a target occupation. Nothing collected identifies a person, which means there is no personal data to protect, disclose or lose.", { after: 200 }),

      h2("5.2  Emerging-technology integration and interface contract  (2)"),
      rich("The Recommendation Engine sits between target selection and pathway generation. It is invoked when a school-leaver needs candidate occupations, and when the pathway service orders intermediate steps."),
      rich("**Interface contract:**"),
      ...[
        "recommend(connection, held_skill_ids, limit=5, max_job_zone=None)",
        "    -> [(soc_code: str, title: str, score: float), ...]",
        "",
        "  Preconditions:",
        "    held_skill_ids is a subset of the 35 O*NET skill identifiers",
        "    max_job_zone is in {1..5} or None",
        "  Postconditions:",
        "    returns exactly `limit` results ordered by descending score,",
        "      where held_skill_ids is non-empty",
        "    returns [] where held_skill_ids is empty          (TR-03)",
        "    every returned soc_code exists in the catalogue",
        "    0.0 <= score <= 1.0",
      ].map((line) => new Paragraph({
        spacing: { after: 0, line: 240 },
        shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
        indent: { left: 240 },
        children: [new TextRun({ text: line || " ", font: "Consolas", size: 18 })],
      })),
      new Paragraph({ spacing: { after: 140 }, children: [] }),
      rich("**Pseudocode:**"),
      ...[
        "FOR each skill i in the 35-skill taxonomy",
        "    mean[i] <- average importance of skill i across all 879 occupations",
        "",
        "FOR each occupation o",
        "    centred[o][i] <- importance[o][i] - mean[i]",
        "",
        "profile[i] <- 1 if the user holds skill i, else 0",
        "centred_profile[i] <- profile[i] - (1 if mean[i] >= 3.5 else 0)",
        "",
        "FOR each occupation o (optionally restricted by job zone)",
        "    score[o] <- cosine(centred_profile, centred[o])",
        "",
        "RETURN the 5 occupations with highest score",
      ].map((line) => new Paragraph({
        spacing: { after: 0, line: 240 },
        shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
        indent: { left: 240 },
        children: [new TextRun({ text: line || " ", font: "Consolas", size: 18 })],
      })),
      new Paragraph({ spacing: { after: 140 }, children: [] }),
      rich("**Why mean-centring.** Measured on the loaded catalogue, the mean cosine similarity between an occupation and its nearest neighbour is 0.994 — the raw vectors nearly all point the same way, because O*NET's skills are generic. Subtracting each skill's mean re-expresses an occupation by how it deviates from the average occupation, which is where the discriminating signal actually is. This lifted top-five occupational-family agreement from 19.4% to 32.4%.", { after: 200 }),

      h2("5.3  Testing and evaluation plan  (2)"),
      rich("**Functional testing.** Each of FR-01 to FR-10 has a Given/When/Then acceptance criterion, written to be executable rather than interpretive. Data-layer requirements are already verified: FR-10's row counts are asserted by the loader on every run, and FR-08's three-step minimum was confirmed by checking that all 879 occupations have three or more reachable primary neighbours."),
      rich("**Emerging-technology metric.** Top-five occupational-family agreement, measured against a random baseline. Test profiles are constructed by taking an occupation's essential skills as a stand-in for a person suited to it, then checking whether the engine returns occupations in the same SOC major group. Current measurement: 59.7% against a 6.9% baseline, with the requirement set at 55%. Exact-occupation recall is deliberately not the metric, because occupations with near-identical skill profiles should legitimately score alike."),
      rich("**User acceptance testing.** Two participants per user profile, four in total, each asked to reach a displayed pathway without instruction. Success is measured against NFR-02: five screens or fewer, unassisted. The school-leaver participants matter most, since that path involves discovering occupations rather than searching for a known one."),
      rich("**Principal technical risk and mitigation.** The recommendation engine's discrimination is inherently limited by the generic nature of O*NET's 35-skill taxonomy — a 0.994 mean nearest-neighbour similarity is a property of the data, not a defect in the implementation. If accuracy proves insufficient under user testing, the mitigation is available and unused: O*NET supplies Knowledge (33 elements), Abilities (52) and Work Activities (41) in the same structure and the same files already downloaded. Extending the feature space from 35 to 161 dimensions requires no new data source, no schema redesign and no change to the algorithm — only a wider vector."),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("wrote " + path.relative(ROOT, OUT) + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
