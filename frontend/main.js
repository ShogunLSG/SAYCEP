/* SAYCEP — the app shell. Loaded last, after every screen's file.
 *
 *   welcome ──► journey (five screens, NFR-02) ──► app (tabs)
 *      ▲  plan code ──────────────────────────────────┘
 *
 * The journey is the onboarding. Once a plan is saved, the app is a set of
 * tabs, and pages (a job, a skill) are pushed over a tab and popped with the
 * back arrow. docs/plans/full-app.md, ADR-0006, ADR-0008.
 */

const CTA = ["Continue", "Find roles that fit", "See what's missing", "Show me the route", "Save as my plan"];

// Tabs are listed only once they exist: an empty tab reads as abandoned work.
const TABS = [
  { key: "home", label: "Home", icon: svg(html`<path d="M4 11l8-7 8 7v8a1 1 0 01-1 1h-4v-6h-6v6H5a1 1 0 01-1-1z" />`, 2) },
  { key: "explore", label: "Explore", icon: svg(html`<circle cx="12" cy="12" r="9" /><path d="M15.5 8.5l-2 5-5 2 2-5z" />`, 2) },
  { key: "skills", label: "Skills", icon: svg(html`<path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z" />`, 2) },
  { key: "me", label: "Me", icon: svg(html`<circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />`, 2) },
];

