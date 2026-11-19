/* SAYCEP — the skill-matching model, made visible (ADR-0025).
 *
 * The emerging technology is the recommendation engine: mean-centred cosine
 * similarity over 35 O*NET skill ratings (backend/recommend.py). It ranks For
 * you, orders the Pathway, turns a CV into job suggestions and finds the jobs
 * closest to a job. ModelTag marks each of those places; MatchSheet walks the
 * real numbers for one person and one job, in the five steps the
 * presentation uses, plus the must-have view added on 19 November (ADR-0027)
 * and, for a student who gives one, their field of study (ADR-0029).
 * Every figure comes from GET /profiles/{id}/match/{soc}.
 */

function ModelTag({ onExplain }) {
  return html`
    <p class="model-tag">
      <span class="mt-b">Skill-matching model</span>
      ${onExplain
        ? html`<button class="tl" onClick=${onExplain}>How does it work?</button>`
        : html`<span>ranks these by how closely the skills match</span>`}
    </p>`;
}

const fmt = (x) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(2);

/** A bar from 0 to max, its number beside it. The bar is decoration: the
 *  number is the content (WCAG 1.1.1). */
function Bar({ value, max, tone }) {
  return html`<span class="mbar" aria-hidden="true"><i class=${tone || ""} style=${{ width: `${Math.max(2, 100 * Math.abs(value) / max)}%` }}></i></span>`;
}

/** A diverging bar: below the average job to the left, above it to the right. */
function Diverge({ value, max }) {
  const w = Math.max(2, 50 * Math.abs(value) / max);
  return html`<span class="mdiv" aria-hidden="true"><i class=${value >= 0 ? "pos" : "neg"}
    style=${{ left: `${value >= 0 ? 50 : 50 - w}%`, width: `${w}%` }}></i></span>`;
}

/** Where this job's score sits in the range every job scores against you. */
function Range({ low, high, at, label }) {
  const pos = (x) => `${100 * (x + 1) / 2}%`;           // the scale runs from −1 to 1
  return html`
    <div class="mrange">
      <span class="mrange-t">${label}</span>
      <span class="mrange-l" aria-hidden="true">
        <i class="span" style=${{ left: pos(low), width: `${100 * (high - low) / 2}%` }}></i>
        <i class="zero" style=${{ left: "50%" }}></i>
        <b class="at" style=${{ left: pos(at) }}></b>
      </span>
      <span class="mrange-n">All jobs score from <b>${low.toFixed(2)}</b> to <b>${high.toFixed(2)}</b>; this job <b>${at.toFixed(2)}</b>.</span>
    </div>`;
}

