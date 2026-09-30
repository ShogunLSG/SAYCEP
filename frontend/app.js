/* SAYCEP — the five-screen journey.
 *
 * React without a build step: htm tagged templates stand in for JSX, so the
 * file runs as-is. Every figure on screen comes from the API. This file never
 * computes a gap, a recommendation or a pathway itself -- if a number looks
 * wrong, the place to look is backend/, not here.
 *
 * Add ?presenter to the URL to show which requirement each screen satisfies.
 */

if (!window.React || !window.ReactDOM || !window.htm) {
  // A blank page in front of a marker is the worst failure available. Say what
  // happened instead.
  document.getElementById("root").innerHTML =
    '<p style="max-width:36ch;text-align:center;color:#4A555F">' +
    "SAYCEP could not load its interface libraries, which currently come from " +
    "a CDN. Check the internet connection, or bundle them locally " +
    "(see docs/plans/frontend-journey.md).</p>";
  throw new Error("interface libraries missing");
}

const { useState, useEffect } = React;
const html = htm.bind(React.createElement);
const PRESENTER = new URLSearchParams(location.search).has("presenter");

// ---------- API ----------

async function request(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch (_) { /* keep the status line */ }
    throw new Error(detail);
  }
  return res.json();
}

const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  put: (path, body) => request("PUT", path, body),
  del: (path) => request("DELETE", path),
};

/** Fetch whenever `path` or `rev` changes; a null path fetches nothing.
 *  The previous data stays on screen while a refetch is in flight, so a
 *  progress tick updates in place instead of flashing "Loading…". */
function useFetch(path, rev = 0) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path });
  useEffect(() => {
    if (!path) { setState({ data: null, error: null, loading: false }); return; }
    let live = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    api.get(path).then(
      (data) => live && setState({ data, error: null, loading: false }),
      (err) => live && setState({ data: null, error: err.message, loading: false }),
    );
    return () => { live = false; };
  }, [path, rev]);
  return state;
}

// The saved plan is a profile id in this browser -- not an account. If the
// browser forgets it (private window, cleared data) the journey starts fresh.
const SAVED = "saycep.plan";
const saved = {
  get: () => { try { return localStorage.getItem(SAVED); } catch (_) { return null; } },
  set: (id) => { try { localStorage.setItem(SAVED, id); } catch (_) { /* plan lasts this visit */ } },
  clear: () => { try { localStorage.removeItem(SAVED); } catch (_) { /* nothing to clear */ } },
};

// ---------- small pieces ----------

const svg = (d, w = 2.2) => html`
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth=${w}
       strokeLinecap="round" strokeLinejoin="round">${d}</svg>`;
const Icon = {
  back: svg(html`<path d="M15 18l-6-6 6-6" />`),
  arrow: svg(html`<path d="M5 12h14M13 6l6 6-6 6" />`, 2.4),
  check: svg(html`<path d="M5 13l4 4L19 7" />`, 3.2),
  search: svg(html`<circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" />`, 2),
  undo: svg(html`<path d="M9 14L4 9l5-5" /><path d="M4 9h11a5 5 0 010 10h-3" />`, 2),
};

function Head({ kicker, fr, title, sub }) {
  return html`
    <p class="kicker">${kicker}${PRESENTER && fr ? ` · ${fr}` : ""}</p>
    <h2 class="title">${title}</h2>
    ${sub && html`<p class="sub">${sub}</p>`}`;
}

function Status({ loading, error, children }) {
  if (error) return html`<div class="banner">${error}</div>`;
  if (loading) return html`<p class="loading">Loading…</p>`;
  return children;
}

function Ring({ score, label }) {
  const r = 14, c = 2 * Math.PI * r;
  const s = Math.max(0, Math.min(1, score)); // mean-centred cosine can dip below 0
  return html`
    <span class="ring" title=${label || "Skill match"}>
      <svg width="36" height="36">
        <circle class="bg" cx="18" cy="18" r=${r} />
        <circle class="fg" cx="18" cy="18" r=${r}
                strokeDasharray=${c} strokeDashoffset=${c * (1 - s)} />
      </svg>
      ${PRESENTER && html`<span>${Math.round(s * 100)}%</span>`}
    </span>`;
}

