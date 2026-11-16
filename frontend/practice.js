/* SAYCEP — interview practice (module 5, ADR-0015, ADR-0024).
 *
 * One question at a time for the user's goal; type an answer, get a
 * checklist with tips. Guidance, not a score. Answers stay in this page
 * and are never sent anywhere but the feedback call, which keeps nothing.
 * Change the answer and check again: the page shows what improved.
 */

// Sentence starters for the three parts of a story, shown for whichever is missing.
const STARTERS = {
  situation: ["Situation", "“Last year at school…”, “One weekend at home…”, “When I worked at…”"],
  action: ["Action", "“I checked…”, “I fixed…”, “I showed them how to…”"],
  result: ["Result", "“In the end…”, “As a result…”, “It worked, and I learned…”"],
};

function changeLine(prev, now) {
  const diff = now.met - prev.met;
  const gained = now.items.filter((it) => it.ok && (prev.items.find((p) => p.key === it.key) || {}).ok === false);
  return html`
    <p class="retry"><b>${prev.met} of ${prev.of}</b> <span aria-hidden="true">→</span><span class="sr-only"> then </span> <b>${now.met} of ${now.of}</b>
      ${diff > 0 ? html` <span class="up">+${diff}</span>` : diff < 0 ? html` <span class="down">${diff}</span>` : html` <span>no change</span>`}
      ${gained.length > 0 && html`<span class="gained">. Now there: ${gained.map((g) => g.label.replace(/\*/g, "")).join("; ")}.</span>`}</p>`;
}

function PracticePage({ profileId }) {
  const qs = useFetch(`/interview/questions?profile_id=${profileId}`);
  const [i, setI] = useState(0);
  const [answers, setAnswers] = useState({});
  const [fb, setFb] = useState({});
  const [prevFb, setPrevFb] = useState({});     // the feedback before the latest check, per question
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (!qs.data) return html`<div class="page"><div class="page-body"><${Status} loading=${qs.loading} error=${qs.error} /></div></div>`;
  const list = qs.data.questions, q = list[i], a = answers[q.id] || "", f = fb[q.id];

  async function check() {
    setBusy(true); setError(null);
    try {
      const r = await api.post("/interview/feedback", {
        answer: a, skill_element_id: q.skill ? q.skill.element_id : null, tool: q.tool || null });
      setPrevFb((x) => ({ ...x, [q.id]: fb[q.id] || null }));
      setFb((x) => ({ ...x, [q.id]: r }));
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  return html`
    <div class="page">
      <div class="page-body">
        <p class="kicker">Interview practice · ${qs.data.title}${PRESENTER ? " · ADR-0015" : ""}</p>
        <div class="qdots" role="group" aria-label=${`Question ${i + 1} of ${list.length}`}>
          ${list.map((x, k) => html`<button key=${x.id} aria-label=${`Question ${k + 1}${fb[x.id] ? ", answered" : ""}`} aria-current=${k === i ? "step" : undefined}
            class=${"qdot" + (k === i ? " on" : "") + (fb[x.id] ? " done" : "")} onClick=${() => setI(k)}>${k + 1}</button>`)}
        </div>
        <h3 class="sheet-title qtext" id="qtext">${q.text}</h3>
        ${q.skill && html`<p class="note">This question is about <b>${q.skill.name}</b>.</p>`}
        ${q.tool && html`<p class="note">This is a technical question about <b>${q.tool}</b>, a tool or software this job uses.</p>`}
        <details class="why star">
          <summary>How to answer: situation, action, result</summary>
          <b>Situation</b> — when and where it happened (school, home, church, sport or work all count).
          <b>Action</b> — what <i>you</i> did, using "I".
          <b>Result</b> — how it turned out, or what you learned. Aim for about 40 to 250 words.
        </details>
        <textarea id="answer" class="cvbox" aria-labelledby="qtext" rows="7" maxLength="5000" value=${a}
                  placeholder="Type your answer as you would say it…"
                  onInput=${(e) => setAnswers((x) => ({ ...x, [q.id]: e.target.value }))}></textarea>
        <div class="plan-actions">
          <button class="btn" disabled=${busy || a.trim().length < 3} onClick=${check}>${busy ? "Reading…" : "Get feedback"}</button>
          ${i < list.length - 1
            ? html`<button class="btn ghost" onClick=${() => setI(i + 1)}>Next question</button>`
            : html`<button class="btn ghost" onClick=${() => setI(0)}>Back to the first</button>`}
        </div>
        ${error && html`<div class="banner">${error}</div>`}
        <div aria-live="polite">${f && html`
          <div class="goalchg fbk">
            <p class="big-count"><b>${f.met}</b> of ${f.of} <span>things interviewers listen for</span></p>
            ${prevFb[q.id] && changeLine(prevFb[q.id], f)}
            <ul class="sk">${f.items.map((it) => html`
              <li key=${it.key} class=${it.ok ? "have" : ""}><span class="mk" role="img" aria-label=${it.ok ? "Done" : "Not yet"}>${it.ok ? Icon.check : null}</span>
                <span><b>${it.label.replace(/\*/g, "")}</b>${it.tip ? html`<br /><span class="tip">${it.tip}</span>` : ""}</span></li>`)}
            </ul>
            ${f.items.some((it) => !it.ok && STARTERS[it.key]) && html`
              <div class="starters"><b>Ways to start the missing parts</b>
                ${f.items.filter((it) => !it.ok && STARTERS[it.key]).map((it) => html`
                  <p key=${it.key}><i>${STARTERS[it.key][0]}:</i> ${STARTERS[it.key][1]}</p>`)}
                <p class="note">Edit your answer above and tap Get feedback again to see what improves.</p>
              </div>`}
          </div>`}</div>
        <p class="prov">${qs.data.note} Questions from O*NET 29.0's skills and tasks for this job; feedback rules written by us.</p>
      </div>
    </div>`;
}

function PracticeCard({ onOpen }) {
  return html`
    <section class="card">
      <h3 class="ch">Practise for an interview</h3>
      <p class="note">Questions for your goal, with tips on each answer. Nothing you type is saved.</p>
      <button class="btn full" onClick=${onOpen}>Start practising</button>
    </section>`;
}
