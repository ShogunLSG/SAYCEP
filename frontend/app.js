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
};

/** Fetch whenever `path` changes; a null path fetches nothing. */
function useFetch(path) {
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
  }, [path]);
  return state;
}

// ---------- small pieces ----------

const svg = (d, w = 2.2) => html`
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth=${w}
       strokeLinecap="round" strokeLinejoin="round">${d}</svg>`;
const Icon = {
  back: svg(html`<path d="M15 18l-6-6 6-6" />`),
  arrow: svg(html`<path d="M5 12h14M13 6l6 6-6 6" />`, 2.4),
  check: svg(html`<path d="M5 13l4 4L19 7" />`, 3.2),
  search: svg(html`<circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" />`, 2),
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

function Ring({ score }) {
  const r = 14, c = 2 * Math.PI * r;
  const s = Math.max(0, Math.min(1, score)); // mean-centred cosine can dip below 0
  return html`
    <span class="ring" title="Skill similarity">
      <svg width="36" height="36">
        <circle class="bg" cx="18" cy="18" r=${r} />
        <circle class="fg" cx="18" cy="18" r=${r}
                strokeDasharray=${c} strokeDashoffset=${c * (1 - s)} />
      </svg>
      <span>${Math.round(s * 100)}%</span>
    </span>`;
}

function OccRow({ occ, picked, onPick, score }) {
  return html`
    <button class=${"occ" + (picked ? " on" : "")} aria-pressed=${picked}
            onClick=${() => onPick(occ)}>
      ${score != null && html`<${Ring} score=${score} />`}
      <span class="t">${occ.title}
        <span class="meta mono">${occ.soc_code} · Job Zone ${occ.job_zone}</span>
      </span>
      <span class="tick">${Icon.check}</span>
    </button>`;
}

const zoneName = (name) => (name || "").replace(/^Job Zone \w+:\s*/, "");

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
  const shown = data ? data.skills.filter((s) => s.name.toLowerCase().includes(q.toLowerCase())) : [];
  return html`
    <${Head} kicker="Your skills" fr="FR-02"
             title="What can you already do?"
             sub="Tap anything that's genuinely true of you. Honest beats modest — this is what your gap is measured against." />
    <${Status} loading=${loading} error=${error}>
      <div class="filter">
        ${Icon.search}
        <input id="skill-filter" placeholder="Filter skills…" autocomplete="off"
               value=${q} onInput=${(e) => setQ(e.target.value)} />
      </div>
      <div class="chips">
        ${shown.map((s) => html`
          <button key=${s.element_id} class=${"chip" + (held.has(s.element_id) ? " on" : "")}
                  aria-pressed=${held.has(s.element_id)} aria-label=${s.name} title=${s.description}
                  onClick=${() => onToggle(s.element_id)}>${s.name}</button>`)}
      </div>
      <p class="count"><b>${held.size}</b> of ${data ? data.total : 35} selected</p>
    <//>`;
}

// ---------- step 3 : explore ----------