/** The figures a marker checks against, shown only with ?presenter. */
function Figure({ children }) {
  return PRESENTER ? html`<span class="fig mono">${children}</span>` : null;
}

function OccRow({ occ, picked, onPick, score, match }) {
  return html`
    <button class=${"occ" + (picked ? " on" : "")} aria-pressed=${picked}
            onClick=${() => onPick(occ)}>
      ${score != null && html`<${Ring} score=${score} label=${match} />`}
      <span class="t">${occ.title}
        ${occ.also_called && html`<span class="aka">also called ${occ.also_called}</span>`}
        <span class="meta">
          ${match && html`<b class="match">${match}</b>
            <span class="score mono" title="Similarity score (FR-06)">${score.toFixed(2)}</span>${" · "}`}${occ.preparation ? occ.preparation.label : ""}
          <${Figure}>${occ.soc_code} · Zone ${occ.job_zone}<//>
        </span>
      </span>
      <span class="tick">${Icon.check}</span>
    </button>`;
}

const zoneName = (name) => (name || "").replace(/^Job Zone \w+:\s*/, "");

// Button labels for O*NET's five Job Zones, shortest form of backend/plain.py's
// wording. The full sentence for the chosen zone comes back from the API.
const ZONE_CHIPS = ["None", "Matric", "Trade", "Degree", "Postgrad"];

// ---------- the role sheet : "what is this job?" ----------
// The journey's quick look at a job. The same content fills the full job page
// in the app (JobDetail, in job.js).

function RoleSheet({ soc, profileId, isTarget, onAim, onClose }) {
  const { data, error, loading } = useFetch(
    `/occupations/${soc}${profileId ? `?profile_id=${profileId}` : ""}`);
  useEffect(() => {
    const esc = (e) => e.key === "Escape" && onClose();
    addEventListener("keydown", esc);
    return () => removeEventListener("keydown", esc);
  }, []);
  return html`
    <div class="scrim" onClick=${onClose}></div>
    <div class="sheet" role="dialog" aria-modal="true" aria-label=${data ? data.title : "Job details"}>
      <div class="grab"></div>
      <button class="x" aria-label="Close" onClick=${onClose}>×</button>
      <${Status} loading=${loading} error=${error}>
        ${data && html`
          <div class="sheet-body"><${JobDetail} data=${data} /></div>
          ${onAim && html`<div class="sheet-foot">
            <button class="cta" disabled=${isTarget} onClick=${() => { onAim(data); onClose(); }}>
              ${isTarget ? "This is your goal" : "Aim for this job"}</button>
          </div>`}`}
      <//>
    </div>`;
}

// ---------- step 1 : who ----------

const STARTS = [
  { v: "student", ico: "🎓", t: "I'm studying",
    p: "Enrolled in a qualification and planning what comes next.",
    via: "You'll search for the role you're aiming at" },
  { v: "school_leaver", ico: "🧭", t: "I left school",
    p: "No qualification yet — not sure what's actually open to me.",
    via: "We'll start with routes that don't need a degree" },
];

function StepStart({ type, onPick }) {
  return html`
    <${Head} kicker="Your starting point" fr="FR-01"
             title="Where are you starting from?"
             sub="This changes how we help you, not just what we call you." />
    ${STARTS.map((o) => html`
      <button key=${o.v} class=${"choice" + (type === o.v ? " on" : "")}
              aria-pressed=${type === o.v} onClick=${() => onPick(o.v)}>
        <span class="ico">${o.ico}</span>
        <span>
          <strong>${o.t}</strong><p>${o.p}</p>
          <span class="via">${o.via} →</span>
        </span>
        <span class="tick">${Icon.check}</span>
      </button>`)}`;
}

// ---------- step 2 : skills ----------

