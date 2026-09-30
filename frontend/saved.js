/* SAYCEP — saved jobs and comparison (slice 3, ADR-0010).
 *
 * "Which of these is closest for me?" is the question a school-leaver actually
 * has once they've found a few jobs they like. Every figure is from the API.
 */

function SavedJobs({ profileId, rev, onOpen, onCompare }) {
  const { data } = useFetch(`/profiles/${profileId}/saved`, rev);
  const [pick, setPick] = useState([]);
  if (!data) return null;
  const toggle = (soc) => setPick((p) => p.includes(soc) ? p.filter((x) => x !== soc)
    : p.length < 3 ? [...p, soc] : p);
  return html`
    <section class="card">
      <h3 class="ch">Saved jobs</h3>
      ${data.saved.length === 0
        ? html`<p class="note">Save jobs from Explore to keep them here and compare how close you are to each.</p>`
        : html`
          ${data.saved.map((j) => html`
            <div key=${j.soc_code} class="svd">
              ${data.saved.length > 1 && html`
                <button class=${"pick" + (pick.includes(j.soc_code) ? " on" : "")} aria-pressed=${pick.includes(j.soc_code)}
                        aria-label=${`Select ${j.title} to compare`} onClick=${() => toggle(j.soc_code)}>${Icon.check}</button>`}
              <button class="svd-t" onClick=${() => onOpen(j)}>
                <b>${j.title}</b>
                <span class="meta">${j.readiness.have} of ${j.readiness.total} ${j.readiness.basis === "essential" ? "must-haves" : "key skills"} · ${j.preparation.label}</span>
                <${Meter} have=${j.readiness.have} total=${j.readiness.total} />
              </button>
            </div>`)}
          ${data.saved.length > 1 && html`
            <button class="btn full" disabled=${pick.length < 2} onClick=${() => onCompare(pick)}>
              ${pick.length < 2 ? "Tick two or three to compare" : `Compare ${pick.length} jobs`}</button>`}`}
    </section>`;
}

function ComparePage({ profileId, socs, onOpen }) {
  const q = socs.map((s) => `soc=${encodeURIComponent(s)}`).join("&");
  const { data, error, loading } = useFetch(`/profiles/${profileId}/compare?${q}`);
  return html`
    <div class="page">
      <div class="page-body">
        <${Status} loading=${loading} error=${error}>
          ${data && (() => {
            const best = Math.max(...data.jobs.map((j) => j.readiness.have / (j.readiness.total || 1)));
            return html`
              <p class="kicker">Compare</p>
              <h3 class="sheet-title">Which is closest for you?</h3>
              <div class=${"cmp cols" + data.jobs.length}>
                ${data.jobs.map((j) => html`
                  <div key=${j.soc_code} class=${"cmpcol" + (j.readiness.have / (j.readiness.total || 1) === best ? " lead" : "")}>
                    <button class="tl cmp-title" onClick=${() => onOpen(j)}>${j.title}</button>
                    <div class="cmp-row"><span class="lbl">Training</span>${j.preparation.label}</div>
                    <div class="cmp-row"><span class="lbl">${j.readiness.basis === "essential" ? "Must-haves" : "Key skills"}</span>
                      <b class="cmp-big">${j.readiness.have}<small> of ${j.readiness.total}</small></b>
                      <${Meter} have=${j.readiness.have} total=${j.readiness.total} /></div>
                    <div class="cmp-row"><span class="lbl">All skills</span>${j.overall_have} of ${j.overall_total}</div>
                    <div class="cmp-row"><span class="lbl">Still to learn</span>
                      ${j.to_learn.length === 0
                        ? html`<span class="okt">Nothing — you're ready</span>`
                        : j.to_learn.map((m) => html`<span key=${m.element_id} class="need">${m.name}</span>`)}
                    </div>
                  </div>`)}
              </div>
              ${data.shared_must_haves.length > 0 && html`
                <h4 class="sect">Must-haves they share</h4>
                <p class="note">Learning these moves you closer to all of them at once.</p>
                <ul class="sk">${data.shared_must_haves.map((m) => html`
                  <li key=${m.element_id} class=${m.held ? "have" : ""}><span class="mk">${m.held ? Icon.check : null}</span><span>${m.name}</span></li>`)}</ul>`}
              <p class="prov">O*NET 29.0 (August 2024 release)</p>`;
          })()}
        <//>
      </div>
    </div>`;
}
