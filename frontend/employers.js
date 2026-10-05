/* SAYCEP — what employers ask for (module 4, ADR-0017).
 *
 * A summary of real job adverts linked to a job by title: US, March–April
 * 2024, all closed. It says so every time it appears. Shown on the job page
 * and, for the goal, as a card on Home. Counts only; no advert text.
 */

function yearsLine(y) {
  if (!y) return null;
  const m = y.median;
  return m <= 1 ? "Experience asked for: usually a year or less."
    : `Experience asked for: usually about ${Math.round(m)} years.`;
}

const STATUS_WORDS = { held: "You have this", learning: "Learning" };

function EmployersAsk({ soc, profileId, focus, onOpenSkill }) {
  const { data, error, loading } = useFetch(`/occupations/${soc}/adverts${profileId ? `?profile_id=${profileId}` : ""}`);
  useEffect(() => {                       // opened from Home: land on this section
    const h = focus && data && document.getElementById("emp-h");
    if (!h) return;
    h.setAttribute("tabindex", "-1");
    h.focus({ preventScroll: true });
    h.scrollIntoView({ block: "start" });
  }, [focus, !!data]);
  const head = html`<h4 class="sect" id="emp-h">What employers ask for${PRESENTER ? " · ADR-0017" : ""}</h4>`;
  if (loading || error) return html`${head}<${Status} loading=${loading} error=${error} />`;
  if (!data.loaded) return html`${head}<p class="note">Job advert data isn't loaded on this copy of SAYCEP.</p>`;
  if (!data.enough) return html`${head}<p class="note">${data.adverts
    ? `Only ${data.adverts} advert${data.adverts === 1 ? "" : "s"} in our data match this job — too few to say what employers ask for.`
    : "No adverts in our data match this job's name, so we can't say what employers ask for."}</p>`;
  return html`
    <section class="emp" aria-labelledby="emp-h">
      ${head}
      <p class="note">From <b>${data.adverts}</b> real adverts for this job in the <b>United States</b>, March–April 2024.
        They've closed — this shows what employers asked for, not jobs to apply for.</p>
      <div class="emp-facts">
        <p><b>${data.entry_words}</b> were open to beginners.<${Figure}> ${data.entry_level}/${data.adverts}<//></p>
        ${data.years && html`<p>${yearsLine(data.years)}<${Figure}> median ${data.years.median} of ${data.years.stated}<//></p>`}
      </div>
      ${data.requirements.length > 0 && html`
        <h5 class="sub-h">What the adverts mention</h5>
        <ul class="emp-list">${data.requirements.map((r) => html`
          <li key=${r.key}><span class="share">${r.words}</span><span>${r.label}</span><${Figure}>${r.n}<//></li>`)}
        </ul>`}
      ${data.tools.length > 0 && html`
        <h5 class="sub-h">Tools and software they name</h5>
        <div class="chips soft">${data.tools.map((t) => html`
          <span key=${t.name} class="chip static">${t.name} <i>${t.words}</i></span>`)}</div>`}
      ${data.skills.length > 0 && html`
        <h5 class="sub-h">Skills these adverts talk about most</h5>
        <ul class="emp-list">${data.skills.map((k) => html`
          <li key=${k.element_id}><span class="share">${k.words}</span>
            <span>${onOpenSkill ? html`<button class="tl" onClick=${() => onOpenSkill(k)}>${k.name}</button>` : k.name}
              ${k.status && html` <span class=${"tag " + k.status}>${STATUS_WORDS[k.status]}</span>`}</span>
            <${Figure}>×${k.lift}<//></li>`)}
        </ul>
        <p class="note">Words these adverts use more than adverts in general. The skills lists above,
          from O*NET's ratings, are still the best guide to what the job needs.</p>`}
      ${data.titles.length > 0 && html`<p class="note">The adverts were called: ${data.titles.map((t) => t.title).join(" · ")}.</p>`}
      <p class="prov">${data.dataset} · listed ${data.listed_from} to ${data.listed_to}</p>
    </section>`;
}

/** Home: the goal's two plainest facts, and a way into the full section. */
function EmployersCard({ profileId, goal, onOpen }) {
  const { data } = useFetch(goal ? `/occupations/${goal.soc_code}/adverts?profile_id=${profileId}` : null);
  if (!goal || !data || !data.enough) return null;
  const top = data.requirements[0];
  return html`
    <section class="card">
      <h3 class="ch">What employers ask for</h3>
      <p class="note">In ${data.adverts} US adverts for ${goal.title.toLowerCase()} (2024):${" "}<b>${data.entry_words}</b> were open to beginners${top ? html`, and <b>${top.words}</b> mentioned ${top.label.charAt(0).toLowerCase() + top.label.slice(1)}` : ""}.</p>
      <button class="btn full" onClick=${onOpen}>See what employers ask for</button>
    </section>`;
}
