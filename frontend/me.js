/* SAYCEP — the Me tab and the printable plan (slice 6).
 *
 * The plan code lives here, with sign-out and start-over. "Print my plan"
 * renders a one-page version and hands it to the browser's own print dialog
 * (which also saves as PDF) -- no library, no server-side rendering.
 */

function MeTab({ profileId, rev, onNameSaved, onPrint, onJourney, onSignOut, onStartOver }) {
  const { data } = useFetch(`/profiles/${profileId}`, rev);
  const [name, setName] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [fieldSaved, setFieldSaved] = useState(null);   // the area just saved, for the "Saved" note
  if (!data) return html`<div class="pane tabpane"><p class="loading">Loading…</p></div>`;
  const value = name ?? (data.display_name || "");
  async function save(e) {
    e.preventDefault(); setSaving(true);
    try { await api.put(`/profiles/${profileId}/name`, { display_name: value }); setSaved(true); onNameSaved(); }
    finally { setSaving(false); }
  }
  async function saveField(id) {
    const r = await api.put(`/profiles/${profileId}/field`, { element_id: id });
    setFieldSaved(r.field ? r.field.name : "none"); onNameSaved();
  }
  return html`
    <div class="pane tabpane">
      <form class="card" onSubmit=${save}>
        <label class="field">
          <span>Your first name <i>(optional)</i></span>
          <input id="me-name" value=${value} maxLength="40" placeholder="Your first name"
                 onInput=${(e) => { setName(e.target.value); setSaved(false); }} />
        </label>
        <button class="btn" type="submit" disabled=${saving}>${saved ? html`${Icon.check} Saved` : "Save name"}</button>
        <p class="note">It's only used to greet you. Apart from a field of study, if you give one,
          SAYCEP asks for nothing else about you.</p>
      </form>

      ${data.profile_type === "student" && html`
        <section class="card">
          <${FieldPicker} id="me-field" value=${data.field ? data.field.element_id : null} onChange=${saveField} />
          <p class="note" aria-live="polite">${fieldSaved
            ? (fieldSaved === "none" ? "Saved: no field. Your matches use your skills only." : html`${Icon.check} Saved. Your matches now include ${fieldSaved}.`)
            : ""}</p>
        </section>`}

      <section class="card">
        <h3 class="ch">Your plan</h3>
        <div class="kv"><span>Starting point</span><b>${data.profile_type === "student" ? "I'm studying" : "I left school"}</b></div>
        ${data.profile_type === "student" && html`<div class="kv"><span>Field of study</span><b>${data.field ? data.field.name : "Not given"}</b></div>`}
        <div class="kv"><span>Goal</span><b>${data.target ? data.target.title : "Not set"}</b></div>
        <div class="kv"><span>Skills you have</span><b>${data.held_count}</b></div>
        <div class="kv"><span>Working on</span><b>${data.learning_count}</b></div>
        <div class="plan-actions">
          <button class="btn" onClick=${() => onJourney(2, data)}>Change my goal</button>
          <button class="btn ghost" onClick=${() => onJourney(1, data)}>Update my skills</button>
        </div>
      </section>

      <section class="card">
        <h3 class="ch">Print or share my plan</h3>
        <p class="note">A one-page version to take to a teacher, a parent or a career counsellor.
          Your browser can also save it as a PDF.</p>
        <button class="btn full" onClick=${onPrint}>Print my plan</button>
      </section>

      <section class="codecard">
        <span class="lbl">Your plan code${PRESENTER ? " · ADR-0008" : ""}</span>
        <b class="code mono">${data.plan_code}</b>
        <p>Use it to open this plan on another phone or computer. Anyone with the code can see
          your plan, so share it only with people you trust.</p>
      </section>

      <section class="card about">
        <h3 class="ch">Where the information comes from</h3>
        <p class="note">Every job, skill and rating comes from the O*NET 29.0 database (August 2024), published
          by the U.S. Department of Labor under CC BY 4.0 and taken from Kaggle. It describes American jobs:
          South African qualifications, pay and colleges may differ.</p>
      </section>

      <div class="plan-links">
        <button class="link" onClick=${onSignOut}>Sign out on this device</button>
        <button class="link" onClick=${onStartOver}>Start over from scratch</button>
      </div>
    </div>`;
}

/** The one-page plan. Hidden on screen; the only thing on paper. */
function PrintPlan({ profileId, onReady }) {
  const prof = useFetch(`/profiles/${profileId}`);
  const gap = useFetch(`/profiles/${profileId}/gap`);
  const route = useFetch(`/profiles/${profileId}/pathway`);
  const saved = useFetch(`/profiles/${profileId}/saved`);
  const ready = prof.data && gap.data && route.data && saved.data;
  useEffect(() => { if (ready) onReady(); }, [ready]);
  if (!ready) return null;
  const p = prof.data, g = gap.data, r = p.readiness;
  const must = g.missing.filter((m) => m.classification === "essential");
  const have = p.skills.filter((k) => k.status === "held").map((k) => k.name);
  const learning = p.skills.filter((k) => k.status === "learning").map((k) => k.name);
  return html`
    <div class="printable">
      <header>
        <span class="brand">SAYCEP</span>
        <h1>${p.display_name ? `${p.display_name}'s career plan` : "My career plan"}</h1>
        <p>Printed ${new Date().toLocaleDateString([], { day: "numeric", month: "long", year: "numeric" })} · plan code ${p.plan_code}</p>
      </header>
      <section>
        <h2>Goal: ${p.target.title}</h2>
        <p>${p.target.preparation.label}. ${p.target.preparation.detail}</p>
        <p><b>${r.have} of ${r.total}</b> ${r.basis === "essential" ? "must-have skills" : "most important skills"} held${" · "}${r.overall_have} of ${r.overall_total} skills this job uses.</p>
      </section>
      <section class="cols">
        <div>
          <h3>Still to learn</h3>
          ${must.length ? html`<ul>${must.map((m) => html`<li key=${m.element_id}><b>${m.name}</b> — ${m.description}</li>`)}</ul>`
            : html`<p>Every must-have is held.</p>`}
          ${learning.length > 0 && html`<p><b>Working on:</b> ${learning.join(", ")}</p>`}
        </div>
        <div>
          <h3>Skills I have</h3>
          <p>${have.join(", ")}</p>
        </div>
      </section>
      <section>
        <h3>My route</h3>
        <ol>${route.data.steps.map((st) => html`
          <li key=${st.soc_code}><b>${st.title}</b>${st.is_target ? " (goal)" : ""} — ${st.preparation.label}${st.ready ? " · ready" : ""}</li>`)}</ol>
      </section>
      ${saved.data.saved.length > 0 && html`
        <section>
          <h3>Other jobs I'm considering</h3>
          <ul>${saved.data.saved.map((j) => html`<li key=${j.soc_code}>${j.title} — ${j.readiness.have} of ${j.readiness.total} ${j.readiness.basis === "essential" ? "must-haves" : "key skills"}</li>`)}</ul>
        </section>`}
      <footer>Source: O*NET 29.0 (August 2024), U.S. Department of Labor, CC BY 4.0, via Kaggle.
        Describes American jobs; South African requirements may differ. Open this plan again at SAYCEP with the code above.</footer>
    </div>`;
}
