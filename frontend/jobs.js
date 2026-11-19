/* SAYCEP — Jobs for you: sample listings as job cards (module 4, ADR-0022).
 *
 * Real adverts linked to a job by title, ranked by how much of what each one
 * mentions the user already has. They are US adverts from spring 2024, all
 * closed: every section says "Sample listings" and why, and Apply explains
 * itself rather than going anywhere. No company, link or pay is shown.
 */

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso) => { const [y, m, d] = iso.split("-"); return `${+d} ${MONTHS[+m - 1]} ${y}`; };

function SampleBadge({ note }) {
  return html`
    <p class="sample"><span class="sample-b">Sample listings</span>
      <span>${note}</span></p>`;
}

function JobCard({ j, showOccupation, onOpenJob }) {
  const [open, setOpen] = useState(false);
  const f = j.fit;
  const facts = [
    j.beginner && "Open to beginners",
    j.training_given && "Training given",
    j.years != null && `Asks ${j.years <= 1 ? "a year or less" : `${Math.round(j.years)} years`}`,
    ...j.requirements,
  ].filter(Boolean);
  const noteId = `apply-${j.advert_id}`;
  return html`
    <article class="jc">
      <div class="jc-top">
        <span class=${"fitb b" + f.band}>${f.words}</span>
        <span class="jc-when">Listed ${shortDate(j.listed)}</span>
      </div>
      <h4 class="jc-t">${j.title}</h4>
      <p class="jc-meta">
        ${showOccupation && html`<button class="tl" onClick=${() => onOpenJob({ soc_code: j.soc_code, title: j.occupation })}>${j.occupation}</button> · `}
        ${j.location}${j.work_type ? ` · ${j.work_type}` : ""}</p>
      ${f.mentioned > 0 && html`
        <p class="jc-have">You have <b>${f.have} of the ${f.mentioned}</b> skills it mentions${f.learning ? `, and you're learning ${f.learning}` : ""}.</p>
        <${Meter} have=${f.have} total=${f.mentioned} />`}
      ${facts.length > 0 && html`<div class="chips soft jc-facts">${facts.map((x) => html`
        <span key=${x} class=${"chip static" + (x === "Open to beginners" || x === "Training given" ? " hot" : "")}>${x}</span>`)}</div>`}
      <button class="btn ghost jc-apply" aria-expanded=${open} aria-controls=${noteId} onClick=${() => setOpen(!open)}>Apply</button>
      <p id=${noteId} class="note jc-note" hidden=${!open}>This is a demo listing from a closed US advert.
        In the full system, Apply opens the live advert on the employer's site.</p>
    </article>`;
}

/** Home: the three best-fitting listings across the goal and the route. */
function JobsForYouCard({ profileId, rev, onOpenAll, onOpenJob }) {
  const { data } = useFetch(`/profiles/${profileId}/listings?limit=3`, rev);
  if (!data || !data.loaded || data.listings.length === 0) return null;
  return html`
    <section class="card jobs">
      <h3 class="ch">Jobs for you</h3>
      <${SampleBadge} note=${data.note} />
      ${data.listings.map((j) => html`<${JobCard} key=${j.advert_id} j=${j} showOccupation onOpenJob=${onOpenJob} />`)}
      <button class="btn full" onClick=${onOpenAll}>See all ${data.total} jobs for you</button>
    </section>`;
}

/** A page: every listing for the goal and the jobs on the route, best fit first. */
function JobsPage({ profileId, onOpenJob }) {
  const { data, error, loading } = useFetch(`/profiles/${profileId}/listings?limit=40`);
  return html`
    <div class="page">
      <div class="page-body">
        <p class="kicker">Jobs for you${PRESENTER ? " · ADR-0022" : ""}</p>
        <h3 class="sheet-title">Jobs you'd fit</h3>
        <${Status} loading=${loading} error=${error}>
          ${data && (data.loaded
            ? html`
              <${SampleBadge} note=${data.note} />
              <p class="note">From your goal and the jobs on your route, best fit first.</p>
              ${data.listings.map((j) => html`<${JobCard} key=${j.advert_id} j=${j} showOccupation onOpenJob=${onOpenJob} />`)}
              <p class="prov">${data.dataset}</p>`
            : html`<p class="note">Sample listings aren't loaded on this copy of SAYCEP.</p>`)}
        <//>
      </div>
    </div>`;
}

/** The job page: this job's own listings. */
function JobListings({ soc, profileId }) {
  const { data } = useFetch(`/occupations/${soc}/listings?limit=10${profileId ? `&profile_id=${profileId}` : ""}`);
  const [all, setAll] = useState(false);
  if (!data || !data.loaded || data.listings.length === 0) return null;
  const shown = all ? data.listings : data.listings.slice(0, 3);
  return html`
    <section class="jobs" aria-labelledby="jl-h">
      <h4 class="sect" id="jl-h">Sample listings for this job</h4>
      <${SampleBadge} note=${data.note} />
      ${shown.map((j) => html`<${JobCard} key=${j.advert_id} j=${j} />`)}
      ${data.listings.length > 3 && html`<button class="more" onClick=${() => setAll(!all)}>
        ${all ? "Show fewer" : `Show ${data.listings.length - 3} more`}</button>`}
    </section>`;
}