function StepExplore({ profileId, type, target, onPick }) {
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
    <${Head} kicker="Your options" fr="FR-03 · FR-04 · FR-05 · FR-06"
             title="Pick something to aim for"
             sub="Tap a role to set it as your target. You can come back and change it." />
    <div class="tabs" role="tablist">
      ${TABS.map(([k, label]) => html`
        <button key=${k} role="tab" aria-selected=${tab === k}
                class=${"tab" + (tab === k ? " on" : "")} onClick=${() => setTab(k)}>${label}</button>`)}
    </div>

    ${tab === "foryou" && html`
      <p class="note">${leaver
        ? "Ranked by how closely your skills match — only roles that don't need a degree."
        : "Ranked by how closely your skills match, across every preparation level."}</p>
      <${Status} loading=${recs.loading} error=${recs.error}>
        ${recs.data && html`<div class="list">
          ${recs.data.recommendations.map((r) => html`
            <${OccRow} key=${r.soc_code} occ=${r} score=${r.score}
                       picked=${isPicked(r)} onPick=${onPick} />`)}
        </div>`}
        ${recs.data && recs.data.message && html`<p class="note">${recs.data.message}</p>`}
      <//>`}

    ${tab === "browse" && html`
      <div class="zones" role="group" aria-label="Preparation level">
        ${[1, 2, 3, 4, 5].map((z) => html`
          <button key=${z} class=${"zone" + (zone === z ? " on" : "")} aria-pressed=${zone === z}
                  onClick=${() => setZone(z)}>Zone ${z}</button>`)}
      </div>
      <${Status} loading=${browse.loading} error=${browse.error}>
        ${browse.data && html`
          <p class="zdesc"><b>${zoneName(browse.data.job_zone.name)}.</b> ${browse.data.job_zone.education}
            ${" "}${browse.data.total} occupations.</p>
          <div class="list">
            ${browse.data.occupations.map((o) => html`
              <${OccRow} key=${o.soc_code} occ=${o} picked=${isPicked(o)} onPick=${onPick} />`)}
          </div>`}
      <//>`}

    ${tab === "search" && html`
      <div class="filter">
        ${Icon.search}
        <input id="occ-search" placeholder="Search 879 occupations — try “electric”" autocomplete="off"
               value=${q} onInput=${(e) => setQ(e.target.value)} />
      </div>
      ${term.length < 2
        ? html`<p class="note">Type at least two letters.</p>`
        : html`<${Status} loading=${search.loading} error=${search.error}>
            ${search.data && html`
              <p class="note">${search.data.message || `${search.data.total} match${search.data.total === 1 ? "" : "es"}`}</p>
              <div class="list">
                ${search.data.occupations.map((o) => html`
                  <${OccRow} key=${o.soc_code} occ=${o} picked=${isPicked(o)} onPick=${onPick} />`)}
              </div>`}
          <//>`}`}

    <p class="prov">Source: O*NET 29.0 (August 2024 release) · U.S. Department of Labor · CC BY 4.0</p>`;
}

// ---------- step 4 : gap ----------

function StepGap({ profileId }) {
  const { data, error, loading } = useFetch(`/profiles/${profileId}/gap`);
  const [all, setAll] = useState(false);
  return html`
    <${Head} kicker="The gap" fr="FR-07 · FR-09" title="What's missing?" />
    <${Status} loading=${loading} error=${error}>
      ${data && (() => {
        const shown = all ? data.missing : data.missing.slice(0, 10);
        const dates = [...new Set(data.missing.map((m) => m.source_date).filter(Boolean))];
        return html`
          <div class="target">
            <h3>${data.target.title}</h3>
            <div class="meta mono">${data.target.soc_code} · Job Zone ${data.target.job_zone} · ${zoneName(data.target.zone_name)}</div>
            <div class="stats">
              <div class="stat h"><b>${data.already_held_count}</b><span>You have</span></div>
              <div class="stat e"><b>${data.missing_essential_count}</b><span>Essential</span></div>
              <div class="stat"><b>${data.missing_desirable_count}</b><span>Desirable</span></div>
            </div>
          </div>
          ${data.message
            ? html`<div class="empty"><div class="big">🎉</div>${data.message}</div>`
            : html`
              <div class="rows">
                ${shown.map((m) => {
                  const ess = m.classification === "essential";
                  return html`
                    <div key=${m.element_id} class=${"row" + (ess ? " ess" : "")}>
                      <span class="nm"><span>${m.name}</span>
                        <span class=${"tag " + (ess ? "e" : "d")}>${ess ? "Essential" : "Desirable"}</span></span>
                      <span class="val mono">${m.importance.toFixed(2)} / ${m.importance_scale_max}</span>
                      <span class="bar"><i style=${{ width: `${(m.importance / m.importance_scale_max) * 100}%` }}></i></span>
                    </div>`;
                })}
              </div>
              ${data.missing.length > 10 && html`
                <button class="more" onClick=${() => setAll(!all)}>
                  ${all ? "Show fewer" : `Show all ${data.missing.length} missing skills`}</button>`}
              <p class="rule">Essential means O*NET rates it ${data.threshold} or above for this job, on its 1–5 importance scale.</p>`}
          <p class="prov">${data.target.source_dataset}${dates.length ? ` · ratings dated ${dates.join(", ")}` : ""}</p>`;
      })()}
    <//>`;
}

// ---------- step 5 : pathway ----------

function StepPathway({ profileId }) {
  const { data, error, loading } = useFetch(`/profiles/${profileId}/pathway`);
  return html`
    <${Head} kicker="Your route" fr="FR-08" title="How do you get there?" />
    <${Status} loading=${loading} error=${error}>
      ${data && html`
        <p class="sub">${data.intermediate_steps} steps, then ${data.target.title.toLowerCase()} itself.</p>
        <div class="steps">
          ${data.steps.map((s, i) => html`
            <div key=${s.soc_code} class=${"step" + (s.is_target ? " target-step" : "")}>
              <div class="rail">
                <span class="dot">${s.step}</span>
                ${i < data.steps.length - 1 && html`<span class="rline"></span>`}
              </div>
              <div class="sbody">
                <div class="sh">
                  <h4>${s.title}</h4><span class="zn">Zone ${s.job_zone}</span>
                  ${s.is_target && html`<span class="pill">Target</span>`}
                </div>
                ${s.focus.slice(0, 4).map((f) => html`
                  <div key=${f.element_id} class="fs">
                    <span class="n">${f.name}</span>
                    ${f.badge && html`<span class=${"bdg " + f.badge}>${f.badge === "new" ? "New" : "Deeper"}</span>`}
                    <span class="v mono">${f.badge === "deeper" ? `${f.from.toFixed(2)} → ${f.to.toFixed(2)}` : f.importance.toFixed(2)}</span>
                  </div>`)}
              </div>
            </div>`)}
        </div>
        <p class="basis"><b>New</b> — you don't have it yet. <b>Deeper</b> — this role asks for more of it than the step before.
          Steps come from O*NET's expert-reviewed list of roles related to your target, ordered from closest to the skills you have now.</p>
        <p class="prov">${data.source_dataset}</p>`}
    <//>`;
}

// ---------- the journey ----------

const CTA = ["Continue", "Find roles that fit", "See what's missing", "Show me the route", "Start again"];

function App() {
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState("fwd");
  const [type, setType] = useState(null);
  const [held, setHeld] = useState(() => new Set());
  const [profile, setProfile] = useState(null); // { id, key }
  const [target, setTarget] = useState(null);   // { soc_code, title, job_zone }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  // A profile is created from a type and a skill set. Change either and the
  // next continue creates a fresh one -- profiles are ephemeral in the demo.
  const profileKey = `${type}|${[...held].sort().join(",")}`;

  const go = (n) => { setDir(n > step ? "fwd" : "bwd"); setError(null); setStep(n); };

  function toggle(id) {
    setHeld((prev) => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  }

  function restart() {
    setType(null); setHeld(new Set()); setProfile(null); setTarget(null); go(0);
  }

  async function advance() {
    if (step === 4) return restart();
    setError(null); setBusy(true);
    try {
      if (step === 1 && (!profile || profile.key !== profileKey)) {
        const d = await api.post("/profiles", { profile_type: type, skills: [...held] });
        setProfile({ id: d.profile_id, key: profileKey });
        setTarget(null);
      }
      if (step === 2) {
        await api.put(`/profiles/${profile.id}/target`, { soc_code: target.soc_code });
      }
      go(step + 1);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const ready = [type !== null, held.size > 0, target !== null, true, true][step];

  const panes = [
    html`<${StepStart} type=${type} onPick=${setType} />`,
    html`<${StepSkills} held=${held} onToggle=${toggle} />`,
    html`<${StepExplore} profileId=${profile && profile.id} type=${type} target=${target} onPick=${setTarget} />`,
    html`<${StepGap} profileId=${profile && profile.id} />`,
    html`<${StepPathway} profileId=${profile && profile.id} />`,
  ];

  return html`
    <div class="app">
      <div class="top">
        <div class="toprow">
          <button class="back" aria-label="Back" disabled=${step === 0 || busy} onClick=${() => go(step - 1)}>${Icon.back}</button>
          <span class="steplabel">Step <b>${step + 1}</b> of 5</span>
          <span class="brand">SAYCEP</span>
        </div>
        <div class="segments" aria-hidden="true">
          ${[0, 1, 2, 3, 4].map((i) => html`<span key=${i} class=${"seg" + (i <= step ? " on" : "")}><i></i></span>`)}
        </div>
      </div>

      <div class="body">
        <div key=${step} class=${"pane " + dir}>${panes[step]}</div>
      </div>

      <div class="foot">
        ${error && html`<div class="banner">${error}</div>`}
        ${step === 2 && html`<p class="picked">${target
          ? html`Target: <b>${target.title}</b>`
          : "No target picked yet"}</p>`}
        <button class="cta" disabled=${!ready || busy} onClick=${advance}>
          ${busy ? "Working…" : CTA[step]}${!busy && step < 4 ? Icon.arrow : null}
        </button>
        ${step === 4 && html`<button class="link" onClick=${() => go(2)}>Try a different target</button>`}
      </div>
    </div>`;
}

ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
