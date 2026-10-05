/* SAYCEP — the CV check (module 3, ADR-0014).
 *
 * Paste a CV; see which skills it shows (each quoting the line that showed
 * it), add the ones that are true, and see how it reads against the goal.
 * The text goes to the API, is read, and is forgotten -- never saved.
 */

const EXAMPLE_CV = `Thabo Mokoena — 072 555 0134
Career objective: I want to become a qualified electrician through an apprenticeship.
Education: Matric (2025) with Mathematics and Physical Science. Studying N2 Electrical at a TVET college.
Experience:
- Helped my uncle install wiring and plug points in new houses on weekends.
- Fixed broken bicycles and small appliances for neighbours.
- Worked at a hardware store: served customers, checked stock and kept records.
Skills: using a multimeter, soldering irons and power drills; Microsoft Excel; working in a team; reading circuit diagrams.`;

function CvPage({ profileId, onSet, onOpenSkill }) {
  const [text, setText] = useState("");
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [added, setAdded] = useState(() => new Set());

  async function scan() {
    setBusy(true); setError(null);
    try { setRes(await api.post("/cv/scan", { text, profile_id: profileId })); setAdded(new Set()); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function add(sg) { await onSet(sg, "held"); setAdded((a) => new Set(a).add(sg.element_id)); }

  const g = res && res.goal;
  return html`
    <div class="page">
      <div class="page-body">
        <p class="kicker">Check my CV${PRESENTER ? " · ADR-0014" : ""}</p>
        <h3 class="sheet-title">What does your CV show?</h3>
        <p class="about">Paste your CV below. We'll point out the skills it shows and how it reads for your goal.${" "}<b>It's read and forgotten — never saved.</b></p>
        <textarea id="cv-text" class="cvbox" rows="9" maxLength="15000" value=${text}
                  placeholder="Paste the text of your CV here…" onInput=${(e) => setText(e.target.value)}></textarea>
        <div class="plan-actions">
          <button class="btn" disabled=${busy || text.trim().length < 20} onClick=${scan}>${busy ? "Reading…" : "Check my CV"}</button>
          <button class="btn ghost" onClick=${() => { setText(EXAMPLE_CV); setRes(null); }}>Use an example CV</button>
        </div>
        ${error && html`<div class="banner">${error}</div>`}

        ${res && html`
          <h4 class="sect">Skills your CV shows</h4>
          ${res.suggestions.length === 0
            ? html`<p class="note">We couldn't spot any clearly. Describe what you did in plain words — "fixed", "taught", "served customers".</p>`
            : html`<p class="note">Add the ones that are true. We only go by the words — you know what you can do.</p>
              ${res.suggestions.map((sg) => {
                const have = sg.status === "held" || added.has(sg.element_id);
                return html`
                  <div key=${sg.element_id} class="ps cvs">
                    <div class="ps-t"><b><button class="tl" onClick=${() => onOpenSkill(sg)}>${sg.name}</button></b>
                      <span class="quote">“${sg.evidence}”</span></div>
                    <div class="ps-a">${have
                      ? html`<span class="okt">${Icon.check} On your list</span>`
                      : html`<button class="btn" onClick=${() => add(sg)}>Add to my skills</button>`}</div>
                  </div>`;
              })}`}

          ${g && html`
            <h4 class="sect">How it reads for ${g.title}</h4>
            <div class="goalchg">
              <p class="cvline">${g.named_for_this_job.length
                ? html`It names <b>${g.named_for_this_job.length}</b> of the tools and software this job uses: ${g.named_for_this_job.join(", ")}.`
                : "It doesn't name any of the tools or software this job uses yet."}</p>
              ${g.key_skills.map((k) => html`
                <p key=${k.element_id} class="cvline">${k.evidence
                  ? html`<span class="okt">${Icon.check}</span> <b>${k.name}</b> — “${k.evidence}”`
                  : html`<span class="miss">○</span> <b>${k.name}</b> — not shown yet. Add an example of when you did it.`}</p>`)}
              ${g.worth_mentioning.length > 0 && html`<p class="note">Worth mentioning if you've used them: ${g.worth_mentioning.join(", ")}.</p>`}
              <${Figure}>score ${g.score} (overlap ${g.overlap}, coverage ${g.coverage}) · ${g.basis}<//>
            </div>`}

          <h4 class="sect">CV checklist</h4>
          <ul class="sk">${res.checks.map((c) => html`
            <li key=${c.key} class=${c.present ? "have" : ""}><span class="mk">${c.present ? Icon.check : null}</span>
              <span>${c.label}${c.present ? "" : " — missing"}</span></li>`)}</ul>
          <p class="prov">Skills found by trigger words we wrote; tools and software as O*NET 29.0 lists them for each job.</p>`}
      </div>
    </div>`;
}

/** Home card: the way in from the plan. */
function CvCard({ onOpen }) {
  return html`
    <section class="card cvcard">
      <h3 class="ch">Check my CV</h3>
      <p class="note">Paste your CV to find skills you forgot to add, and see how it reads for your goal. Never saved.</p>
      <button class="btn full" onClick=${onOpen}>Check my CV</button>
    </section>`;
}
