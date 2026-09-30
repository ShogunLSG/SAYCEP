/* SAYCEP — progress history (slice 5, ADR-0012).
 *
 * Each event carries the goal's readiness as it stood at that moment, so the
 * climb is drawn straight from the API with nothing recomputed here.
 */

const when = (iso) => {
  const d = new Date(iso);
  const today = new Date();
  const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return d.toDateString() === today.toDateString() ? `Today ${time}`
    : `${d.toLocaleDateString([], { day: "numeric", month: "short" })} ${time}`;
};

function eventText(e) {
  if (e.kind === "started") return html`Started your plan with <b>${e.skill_count}</b> skill${e.skill_count === 1 ? "" : "s"}`;
  if (e.kind === "goal") return html`Set your goal: <b>${e.job}</b>`;
  if (e.status === "held") return html`<b>${e.skill}</b> — you can do it now`;
  if (e.status === "learning") return html`Started learning <b>${e.skill}</b>`;
  return html`Took <b>${e.skill}</b> off your list`;
}

function ProgressHistory({ profileId, rev }) {
  const { data } = useFetch(`/profiles/${profileId}/history`, rev);
  const [all, setAll] = useState(false);
  if (!data || data.events.length === 0) return null;
  const ev = data.events;                                   // newest first
  // The climb toward the current goal: events since it was last set, oldest first.
  const lastGoal = ev.findIndex((e) => e.kind === "goal" || (e.kind === "started" && e.goal_total != null));
  const since = (lastGoal === -1 ? ev : ev.slice(0, lastGoal + 1)).slice().reverse()
    .filter((e) => e.goal_total != null);
  const total = since.length ? since[since.length - 1].goal_total : 0;
  const shown = all ? ev : ev.slice(0, 5);
  return html`
    <section class="card">
      <h3 class="ch">Your progress${PRESENTER ? " · ADR-0012" : ""}</h3>
      ${since.length > 1 && total > 0 && html`
        <div class="climb" aria-label="Must-haves held over time">
          ${since.map((e, i) => html`
            <span key=${i} class="cb" title=${`${e.goal_have} of ${e.goal_total}`}>
              <i style=${{ height: `${Math.max(6, (e.goal_have / e.goal_total) * 100)}%` }}
                 class=${e.goal_have === e.goal_total ? "full" : ""}></i></span>`)}
        </div>
        <p class="note">Must-haves for your goal after each change: ${since.map((e) => e.goal_have).join(" → ")} of ${total}.</p>`}
      <ol class="tl-list">
        ${shown.map((e, i) => html`
          <li key=${i} class=${"tle k-" + (e.status || e.kind)}>
            <span class="tle-dot"></span>
            <span class="tle-t">${eventText(e)}<span class="meta">${when(e.at)}</span></span>
          </li>`)}
      </ol>
      ${ev.length > 5 && html`<button class="more" onClick=${() => setAll(!all)}>
        ${all ? "Show less" : `Show all ${ev.length}`}</button>`}
    </section>`;
}