function MatchSheet({ profileId, soc, onClose }) {
  const { data, error, loading } = useFetch(`/profiles/${profileId}/match/${soc}`);
  const box = useDialog(onClose);
  const [all, setAll] = useState(false);
  const d = data && data.explained ? data : null;
  const byNeed = d ? [...d.skills].sort((a, b) => b.importance - a.importance) : [];
  const byDiff = d ? [...d.skills].sort((a, b) => Math.abs(b.job_centred) - Math.abs(a.job_centred)) : [];
  const held = d ? d.skills.filter((k) => k.held) : [];
  // A field of study (ADR-0029) is one more row in what lifted or held back the score.
  const fieldRow = d && d.field ? { element_id: "field", name: `Your field: ${d.field.name}`, contribution: d.field.contribution } : null;
  const rowsC = fieldRow ? [...held, fieldRow] : held;
  const lifts = rowsC.filter((k) => k.contribution > 0).sort((a, b) => b.contribution - a.contribution);
  const drags = rowsC.filter((k) => k.contribution < 0).sort((a, b) => a.contribution - b.contribution);
  const maxDiff = d ? Math.max(...d.skills.map((k) => Math.abs(k.job_centred))) : 1;
  const maxC = d ? Math.max(0.01, ...rowsC.map((k) => Math.abs(k.contribution))) : 1;
  const N = all ? 35 : 8;
  // Rendered at the app's top level, not inside the page that opened it: in the
  // journey that page scrolls, and a panel inside it would be cut off.
  return ReactDOM.createPortal(html`
    <div class="scrim" onClick=${onClose}></div>
    <div class="sheet match" role="dialog" aria-modal="true" tabindex="-1" ref=${box}
         aria-label=${data ? `How we matched you to ${data.title}` : "How we matched you"}>
      <div class="grab"></div>
      <button class="x" aria-label="Close" onClick=${onClose}>×</button>
      <div class="sheet-body">
        <${Status} loading=${loading} error=${error}>
          ${data && !d && html`<p class="note">${data.message}</p>`}
          ${d && html`
            <p class="kicker">Skill-matching model${PRESENTER ? " · FR-06 · ADR-0025" : ""}</p>
            <h3 class="sheet-title">How we matched you to ${d.title}</h3>
            <p class="mscore"><b>${d.score.toFixed(2)}</b> <span>${d.match}</span></p>
            <p class="about">The model turns the job and you into lists of 35 numbers, one per skill,
              and measures how closely they point the same way, in two views of the job. Here are the real numbers.</p>

            <h4 class="sect"><span class="mstep">1</span> The job, as 35 numbers</h4>
            <p class="note">How much ${d.title.toLowerCase()} need each skill, out of 5 (O*NET's ratings). Ticked: skills you have.</p>
            <ul class="mrows">${byNeed.slice(0, N).map((k) => html`
              <li key=${k.element_id}><span class="mk" role="img" aria-label=${k.held ? "You have this" : "Not yet"}>${k.held ? Icon.check : null}</span>
                <span class="mn">${k.name}</span><${Bar} value=${k.importance} max=${5} /><span class="mv">${k.importance.toFixed(2)}</span></li>`)}
            </ul>

            <h4 class="sect"><span class="mstep">2</span> You, as 35 numbers</h4>
            <p class="note">Each skill you ticked is a 1, the rest are 0. You ticked <b>${held.length}</b>:${" "}${held.map((k) => k.name).join(", ")}.
              ${d.skills.some((k) => k.typical) && html` Skills almost every job needs
              (${d.skills.filter((k) => k.typical).map((k) => k.name).join(", ")}) count as ordinary, so having them doesn't set you apart.`}</p>

            <h4 class="sect"><span class="mstep">3</span> What makes this job different</h4>
            <p class="note">The model subtracts the average job from every job. What's left shows what this job needs${" "}<b>more</b> than most jobs (right) or <b>less</b> (left).</p>
            <ul class="mrows">${byDiff.slice(0, N).map((k) => html`
              <li key=${k.element_id}><span class="mk" role="img" aria-label=${k.held ? "You have this" : "Not yet"}>${k.held ? Icon.check : null}</span>
                <span class="mn">${k.name}</span><${Diverge} value=${k.job_centred} max=${maxDiff} /><span class="mv">${fmt(k.job_centred)}</span></li>`)}
            </ul>
            <button class="more" onClick=${() => setAll(!all)}>${all ? "Show the top 8" : "Show all 35 skills"}</button>

            <h4 class="sect"><span class="mstep">4</span> The job's must-have list</h4>
            <p class="note">Your answers are yes or no, so the model also compares them with the job's must-haves, which are
              yes or no too: the skills it rates 3.5 or more${d.skills.some((k) => k.must_have && k.importance < 3.5) ? " (this job has none, so its top 5)" : ""}.
              Ticked: ones you have.</p>
            <ul class="mrows">${d.skills.filter((k) => k.must_have).map((k) => html`
              <li key=${k.element_id}><span class="mk" role="img" aria-label=${k.held ? "You have this" : "Not yet"}>${k.held ? Icon.check : null}</span>
                <span class="mn">${k.name}</span><${Bar} value=${1 - k.must_have_share} max=${1} /><span class="mv">${Math.round(100 * k.must_have_share)}%</span></li>`)}
            </ul>
            <p class="note">The bar is how unusual each must-have is: the figure is the share of all jobs that also have it as a must-have.</p>

            <h4 class="sect"><span class="mstep">5</span> The score</h4>
            ${d.field
              ? html`<p class="note">The model measures how closely your skills match the job both ways, and averages them:
                  its ratings <b>${d.score_ratings.toFixed(2)}</b>, its must-have list <b>${d.score_must_haves.toFixed(2)}</b>,
                  so your skills score <b>${d.score_skills.toFixed(2)}</b>. Your field of study, <b>${d.field.name}</b>,
                  matches what this job needs to know at <b>${d.field.score.toFixed(2)}</b>${" "}(O*NET rates it${" "}${d.field.importance.toFixed(2)} out of 5 for this job). Your field counts for a tenth, so the match score is${" "}
                  <b>${d.score.toFixed(2)}</b>. Each share is below; they add up to the score.</p>`
              : html`<p class="note">The model measures how closely you match the job both ways, and averages them:
                  its ratings <b>${d.score_ratings.toFixed(2)}</b>, its must-have list <b>${d.score_must_haves.toFixed(2)}</b>,
                  so the match score is <b>${d.score.toFixed(2)}</b>. Each skill's share is below; they add up to the score.</p>`}
            ${lifts.length > 0 && html`<p class="msub">What lifted it</p>
              <ul class="mrows">${lifts.map((k) => html`
                <li key=${k.element_id}><span class="mn">${k.name}</span><${Bar} value=${k.contribution} max=${maxC} tone="pos" /><span class="mv">${fmt(k.contribution)}</span></li>`)}</ul>`}
            ${drags.length > 0 && html`<p class="msub">What held it back: skills you have that this job needs less than most</p>
              <ul class="mrows">${drags.map((k) => html`
                <li key=${k.element_id}><span class="mn">${k.name}</span><${Bar} value=${k.contribution} max=${maxC} tone="neg" /><span class="mv">${fmt(k.contribution)}</span></li>`)}</ul>`}

            <h4 class="sect">Why step 3 matters</h4>
            <${Range} label="Without step 3 (raw ratings against your ticks)" low=${d.spread.uncentred.low} high=${d.spread.uncentred.high} at=${d.score_uncentred} />
            <${Range} label="The model (steps 3 to 5)" low=${d.spread.centred.low} high=${d.spread.centred.high} at=${d.score} />
            <p class="note">Without step 3, all ${d.spread.jobs} jobs bunch together and every one looks like a fit, because nearly
              every job needs reading, listening and thinking. With it, they spread out, and jobs that don't suit you go below zero.</p>
            <p class="prov">${d.method} · ${d.dataset}</p>`}
        <//>
      </div>
    </div>`, document.querySelector(".app") || document.body);
}