function StepSkills({ held, onToggle }) {
  const { data, error, loading } = useFetch("/skills");
  const [q, setQ] = useState("");
  const [last, setLast] = useState(null); // the skill last tapped, explained below
  const needle = q.toLowerCase();
  const shown = data ? data.skills.filter((s) =>
    s.name.toLowerCase().includes(needle) || (s.description || "").toLowerCase().includes(needle)) : [];
  const tap = (s) => { onToggle(s.element_id); setLast(s); };
  return html`
    <${Head} kicker="Your skills" fr="FR-02"
             title="What can you already do?"
             sub="Tap anything that's genuinely true of you — from school, work, home or helping out. Honest beats modest." />
    <${Status} loading=${loading} error=${error}>
      <div class="filter">
        ${Icon.search}
        <input id="skill-filter" placeholder="Search — try “fix”, “people” or “numbers”" autocomplete="off"
               value=${q} onInput=${(e) => setQ(e.target.value)} />
      </div>
      ${data && data.groups.map((g) => {
        const inGroup = shown.filter((s) => s.group === g);
        return inGroup.length > 0 && html`
          <div key=${g} class="group">
            <h4 class="gh">${g}</h4>
            <div class="chips">
              ${inGroup.map((s) => html`
                <button key=${s.element_id} class=${"chip" + (held.has(s.element_id) ? " on" : "")}
                        aria-pressed=${held.has(s.element_id)} aria-label=${s.name} title=${s.description}
                        onClick=${() => tap(s)}>${s.name}</button>`)}
            </div>
          </div>`;
      })}
      ${data && shown.length === 0 && html`<p class="note">No skills match “${q}”.</p>`}
    <//>
    <div class="hint" aria-live="polite">
      ${last
        ? html`<b>${last.name}</b> — ${last.description}`
        : "Not sure what a skill means? Tap it and we'll explain it here."}
    </div>
    <p class="count"><b>${held.size}</b> selected</p>`;
}

// ---------- step 3 : explore ----------