function App() {
  const [view, setView] = useState(() => (saved.get() ? "boot" : "welcome")); // boot | welcome | journey | app
  const [tab, setTab] = useState("home");
  const [stack, setStack] = useState([]);       // pages over a tab: { kind: "job", soc_code, title }
  const [rev, setRev] = useState(0);            // bumped when the goal changes, so Home refetches
  const [skillRev, setSkillRev] = useState(0);  // bumped on any skill change, for Skills and skill pages
  const [unlock, setUnlock] = useState(null);   // { name, status, changes } -- the unlock card
  const [savedRev, setSavedRev] = useState(0);  // bumped when a job is saved or unsaved
  const [printing, setPrinting] = useState(false);
  const [name, setName] = useState("");         // from the welcome screen; sent with POST /profiles
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState("fwd");
  const [type, setType] = useState(null);
  const [held, setHeld] = useState(() => new Set());
  const [profile, setProfile] = useState(null); // { id, key }
  const [target, setTarget] = useState(null);   // { soc_code, title, job_zone }
  const [sheet, setSheet] = useState(null);     // { soc_code, canAim } -- the journey's job panel
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const openers = useRef([]);                   // the element that opened each pushed page
  const lastView = useRef(view);

  // A new journey step, or arriving in the app, moves focus to the new
  // heading so a screen reader announces the change (not on first load).
  useEffect(() => {
    const from = lastView.current;
    lastView.current = view;
    if (view === "journey") focusWhenReady(".pane .title");
    else if (view === "app" && from !== "boot") focusWhenReady(".hello", ".tabbar .tb");
  }, [view, step]);

  // A profile is created from a type and a skill set. Change either and the
  // next continue creates a fresh one; the saved plan then follows the new id.
  const keyOf = (t, ids) => `${t}|${[...ids].sort().join(",")}`;
  const profileKey = keyOf(type, held);

  /** Load a stored profile into the app's state, so going back into the
   *  journey from the plan edits the same profile rather than a copy. */
  function hydrate(p) {
    const ids = p.skills.filter((k) => k.status === "held").map((k) => k.element_id);
    setType(p.profile_type);
    setHeld(new Set(ids));
    setProfile({ id: p.profile_id, key: keyOf(p.profile_type, ids) });
    setTarget(p.target && { soc_code: p.target.soc_code, title: p.target.title, job_zone: p.target.job_zone });
  }

  /** A profile with a goal opens the app; one without resumes the journey at step 3. */
  function open(p) {
    hydrate(p);
    if (p.target) { setView("app"); setTab("home"); setStack([]); }
    else { setView("journey"); setDir("fwd"); setStep(2); }
  }

  // Coming back: reopen the saved plan, or quietly show the welcome screen.
  useEffect(() => {
    if (view !== "boot") return;
    api.get(`/profiles/${saved.get()}`).then(open, () => { saved.clear(); setView("welcome"); });
  }, []);

  async function resume(code) {
    const r = await api.post("/plans/resume", { plan_code: code });
    saved.set(r.profile_id);
    open(await api.get(`/profiles/${r.profile_id}`));
  }

  function reset() {
    setType(null); setHeld(new Set()); setProfile(null); setTarget(null);
    setStack([]); setTab("home"); setSheet(null); setStep(0); setDir("bwd");
  }
  function startOver() { saved.clear(); reset(); setName(""); setView("welcome"); }
  function signOut() { saved.clear(); reset(); setView("welcome"); }

  const go = (n) => { setDir(n > step ? "fwd" : "bwd"); setError(null); setSheet(null); setStep(n); };

  function toggle(id) {
    setHeld((prev) => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  }

  function enterJourney(n, p) { hydrate(p); setView("journey"); setDir("bwd"); setSheet(null); setStep(n); }

  async function advance() {
    setError(null); setBusy(true);
    try {
      if (step === 4) {
        saved.set(profile.id); setSheet(null); setStack([]); setTab("home"); setRev((r) => r + 1); setView("app");
        return;
      }
      if (step === 1 && (!profile || profile.key !== profileKey)) {
        const [oldType, oldIds] = profile ? profile.key.split("|") : [null, ""];
        if (profile && oldType === type && saved.get() === profile.id) {
          // Editing a saved plan's skills: change that profile in place, so its
          // target, plan code and "working on it" marks survive.
          const before = new Set(oldIds ? oldIds.split(",") : []);
          await Promise.all([
            ...[...held].filter((id) => !before.has(id)).map((id) =>
              api.put(`/profiles/${profile.id}/skills/${id}`, { status: "held" })),
            ...[...before].filter((id) => !held.has(id)).map((id) =>
              api.del(`/profiles/${profile.id}/skills/${id}`)),
          ]);
          setProfile({ id: profile.id, key: profileKey });
        } else {
          const d = await api.post("/profiles", { profile_type: type, skills: [...held], display_name: name || null });
          setProfile({ id: d.profile_id, key: profileKey });
          setTarget(null);
        }
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

  async function makeGoal(occ) {
    await api.put(`/profiles/${profile.id}/target`, { soc_code: occ.soc_code });
    setTarget({ soc_code: occ.soc_code, title: occ.title, job_zone: occ.job_zone });
    setRev((r) => r + 1); setStack([]); setTab("home");
  }

  /** Skill changes from the Skills tab and skill pages; Home has its own. */
  async function setSkill(k, status) {
    const res = status
      ? await api.put(`/profiles/${profile.id}/skills/${k.element_id}`, { status })
      : await api.del(`/profiles/${profile.id}/skills/${k.element_id}`);
    setSkillRev((r) => r + 1); setRev((r) => r + 1);
    // Keep the journey's copy of the skills in step, so "Update my skills"
    // opens on what the profile holds now ("learning" is not held).
    const next = new Set(held);
    status === "held" ? next.add(k.element_id) : next.delete(k.element_id);
    setHeld(next);
    setProfile((p) => p && { ...p, key: keyOf(type, next) });
    if (status === "held" && isUnlock(res.changes)) setUnlock({ name: k.name, status, changes: res.changes });
  }

  // Focus follows navigation: a pushed page puts focus on its heading, and
  // Back returns it to whatever opened the page (WCAG 2.4.3, ADR-0016).
  const push = (page) => {
    openers.current.push(document.activeElement);
    setStack((s) => [...s, page]);
    setTimeout(() => focusWhenReady(".page .sheet-title", ".top .back"), 60);
  };
  const pop = () => {
    const opener = openers.current.pop();
    setStack((s) => s.slice(0, -1));
    setTimeout(() => (opener && opener.isConnected ? opener.focus() : focusWhenReady(".page .sheet-title, .tabpane h2, .hello")), 60);
  };

  if (view === "boot") return html`<div class="app"><p class="loading">Loading…</p></div>`;

  if (view === "welcome") return html`<${Welcome}
    onStart=${(n) => { setName(n); reset(); setDir("fwd"); setView("journey"); }}
    onResume=${resume} />`;

  const sheetEl = sheet && html`<${RoleSheet} key=${sheet.soc_code} soc=${sheet.soc_code} profileId=${profile && profile.id}
    isTarget=${target && target.soc_code === sheet.soc_code}
    onAim=${sheet.canAim ? (occ) => setTarget({ soc_code: occ.soc_code, title: occ.title, job_zone: occ.job_zone }) : null}
    onClose=${() => setSheet(null)} />`;

  // ---------- the app: tabs, with pages pushed over them ----------
  if (view === "app") {
    const page = stack[stack.length - 1];
    const openJob = (o) => push({ kind: "job", soc_code: o.soc_code, title: o.title });
    const openSkill = (k) => push({ kind: "skill", element_id: k.element_id });
    const openCompare = (socs) => push({ kind: "compare", socs });
    const openCv = () => push({ kind: "cv" });
    const openPractice = () => push({ kind: "practice" });
    const title = page ? "" : TABS.find((t) => t.key === tab).label;
    // The tab stays mounted under any pushed page, so coming back finds the
    // search, filter and scroll position exactly as they were.
    let pageEl = null;
    if (page && page.kind === "job") {
      pageEl = html`<${JobPage} key=${page.soc_code} soc=${page.soc_code} profileId=${profile.id}
                   goalSoc=${target && target.soc_code} onOpenJob=${openJob} onMakeGoal=${makeGoal}
                   onSavedChange=${() => setSavedRev((r) => r + 1)} />`;
    } else if (page && page.kind === "compare") {
      pageEl = html`<${ComparePage} key=${page.socs.join()} profileId=${profile.id} socs=${page.socs} onOpen=${openJob} />`;
    } else if (page && page.kind === "practice") {
      pageEl = html`<${PracticePage} profileId=${profile.id} />`;
    } else if (page && page.kind === "cv") {
      pageEl = html`<${CvPage} profileId=${profile.id} onSet=${setSkill} onOpenSkill=${openSkill} />`;
    } else if (page && page.kind === "skill") {
      pageEl = html`<${SkillPage} key=${page.element_id} elementId=${page.element_id} profileId=${profile.id}
                   rev=${skillRev} onSet=${setSkill} onOpenJob=${openJob} />`;
    }
    let tabEl;
    if (tab === "me") {
      tabEl = html`<${MeTab} profileId=${profile.id} rev=${rev + skillRev} onNameSaved=${() => setRev((r) => r + 1)}
                   onPrint=${() => setPrinting(true)} onJourney=${enterJourney}
                   onSignOut=${signOut} onStartOver=${startOver} />`;
    } else if (tab === "skills") {
      tabEl = html`<${SkillsTab} profileId=${profile.id} rev=${skillRev} onOpenSkill=${openSkill} onOpenCv=${openCv} />`;
    } else if (tab === "explore") {
      tabEl = html`<div class="pane tabpane"><${StepExplore} profileId=${profile.id} type=${type} target=${target}
                   onOpen=${openJob}
                   head=${html`<p class="sub tight">Find jobs by how well they fit you, how much training
                     they take, or any name you know them by.</p>`} /></div>`;
    } else {
      tabEl = html`<${Plan} key=${rev} profileId=${profile.id} onOpen=${openJob}
                   onJourney=${enterJourney} onStartOver=${startOver} onSignOut=${signOut}
                   onUnlock=${(u) => { setUnlock(u); setSkillRev((r) => r + 1); }}
                   onChanged=${() => setSkillRev((r) => r + 1)}>
                 <${SavedJobs} profileId=${profile.id} rev=${savedRev + skillRev} onOpen=${openJob} onCompare=${openCompare} />
                 <${ProgressHistory} profileId=${profile.id} rev=${skillRev} />
                 <${CvCard} onOpen=${openCv} />
                 <${PracticeCard} onOpen=${openPractice} />
               <//>`;
    }
    const body = html`<div class="tabhost" inert=${page ? "" : undefined}>${tabEl}</div>${pageEl}`;
    return html`
      <div class="app">
        <div class="top">
          <div class="toprow">
            ${page
              ? html`<button class="back" aria-label="Back" onClick=${pop}>${Icon.back}</button>`
              : html`<span class="plan-title">${title}</span>`}
            <span class="steplabel"></span>
            <span class="brand">SAYCEP</span>
          </div>
        </div>
        <div class="body">${body}</div>
        <nav class="tabbar" aria-label="Main">
          ${TABS.map((t) => html`
            <button key=${t.key} class=${"tb" + (tab === t.key && !page ? " on" : "")}
                    aria-current=${tab === t.key ? "page" : undefined}
                    onClick=${() => { setTab(t.key); setStack([]); openers.current = []; }}>
              ${t.icon}<span>${t.label}</span>
            </button>`)}
        </nav>
        ${unlock && html`<${UnlockCard} u=${unlock} onOpenJob=${openJob} onClose=${() => setUnlock(null)} />`}
      </div>
      ${printing && html`<${PrintPlan} profileId=${profile.id}
        onReady=${() => setTimeout(() => { window.print(); setPrinting(false); }, 50)} />`}`;
  }

  // ---------- the journey ----------
  const ready = [type !== null, held.size > 0, target !== null, true, true][step];
  const inPlan = !!saved.get() && profile && target;

  const panes = [
    html`<${StepStart} type=${type} onPick=${setType} />`,
    html`<${StepSkills} held=${held} onToggle=${toggle} />`,
    html`<${StepExplore} profileId=${profile && profile.id} type=${type} target=${target}
                         onOpen=${(o) => setSheet({ soc_code: o.soc_code, canAim: true })} />`,
    html`<${StepGap} profileId=${profile && profile.id} />`,
    html`<${StepPathway} profileId=${profile && profile.id}
                         onOpen=${(o) => setSheet({ soc_code: o.soc_code, canAim: false })} />`,
  ];

  return html`
    <div class="app">
      <div class="top">
        <div class="toprow">
          <button class="back" aria-label="Back" disabled=${busy}
                  onClick=${() => (step === 0 ? (inPlan ? setView("app") : setView("welcome")) : go(step - 1))}>${Icon.back}</button>
          <span class="steplabel">Step <b>${step + 1}</b> of 5</span>
          ${inPlan
            ? html`<button class="toplink" onClick=${() => { setRev((r) => r + 1); setView("app"); }}>My plan</button>`
            : html`<span class="brand">SAYCEP</span>`}
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

      ${sheetEl}
    </div>`;
}

ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
