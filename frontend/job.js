/* SAYCEP — a job, in depth.
 *
 * JobDetail is shared: the journey shows it in a panel (RoleSheet, app.js);
 * the app shows it as a full page (JobPage) with related jobs, software and
 * tools added (ADR-0009). Like everything else, it only displays the API.
 */

function JobDetail({ data, full, onOpenJob }) {
  const [all, setAll] = useState(false);
  const [allTasks, setAllTasks] = useState(false);
  const [allTools, setAllTools] = useState(false);
  const must = data.required_skills.filter((k) => k.classification === "essential");
  const rest = data.required_skills.filter((k) => k.classification !== "essential");
  const known = data.held_count != null;
  const Skill = (k) => html`
    <li key=${k.element_id} class=${k.held ? "have" : ""}>
      ${known && html`<span class="mk" role="img" aria-label=${k.held ? "You have this" : "Not yet"}>${k.held ? Icon.check : null}</span>`}
      <span>${k.name}</span><${Figure}>${k.importance.toFixed(2)}<//>
    </li>`;
  return html`
    <p class="kicker">What is this job?${PRESENTER ? " · FR-04 · FR-09" : ""}</p>
    <h3 class="sheet-title">${data.title}</h3>
    <p class="about">${data.description}</p>
    ${data.tasks.length > 0 && html`
      <h4 class="sect">A day in this job</h4>
      <ul class="day">
        ${(allTasks ? data.tasks : data.tasks.slice(0, 4)).map((t, i) => html`
          <li key=${i}>${t.task}<${Figure}>${t.importance != null ? ` ${t.importance.toFixed(2)}` : " unrated"}<//></li>`)}
      </ul>
      ${data.tasks.length > 4 && html`<button class="more" onClick=${() => setAllTasks(!allTasks)}>
        ${allTasks ? "Show fewer" : "Show more of what they do"}</button>`}`}
    <div class="prep">
      <b>${data.preparation.label}</b>
      <span>${data.preparation.detail}</span>
      <${Figure}>${data.soc_code} · Job Zone ${data.job_zone}<//>
    </div>
    ${known && html`<p class="fit">${data.essential_count
      ? html`You have <b>${data.essential_held} of ${data.essential_count}</b> must-have skills
          and ${data.held_count} of ${data.required_skills.length} overall.`
      : html`You have <b>${data.held_count} of ${data.required_skills.length}</b> skills this job uses.`}</p>`}
    ${must.length > 0
      ? html`<h4 class="sect e">Must-have skills</h4><ul class="sk">${must.map(Skill)}</ul>`
      : html`<p class="note">This job has no single must-have skill — every skill below counts a little.</p>`}
    <h4 class="sect">${must.length ? "Other skills it uses" : "Skills it uses"}</h4>
    <ul class="sk">${(all ? rest : rest.slice(0, 6)).map(Skill)}</ul>
    ${rest.length > 6 && html`<button class="more" onClick=${() => setAll(!all)}>
      ${all ? "Show fewer" : `Show all ${rest.length}`}</button>`}

    ${full && data.tool_groups.length > 0 && html`
      <h4 class="sect">Tools of the trade</h4>
      <div class="tools">
        ${(allTools ? data.tool_groups : data.tool_groups.slice(0, 4)).map((g) => html`
          <div key=${g.category} class="tool"><b>${g.category}</b><span>${g.examples.join(", ")}</span></div>`)}
      </div>
      <p class="note">${data.tool_total} tools listed by O*NET for this job, grouped by kind.
        ${data.tool_groups.length > 4 && html` <button class="more inline" onClick=${() => setAllTools(!allTools)}>
          ${allTools ? "Show fewer" : "Show more kinds"}</button>`}</p>`}

    ${full && data.technology.length > 0 && html`
      <h4 class="sect">Software you'd use</h4>
      <div class="chips soft">
        ${data.technology.map((t) => html`
          <span key=${t.example} class=${"chip static" + (t.hot ? " hot" : "")}
                title=${t.category}>${t.example}${t.hot ? html` <i>in wide use</i>` : ""}</span>`)}
      </div>`}

    ${full && data.related.length > 0 && html`
      <h4 class="sect">Jobs like this</h4>
      <p class="note">O*NET's experts list these as closest to ${data.title.toLowerCase()}.</p>
      <div class="list">
        ${data.related.map((r) => html`
          <button key=${r.soc_code} class="occ" onClick=${() => onOpenJob(r)}>
            <span class="t">${r.title}<span class="meta">${r.preparation.label}</span></span>
            <span class="chev">›</span>
          </button>`)}
      </div>`}

    <${Prov} dataset=${data.provenance.dataset} dates=${data.provenance.skill_rating_dates} label="skill ratings dated" />
    ${data.provenance.task_dates.length > 0 && data.tasks.length > 0 &&
      html`<p class="prov tight">Tasks dated ${data.provenance.task_dates.join(", ")}</p>`}`;
}

function JobPage({ soc, profileId, goalSoc, onOpenJob, onMakeGoal, onSavedChange }) {
  const { data, error, loading } = useFetch(
    `/occupations/${soc}${profileId ? `?profile_id=${profileId}` : ""}`);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(null);
  const isSaved = saved ?? (data && data.saved);
  async function toggleSave() {
    const next = !isSaved;
    setSaved(next);
    try {
      if (next) await api.put(`/profiles/${profileId}/saved/${soc}`);
      else await api.del(`/profiles/${profileId}/saved/${soc}`);
      onSavedChange && onSavedChange();
    } catch (_) { setSaved(!next); }
  }
  const isGoal = goalSoc === soc;
  return html`
    <div class="page">
      <${Status} loading=${loading} error=${error}>
        ${data && html`
          <div class="page-body"><${JobDetail} data=${data} full onOpenJob=${onOpenJob} /></div>
          <div class="page-foot">
            <button class=${"btn full" + (isSaved ? " ok" : "")} aria-pressed=${!!isSaved} onClick=${toggleSave}>
              ${isSaved ? html`${Icon.check} Saved` : "Save this job"}</button>
            <button class="cta" disabled=${isGoal || busy}
                    onClick=${async () => { setBusy(true); try { await onMakeGoal(data); } finally { setBusy(false); } }}>
              ${isGoal ? "This is your goal" : busy ? "Working…" : "Make this my goal"}</button>
          </div>`}
      <//>
    </div>`;
}
