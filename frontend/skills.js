/* SAYCEP — skills: the Skills tab, a page per skill, and the unlock card.
 *
 * Every number here is computed by the API: a skill page's jobs come from
 * O*NET importance, and the unlock card from readiness before and after the
 * change (PUT /profiles/{id}/skills returns `changes`). Slice 2 of
 * docs/plans/full-app.md.
 */

const STATUS_LABEL = { held: "You have it", learning: "Working on it" };

function StatusActions({ status, busy, onSet }) {
  if (status === "held") return html`
    <div class="ps-a"><button class="btn ghost" disabled=${busy} onClick=${() => onSet(null)}>${Icon.undo} I don't have this</button></div>`;
  if (status === "learning") return html`
    <div class="ps-a">
      <button class="btn ok" disabled=${busy} onClick=${() => onSet("held")}>${Icon.check} I can do this now</button>
      <button class="btn ghost" disabled=${busy} onClick=${() => onSet(null)}>Stop</button>
    </div>`;
  return html`
    <div class="ps-a">
      <button class="btn" disabled=${busy} onClick=${() => onSet("learning")}>Start learning</button>
      <button class="btn ghost" disabled=${busy} onClick=${() => onSet("held")}>I can already</button>
    </div>`;
}

function SkillsTab({ profileId, rev, onOpenSkill, onOpenCv }) {
  const all = useFetch("/skills");
  const prof = useFetch(`/profiles/${profileId}`, rev);
  const [show, setShow] = useState("all");
  if (!all.data || !prof.data) return html`<div class="pane tabpane"><${Status} loading=${true} error=${all.error || prof.error} /></div>`;
  const status = Object.fromEntries(prof.data.skills.map((k) => [k.element_id, k.status]));
  const counts = { held: 0, learning: 0, none: 0 };
  all.data.skills.forEach((k) => { counts[status[k.element_id] || "none"]++; });
  const keep = (k) => show === "all" || (status[k.element_id] || "none") === show;
  const FILTERS = [["all", `All ${all.data.total}`], ["held", `Have ${counts.held}`],
                   ["learning", `Learning ${counts.learning}`], ["none", `Not yet ${counts.none}`]];
  return html`
    <div class="pane tabpane">
      <p class="sub tight">All 35 skills O*NET measures. Tap one to see what it opens up.</p>
      ${onOpenCv && html`<button class="btn full cvbtn" onClick=${onOpenCv}>Find skills in my CV</button>`}
      <div class="tabs" role="tablist">
        ${FILTERS.map(([k, label]) => html`
          <button key=${k} role="tab" aria-selected=${show === k} class=${"tab" + (show === k ? " on" : "")}
                  onClick=${() => setShow(k)}>${label}</button>`)}
      </div>
      ${all.data.groups.map((g) => {
        const rows = all.data.skills.filter((k) => k.group === g && keep(k));
        return rows.length > 0 && html`
          <div key=${g} class="group">
            <h4 class="gh">${g}</h4>
            <div class="list">
              ${rows.map((k) => html`
                <button key=${k.element_id} class="occ skillrow" onClick=${() => onOpenSkill(k)}>
                  <span class=${"sdot " + (status[k.element_id] || "none")}>${status[k.element_id] === "held" ? Icon.check : null}</span>
                  <span class="t">${k.name}
                    ${status[k.element_id] && html`<span class="meta">${STATUS_LABEL[status[k.element_id]]}</span>`}</span>
                  <span class="chev">›</span>
                </button>`)}
            </div>
          </div>`;
      })}
    </div>`;
}

function SkillPage({ elementId, profileId, rev, onSet, onOpenJob }) {
  const { data, error, loading } = useFetch(`/skills/${elementId}?profile_id=${profileId}`, rev);
  const [busy, setBusy] = useState(false);
  const set = async (status) => { setBusy(true); try { await onSet({ element_id: elementId, name: data.name }, status); } finally { setBusy(false); } };
  return html`
    <div class="page">
      <div class="page-body">
        <${Status} loading=${loading && !data} error=${error}>
          ${data && html`
            <p class="kicker">${data.group}</p>
            <h3 class="sheet-title">${data.name}</h3>
            <p class="about">${data.description}</p>
            <div class="skillstate">
              <span class=${"sdot big " + (data.status || "none")}>${data.status === "held" ? Icon.check : null}</span>
              <b>${data.status ? STATUS_LABEL[data.status] : "Not on your list yet"}</b>
            </div>
            <${StatusActions} status=${data.status} busy=${busy} onSet=${set} />
            <h4 class="sect">Where it matters most</h4>
            <p class="note">A must-have in <b>${data.must_have_in}</b> of the 879 jobs. These rely on it most:</p>
            <div class="list">
              ${data.top_jobs.map((j) => html`
                <button key=${j.soc_code} class="occ" onClick=${() => onOpenJob(j)}>
                  <span class="t">${j.title}<span class="meta">${j.level} · ${j.preparation.label}
                    <${Figure}> · ${j.importance.toFixed(2)}<//></span></span>
                  <span class="chev">›</span>
                </button>`)}
            </div>
            <${Prov} dataset=${data.source_dataset} dates=${data.rating_dates} />`}
        <//>
      </div>
    </div>`;
}

/** Shown after a skill change that did something worth saying. */
function UnlockCard({ u, onOpenJob, onClose }) {
  const c = u.changes, g = c.goal;
  const more = c.ready_jobs_after - c.ready_jobs_before;
  return html`
    <div class="scrim" onClick=${onClose}></div>
    <div class="sheet unlock" role="dialog" aria-modal="true" aria-label="What changed">
      <div class="grab"></div>
      <div class="sheet-body">
        <div class="burst">${Icon.check}</div>
        <h3 class="sheet-title center">${u.name}${u.status === "held" ? " — added" : " — removed"}</h3>
        ${g && html`
          <div class="goalchg">
            <span class="lbl">Your goal · ${g.title}</span>
            <p class="big-count"><b>${g.after}</b> of ${g.total} <span>${g.basis === "essential" ? "must-have skills" : "most important skills"}</span></p>
            <${Meter} have=${g.after} total=${g.total} big />
            ${g.ready && g.before < g.total && html`<p class="ready-line"><b class="h">You now have everything this job depends on.</b></p>`}
          </div>`}
        ${c.newly_ready_steps.length > 0 && html`
          <h4 class="sect">You're now ready for</h4>
          <div class="list">
            ${c.newly_ready_steps.map((j) => html`
              <button key=${j.soc_code} class="occ" onClick=${() => { onClose(); onOpenJob(j); }}>
                <span class="t">${j.title}<span class="meta">A job closely related to your goal</span></span><span class="chev">›</span>
              </button>`)}
          </div>`}
        ${more !== 0 && html`<p class="fit center">You have every must-have for <b>${c.ready_jobs_after}</b> jobs
          — ${Math.abs(more)} ${more > 0 ? "more" : "fewer"} than before.</p>`}
      </div>
      <div class="sheet-foot"><button class="cta" onClick=${onClose}>Nice</button></div>
    </div>`;
}

/** Worth a card, or only a toast? */
const isUnlock = (c) => !!c && ((c.goal && c.goal.after !== c.goal.before) ||
  c.newly_ready_steps.length > 0 || c.ready_jobs_after !== c.ready_jobs_before);
