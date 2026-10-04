/* SAYCEP — the interest quiz (slice 4, ADR-0011).
 *
 * For the school-leaver who doesn't know job names yet: twelve "would you
 * enjoy…" statements, matched against O*NET's interest profile for every job.
 * The statements are ours and the screen says it's a simplified version.
 */

function InterestQuiz({ profileId, maxZone, onOpen }) {
  const quiz = useFetch("/interests/quiz");
  const [ans, setAns] = useState({});          // question id -> 0 | 1 | 2
  const [asked, setAsked] = useState(false);
  const done = quiz.data && Object.keys(ans).length === quiz.data.questions.length;
  const totals = {};
  if (quiz.data) quiz.data.questions.forEach((q) => { totals[q.area] = (totals[q.area] || 0) + (ans[q.id] || 0); });
  const q = "RIASEC".split("").map((x) => `${x.toLowerCase()}=${totals[x] || 0}`).join("&");
  const res = useFetch(asked && done
    ? `/interests/match?${q}&limit=10${maxZone ? `&max_job_zone=${maxZone}` : ""}${profileId ? `&profile_id=${profileId}` : ""}`
    : null);

  if (!quiz.data) return html`<${Status} loading=${quiz.loading} error=${quiz.error} />`;

  if (asked && done) return html`
    <p class="note">${quiz.data.note}</p>
    <${Status} loading=${res.loading && !res.data} error=${res.error}>
      ${res.data && html`
        ${res.data.message
          ? html`<div class="empty">${res.data.message}</div>`
          : html`
            <p class="fit">You lean towards <b>${res.data.your_areas.map((a) => a.name).join(" and ")}</b>.
              These jobs share that shape${maxZone ? " — only ones that don't need a degree" : ""}:</p>
            <div class="list">
              ${res.data.results.map((j) => html`
                <button key=${j.soc_code} class="occ" onClick=${() => onOpen(j)}>
                  <span class="t">${j.title}
                    <span class="meta"><b class="match">${j.fit}</b>${j.skill_match ? ` · skills: ${j.skill_match.toLowerCase()}` : ""}${" · "}${j.preparation.label}<${Figure}> · r=${j.correlation}<//></span>
                    <span class="aka">${j.areas.join(" · ")} · interest profile dated ${j.source_date}</span></span>
                  <span class="chev">›</span>
                </button>`)}
            </div>
            <${Prov} dataset=${res.data.dataset} />`}`}
    <//>
    <button class="btn full" onClick=${() => setAsked(false)}>Change my answers</button>`;

  return html`
    <p class="note">Twelve quick questions. There are no wrong answers — go with your gut.</p>
    <div class="quiz">
      ${quiz.data.questions.map((qq) => html`
        <div key=${qq.id} class=${"qz" + (ans[qq.id] != null ? " done" : "")}>
          <p>${qq.text}</p>
          <div class="qz-a" role="radiogroup" aria-label=${qq.text}>
            ${quiz.data.answers.map((o) => html`
              <button key=${o.value} role="radio" aria-checked=${ans[qq.id] === o.value}
                      class=${"qa" + (ans[qq.id] === o.value ? " on" : "")}
                      onClick=${() => setAns((a) => ({ ...a, [qq.id]: o.value }))}>${o.label}</button>`)}
          </div>
        </div>`)}
    </div>
    <button class="cta" disabled=${!done} onClick=${() => setAsked(true)}>
      ${done ? "Show jobs that fit my interests" : `${Object.keys(ans).length} of ${quiz.data.questions.length} answered`}</button>
    <p class="fine">${quiz.data.note}</p>`;
}