function StepExplore({ profileId, type, target, onOpen, head }) {
  const leaver = type === "school_leaver";
  const [tab, setTab] = useState(leaver ? "foryou" : "search");
  const [zone, setZone] = useState(leaver ? 3 : 4);
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  useEffect(() => { const t = setTimeout(() => setTerm(q.trim()), 250); return () => clearTimeout(t); }, [q]);

  const recs = useFetch(tab === "foryou"
    ? `/recommendations?profile_id=${profileId}&limit=5${leaver ? "&max_job_zone=3" : ""}` : null);
  const browse = useFetch(tab === "browse" ? `/occupations?zone=${zone}&limit=300` : null);
  const search = useFetch(tab === "search" && term.length >= 2
    ? `/occupations?q=${encodeURIComponent(term)}&limit=60` : null);

  const isPicked = (o) => target && target.soc_code === o.soc_code;
  const TABS = [["foryou", "For you"], ["browse", "Browse"], ["search", "Search"]];

  return html`
    ${head || html`<${Head} kicker="Your options" fr="FR-03 · FR-04 · FR-05 · FR-06"
             title="Pick something to aim for"
             sub="Tap a job to see what it involves, then aim for it. You can change your mind later." />`}
    <div class="tabs" role="tablist">
      ${TABS.map(([k, label]) => html`
        <button key=${k} role="tab" aria-selected=${tab === k}
                class=${"tab" + (tab === k ? " on" : "")} onClick=${() => setTab(k)}>${label}</button>`)}
    </div>

    ${tab === "foryou" && html`
      <p class="note">${leaver
        ? "Ranked by how closely your skills match — only roles that don't need a degree."
        : "Ranked by how closely your skills match, across every preparation level."}
        ${" "}The number is the match score: 1.00 would be identical.</p>
      <${Status} loading=${recs.loading} error=${recs.error}>
        ${recs.data && html`<div class="list">
          ${recs.data.recommendations.map((r) => html`
            <${OccRow} key=${r.soc_code} occ=${r} score=${r.score} match=${r.match}
                       picked=${isPicked(r)} onPick=${onOpen} />`)}
        </div>`}
        ${recs.data && recs.data.message && html`<p class="note">${recs.data.message}</p>`}
      <//>`}

    ${tab === "browse" && html`
      <p class="note">How much training does it take to start?</p>
      <div class="zones" role="group" aria-label="Preparation needed">
        ${ZONE_CHIPS.map((label, i) => html`
          <button key=${i} class=${"zone" + (zone === i + 1 ? " on" : "")} aria-pressed=${zone === i + 1}
                  onClick=${() => setZone(i + 1)}>${label}</button>`)}
      </div>
      <${Status} loading=${browse.loading} error=${browse.error}>
        ${browse.data && html`
          <p class="zdesc"><b>${browse.data.job_zone.preparation.label}.</b> ${browse.data.job_zone.preparation.detail}
            ${" "}${browse.data.total} jobs.
            <${Figure}>${zoneName(browse.data.job_zone.name)} (O*NET Job Zone ${zone})<//></p>
          <div class="list">
            ${browse.data.occupations.map((o) => html`
              <${OccRow} key=${o.soc_code} occ=${o} picked=${isPicked(o)} onPick=${onOpen} />`)}
          </div>`}
      <//>`}

    ${tab === "search" && html`
      <div class="filter">
        ${Icon.search}
        <input id="occ-search" placeholder="Search 879 jobs by any name — try “hairdresser”, “mechanic” or “chef”" autocomplete="off"
               value=${q} onInput=${(e) => setQ(e.target.value)} />
      </div>
      ${term.length < 2
        ? html`<p class="note">Type at least two letters.</p>`
        : html`<${Status} loading=${search.loading} error=${search.error}>
            ${search.data && html`
              <p class="note">${search.data.message || `${search.data.total} match${search.data.total === 1 ? "" : "es"}`}</p>
              <div class="list">
                ${search.data.occupations.map((o) => html`
                  <${OccRow} key=${o.soc_code} occ=${o} picked=${isPicked(o)} onPick=${onOpen} />`)}
              </div>`}
          <//>`}`}

    <p class="prov">Source: O*NET 29.0 (August 2024 release) · U.S. Department of Labor · CC BY 4.0</p>`;
}

// ---------- step 4 : gap ----------

function SkillRow({ m }) {
  const ess = m.classification === "essential";
  return html`
    <div class=${"row" + (ess ? " ess" : "")}>
      <span class="nm"><span>${m.name}</span></span>
      <span class="lvl">${m.level}</span>
      <span class="bar"><i style=${{ width: `${(m.importance / m.importance_scale_max) * 100}%` }}></i></span>
      <span class="desc">${m.description}<${Figure}> · ${m.importance.toFixed(2)} / ${m.importance_scale_max}<//></span>
    </div>`;
}

function StepGap({ profileId }) {
  const { data, error, loading } = useFetch(`/profiles/${profileId}/gap`);
  const [all, setAll] = useState(false);
  return html`
    <${Head} kicker="The gap" fr="FR-07 · FR-09" title="What's missing?" />
    <${Status} loading=${loading} error=${error}>
      ${data && (() => {
        const must = data.missing.filter((m) => m.classification === "essential");
        const nice = data.missing.filter((m) => m.classification !== "essential");
        const niceShown = all ? nice : nice.slice(0, 5);
        const dates = [...new Set(data.missing.map((m) => m.source_date).filter(Boolean))];
        return html`
          <div class="target">
            <h3>${data.target.title}</h3>
            <div class="meta">${data.target.preparation.label}
              <${Figure}> · ${data.target.soc_code} · Job Zone ${data.target.job_zone}<//></div>
            <p class="headline">
              You already have <b>${data.already_held_count}</b> of the ${data.required_total} skills this job uses.
              ${must.length
                ? html` <b class="e">${must.length} must-have${must.length === 1 ? "" : "s"}</b> still to learn.`
                : html` <b class="h">You have every must-have.</b>`}
            </p>
            <${Figure}>held ${data.already_held_count} · essential ${data.missing_essential_count} · desirable ${data.missing_desirable_count}<//>
          </div>
          ${data.message
            ? html`<div class="empty"><div class="big">🎉</div>${data.message}</div>`
            : html`
              ${must.length > 0 && html`
                <h4 class="sect e">Must-haves <span>— the job depends on these</span></h4>
                <div class="rows">${must.map((m) => html`<${SkillRow} key=${m.element_id} m=${m} />`)}</div>`}
              ${nice.length > 0 && html`
                <h4 class="sect">Nice to have <span>— they help, but you can start without them</span></h4>
                <div class="rows">${niceShown.map((m) => html`<${SkillRow} key=${m.element_id} m=${m} />`)}</div>
                ${nice.length > 5 && html`
                  <button class="more" onClick=${() => setAll(!all)}>
                    ${all ? "Show fewer" : `Show all ${nice.length} nice-to-haves`}</button>`}`}
              <details class="why">
                <summary>How do we decide what's a must-have?</summary>
                Job analysts at O*NET rated how important each skill is for this job. The ones rated
                highest are must-haves.
                <${Figure}>Essential = O*NET importance ≥ ${data.threshold} on its 1–5 scale.<//>
              </details>`}
          <p class="prov">${data.target.source_dataset}${dates.length ? ` · ratings dated ${dates.join(", ")}` : ""}</p>`;
      })()}
    <//>`;
}

// ---------- step 5 : pathway ----------

function StepPathway({ profileId, onOpen }) {
  const { data, error, loading } = useFetch(`/profiles/${profileId}/pathway`);
  return html`
    <${Head} kicker="Your route" fr="FR-08" title="How do you get there?" />
    <${Status} loading=${loading} error=${error}>
      ${data && html`
        <p class="sub">${data.intermediate_steps} related jobs that build toward ${data.target.title.toLowerCase()},
          starting with the one closest to what you can already do.</p>
        <div class="steps">
          ${data.steps.map((s, i) => html`
            <div key=${s.soc_code} class=${"step" + (s.is_target ? " target-step" : "")}>
              <div class="rail">
                <span class="dot">${s.step}</span>
                ${i < data.steps.length - 1 && html`<span class="rline"></span>`}
              </div>
              <div class="sbody">
                <div class="sh">
                  <h4><button class="tl" onClick=${() => onOpen(s)}>${s.title}</button></h4>
                  ${s.is_target && html`<span class="pill">Your goal</span>`}
                </div>
                <div class="zn">${s.preparation.label}<${Figure}> · Zone ${s.job_zone}<//></div>
                ${s.focus.slice(0, 4).map((f) => html`
                  <div key=${f.element_id} class="fs">
                    <span class="n">${f.name}</span>
                    ${f.badge && html`<span class=${"bdg " + f.badge}>${f.badge === "new" ? "New to you" : "Use it more"}</span>`}
                    <${Figure}>${f.badge === "deeper" ? `${f.from.toFixed(2)} → ${f.to.toFixed(2)}` : f.importance.toFixed(2)}<//>
                  </div>`)}
              </div>
            </div>`)}
        </div>
        <p class="basis"><b>New to you</b> — a skill you haven't got yet. <b>Use it more</b> — you have it, but this job
          needs more of it than the step before. Each step is a job O*NET's experts list as related to your goal.
          Tap a job to see what it involves.</p>
        <p class="prov">${data.source_dataset}</p>`}
    <//>`;
}

// ---------- my plan : the dashboard after the journey ----------
//
// Not a sixth step. NFR-02 caps the journey at five screens to a displayed
// pathway, and it still is five; this is where the user lands afterwards and
// every time they come back. ADR-0006.

function Meter({ have, total, big }) {
  return html`
    <div class=${"meter" + (big ? " big" : "")} role="progressbar"
         aria-valuemin="0" aria-valuemax=${total} aria-valuenow=${have}>
      ${Array.from({ length: total }, (_, i) => html`<span key=${i} class=${i < have ? "on" : ""}></span>`)}
    </div>`;
}

function Readiness({ r }) {
  const what = r.basis === "essential" ? "must-have skills" : `most important skills`;
  const names = r.missing.map((m) => m.name);
  const list = names.length <= 2 ? names.join(" and ")
    : `${names.slice(0, 2).join(", ")} and ${names.length - 2} more`;
  return html`
    <div class="ready">
      <p class="big-count"><b>${r.have}</b> of ${r.total} <span>${what}</span></p>
      <${Meter} have=${r.have} total=${r.total} big />
      <p class="ready-line">${r.ready
        ? html`<b class="h">You have everything this job depends on.</b> Keep building the rest, or aim higher.`
        : html`Learn <b>${list}</b> to have every one.`}</p>
      <div class="overall">
        <span>${r.overall_have} of ${r.overall_total} skills this job uses</span>
        <span class="thin"><i style=${{ width: `${(r.overall_have / r.overall_total) * 100}%` }}></i></span>
      </div>
      ${r.basis !== "essential" && html`<p class="note">This job has no single must-have skill, so we count its five most important.</p>`}
    </div>`;
}

function PlanSkill({ k, status, busy, onSet }) {
  return html`
    <div class=${"ps" + (status === "learning" ? " learning" : "") + (k.classification === "essential" ? " ess" : "")}>
      <div class="ps-t">
        <b>${k.name}</b>
        <span>${k.description}</span>
      </div>
      <div class="ps-a">
        ${status === "learning"
          ? html`
            <button class="btn ok" disabled=${busy} onClick=${() => onSet(k, "held")}>${Icon.check} I can do this now</button>
            <button class="btn ghost" disabled=${busy} onClick=${() => onSet(k, null)}>Stop</button>`
          : html`
            <button class="btn" disabled=${busy} onClick=${() => onSet(k, "learning")}>Start learning</button>
            <button class="btn ghost" disabled=${busy} onClick=${() => onSet(k, "held")}>I can already</button>`}
      </div>
    </div>`;
}

function Plan({ profileId, onOpen, onJourney, onStartOver, onSignOut, onUnlock, children }) {
  const [rev, setRev] = useState(0);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);
  const [moreNice, setMoreNice] = useState(false);
  const prof = useFetch(`/profiles/${profileId}`, rev);
  const gap = useFetch(`/profiles/${profileId}/gap`, rev);
  const route = useFetch(`/profiles/${profileId}/pathway`, rev);

  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 3200); return () => clearTimeout(t); }, [toast]);

  async function setStatus(k, status) {
    setBusy(true);
    try {
      const res = status
        ? await api.put(`/profiles/${profileId}/skills/${k.element_id}`, { status })
        : await api.del(`/profiles/${profileId}/skills/${k.element_id}`);
      if (status === "held" && onUnlock && isUnlock(res.changes)) onUnlock({ name: k.name, status, changes: res.changes });
      else setToast(status === "held" ? `${k.name} added to your skills.`
        : status === "learning" ? `Working on ${k.name}.` : `${k.name} moved back to your list.`);
      setRev((n) => n + 1);
    } catch (e) {
      setToast(`Couldn't save that: ${e.message}`);
    } finally {
      setBusy(false);
    }
  }

  const first = prof.data && gap.data && route.data;
  if (!first) {
    const err = prof.error || gap.error || route.error;
    return html`<div class="pane plan">${err ? html`<div class="banner">${err}</div>` : html`<p class="loading">Loading your plan…</p>`}</div>`;
  }
  const p = prof.data, g = gap.data, rt = route.data, r = p.readiness;
  const status = Object.fromEntries(p.skills.map((k) => [k.element_id, k.status]));
  const learning = g.missing.filter((m) => status[m.element_id] === "learning");
  const must = g.missing.filter((m) => m.classification === "essential" && !status[m.element_id]);
  const nice = g.missing.filter((m) => m.classification !== "essential" && !status[m.element_id]);
  const have = p.skills.filter((k) => k.status === "held");
  // Ready for the goal itself? Then the goal is the answer, not a stepping stone.
  const goal = rt.steps[rt.steps.length - 1];
  const next = goal.ready ? goal : rt.steps.find((st) => !st.ready);

  return html`
    <div class="pane plan">
      ${PRESENTER && html`<p class="kicker">My plan · dashboard · ADR-0005 · ADR-0006</p>`}
      <h2 class="hello">${p.display_name ? `Hi ${p.display_name}` : "Your plan"}</h2>

      <section class="goal">
        <span class="lbl">Your goal</span>
        <h2><button class="tl" onClick=${() => onOpen(p.target)}>${p.target.title}</button></h2>
        <span class="meta">${p.target.preparation.label}<${Figure}> · ${p.target.soc_code}<//></span>
        <${Readiness} r=${r} />
      </section>

      <section class="card">
        <h3 class="ch">Your route</h3>
        <div class="mini-route">
          ${rt.steps.map((st) => html`
            <button key=${st.soc_code} onClick=${() => onOpen(st)}
                    class=${"mr" + (st.ready ? " done" : "") + (st === next ? " next" : "") + (st.is_target ? " goal" : "")}>
              <span class="mdot">${st.ready ? Icon.check : st.step}</span>
              <span class="mt">${st.title}</span>
            </button>`)}
        </div>
        <div class="nextbox">
          <span class="lbl">${next.is_target ? (next.ready ? "Ready for your goal" : "Next: your goal") : `Next: step ${next.step}`}</span>
          <b>${next.title}</b>
          ${next.ready
            ? html`<p>You have every skill this job depends on. The steps before it are optional now.</p>`
            : html`<p>To be ready: ${next.ready_missing.map((m) => m.name).join(", ")}.</p>`}
        </div>
        <p class="note route-note">Your route updates as your skills grow — the job closest to what you can do comes first.</p>
        <button class="more" onClick=${() => onJourney(4, p)}>See the whole route →</button>
      </section>

      ${children}

      <section class="card">
        <h3 class="ch">Skills to work on</h3>
        ${learning.length > 0 && html`
          <h4 class="sect">Working on now</h4>
          ${learning.map((k) => html`<${PlanSkill} key=${k.element_id} k=${k} status="learning" busy=${busy} onSet=${setStatus} />`)}`}
        ${must.length > 0 && html`
          <h4 class="sect e">Must-haves <span>— the job depends on these</span></h4>
          ${must.map((k) => html`<${PlanSkill} key=${k.element_id} k=${k} busy=${busy} onSet=${setStatus} />`)}`}
        ${nice.length > 0 && html`
          <h4 class="sect">Nice to have</h4>
          ${(moreNice ? nice : nice.slice(0, 3)).map((k) => html`<${PlanSkill} key=${k.element_id} k=${k} busy=${busy} onSet=${setStatus} />`)}
          ${nice.length > 3 && html`<button class="more" onClick=${() => setMoreNice(!moreNice)}>
            ${moreNice ? "Show fewer" : `Show all ${nice.length}`}</button>`}`}
        ${g.missing.length === 0 && html`<p class="note">Nothing left to learn for this job. Time to aim higher?</p>`}
        <details class="have">
          <summary>Skills you have (${have.length})</summary>
          ${have.map((k) => html`
            <div key=${k.element_id} class="hv">
              <span class="mk">${Icon.check}</span><span class="n">${k.name}</span>
              <button class="undo" aria-label=${`Remove ${k.name}`} disabled=${busy} onClick=${() => setStatus(k, null)}>${Icon.undo}</button>
            </div>`)}
        </details>
      </section>

      <div class="plan-actions">
        <button class="btn" onClick=${() => onJourney(2, p)}>Change my goal</button>
        <button class="btn ghost" onClick=${() => onJourney(1, p)}>Update my skills</button>
      </div>

      <section class="codecard">
        <span class="lbl">Your plan code${PRESENTER ? " · ADR-0008" : ""}</span>
        <b class="code mono">${p.plan_code}</b>
        <p>Use it to open this plan on another phone or computer. Anyone with the code can see
          your plan, so share it only with people you trust — a teacher, a parent, a counsellor.</p>
      </section>
      <div class="plan-links">
        <button class="link" onClick=${onSignOut}>Sign out on this device</button>
        <button class="link" onClick=${onStartOver}>Start over from scratch</button>
      </div>
      <p class="prov">${rt.source_dataset}</p>
      ${toast && html`<div class="toast" role="status">${toast}</div>`}
    </div>`;
}

